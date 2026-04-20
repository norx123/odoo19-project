# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CustomAdvanceSalary(models.Model):
    """Advance Salary Request Model."""
    _name = 'custom.advance.salary'
    _description = 'Advance Salary Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default=lambda self: _('New'),
        help='Sequence reference for advance salary request'
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id.id,
        help='Employee requesting advance salary'
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True,
        help='Department of the employee'
    )
    request_date = fields.Date(
        string='Request Date', required=True,
        default=fields.Date.today,
        help='Date of advance salary request'
    )
    advance_amount = fields.Float(
        string='Advance Amount', required=True,
        help='Amount requested as salary advance'
    )
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id,
        help='Currency for the advance amount'
    )
    reason = fields.Text(
        string='Reason',
        help='Reason for requesting advance salary'
    )
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    ], string='Payment Method', default='bank',
        help='Preferred payment method'
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
        help='State of the advance salary request'
    )
    approver_ids = fields.One2many(
        'approval.approver.line', 'advance_salary_id',
        string='Approver(s)',
        help='List of approvers for this request'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign sequence."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'custom.advance.salary') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        """Submit the advance salary request."""
        self.ensure_one()
        if not self.advance_amount or self.advance_amount <= 0:
            raise UserError(_('Please enter a valid advance amount.'))
        self.write({'state': 'submitted'})
        # Set approvers to pending
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Advance Salary request submitted for approval.'))

    def action_approve(self):
        """Approve the advance salary request."""
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'approved'})
        self.message_post(body=_('Advance Salary request approved.'))

    def action_refuse(self):
        """Refuse the advance salary request."""
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'refused'})
        self.message_post(body=_('Advance Salary request refused.'))

    def action_cancel(self):
        """Cancel the advance salary request."""
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Advance Salary request cancelled.'))

    def action_reset_draft(self):
        """Reset to draft state."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Advance Salary request reset to draft.'))
