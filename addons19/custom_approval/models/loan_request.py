# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CustomLoanRequest(models.Model):
    """Employee Loan Request Model."""
    _name = 'custom.loan.request'
    _description = 'Request for Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default=lambda self: _('New'),
        help='Sequence reference for loan request'
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id.id,
        help='Employee requesting the loan'
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True,
        help='Department of the employee'
    )
    request_date = fields.Date(
        string='Request Date', required=True,
        default=fields.Date.today,
        help='Date of loan request'
    )
    loan_amount = fields.Float(
        string='Loan Amount', required=True,
        help='Total loan amount requested'
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for the loan'
    )
    loan_type = fields.Selection([
        ('personal', 'Personal Loan'),
        ('medical', 'Medical Loan'),
        ('education', 'Education Loan'),
        ('housing', 'Housing Loan'),
        ('emergency', 'Emergency Loan'),
        ('other', 'Other'),
    ], string='Loan Type', required=True, default='personal',
        help='Type of loan'
    )
    installment_count = fields.Integer(
        string='No. of Installments', default=6,
        help='Number of monthly installments to repay the loan'
    )
    installment_amount = fields.Float(
        string='Installment Amount',
        compute='_compute_installment_amount',
        store=True,
        help='Monthly installment amount'
    )
    repayment_start_date = fields.Date(
        string='Repayment Start Date',
        help='Date from which repayment starts'
    )
    reason = fields.Text(
        string='Reason / Purpose',
        help='Purpose of the loan request'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        help='Company of the employee'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft',
        tracking=True, copy=False,
        help='State of the loan request'
    )
    approver_ids = fields.One2many(
        'approval.approver.line', 'loan_request_id',
        string='Approver(s)',
        help='List of approvers for this loan request'
    )

    @api.depends('loan_amount', 'installment_count')
    def _compute_installment_amount(self):
        """Compute monthly installment amount."""
        for rec in self:
            if rec.installment_count and rec.installment_count > 0:
                rec.installment_amount = rec.loan_amount / rec.installment_count
            else:
                rec.installment_amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign sequence."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'custom.loan.request') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        """Submit the loan request."""
        self.ensure_one()
        if not self.loan_amount or self.loan_amount <= 0:
            raise UserError(_('Please enter a valid loan amount.'))
        self.write({'state': 'submitted'})
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Loan request submitted for approval.'))

    def action_approve(self):
        """Approve the loan request."""
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'approved'})
        self.message_post(body=_('Loan request approved.'))

    def action_refuse(self):
        """Refuse the loan request."""
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'refused'})
        self.message_post(body=_('Loan request refused.'))

    def action_cancel(self):
        """Cancel the loan request."""
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Loan request cancelled.'))

    def action_reset_draft(self):
        """Reset to draft state."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Loan request reset to draft.'))
