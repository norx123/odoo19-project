# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalsLoanRequest(models.Model):
    """Employee Loan Request Model."""
    _name = 'approvals.loan.request'
    _description = 'Request for Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default=lambda self: _('New')
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id.id
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True
    )
    request_date = fields.Date(
        string='Request Date', required=True,
        default=fields.Date.today
    )
    loan_amount = fields.Float(string='Loan Amount', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    loan_type = fields.Selection([
        ('personal', 'Personal Loan'),
        ('medical', 'Medical Loan'),
        ('education', 'Education Loan'),
        ('housing', 'Housing Loan'),
        ('emergency', 'Emergency Loan'),
        ('other', 'Other'),
    ], string='Loan Type', required=True, default='personal')
    installment_count = fields.Integer(string='No. of Installments', default=6)
    installment_amount = fields.Float(
        string='Installment Amount',
        compute='_compute_installment_amount', store=True
    )
    repayment_start_date = fields.Date(string='Repayment Start Date')
    reason = fields.Text(string='Reason / Purpose')
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)
    approver_ids = fields.One2many(
        'approvals.approver.line', 'loan_request_id',
        string='Approver(s)'
    )

    @api.depends('loan_amount', 'installment_count')
    def _compute_installment_amount(self):
        for rec in self:
            if rec.installment_count and rec.installment_count > 0:
                rec.installment_amount = rec.loan_amount / rec.installment_count
            else:
                rec.installment_amount = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'approvals.loan.request') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        self.ensure_one()
        if not self.loan_amount or self.loan_amount <= 0:
            raise UserError(_('Please enter a valid loan amount.'))
        self.write({'state': 'submitted'})
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Loan request submitted for approval.'))

    def action_approve(self):
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'approved'})
        self.message_post(body=_('Loan request approved.'))

    def action_refuse(self):
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'refused'})
        self.message_post(body=_('Loan request refused.'))

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Loan request cancelled.'))

    def action_reset_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Loan request reset to draft.'))
