# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalsAdvanceSalary(models.Model):
    """Advance Salary Request Model."""
    _name = 'approvals.advance.salary'
    _description = 'Advance Salary Request'
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
    advance_amount = fields.Float(string='Advance Amount', required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    reason = fields.Text(string='Reason')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('cheque', 'Cheque'),
    ], string='Payment Method', default='bank')
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
        'approvals.approver.line', 'advance_salary_id',
        string='Approver(s)'
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'approvals.advance.salary') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        self.ensure_one()
        if not self.advance_amount or self.advance_amount <= 0:
            raise UserError(_('Please enter a valid advance amount.'))
        self.write({'state': 'submitted'})
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Advance Salary request submitted for approval.'))

    def action_approve(self):
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'approved'})
        self.message_post(body=_('Advance Salary request approved.'))

    def action_refuse(self):
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'refused'})
        self.message_post(body=_('Advance Salary request refused.'))

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Advance Salary request cancelled.'))

    def action_reset_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Advance Salary request reset to draft.'))
