# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


RESIGNATION_TYPE = [
    ('resigned', 'Normal Resignation'),
    ('fired', 'Fired by the Company'),
]


class ApprovalsResignation(models.Model):
    """Employee Resignation Request Model."""
    _name = 'approvals.resignation'
    _description = 'Employee Resignation'
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
    job_id = fields.Many2one(
        'hr.job', string='Job Position',
        related='employee_id.job_id', store=True
    )
    joining_date = fields.Date(
        string='Joining Date',
        compute='_compute_joining_date', store=True
    )
    resignation_date = fields.Date(
        string='Resignation Date', required=True,
        default=fields.Date.today
    )
    last_working_date = fields.Date(string='Last Working Day', required=True)
    notice_period = fields.Integer(
        string='Notice Period (Days)',
        compute='_compute_notice_period'
    )
    resignation_type = fields.Selection(
        selection=RESIGNATION_TYPE,
        string='Resignation Type', default='resigned'
    )
    reason = fields.Text(string='Reason for Leaving', required=True)
    confirm_date = fields.Date(string='Confirmed Date', readonly=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)
    approver_ids = fields.One2many(
        'approvals.approver.line', 'resignation_id',
        string='Approver(s)'
    )

    @api.depends('employee_id')
    def _compute_joining_date(self):
        for rec in self:
            emp = rec.employee_id
            if emp and hasattr(emp, 'joining_date'):
                rec.joining_date = emp.joining_date
            else:
                rec.joining_date = False

    @api.depends('resignation_date', 'last_working_date')
    def _compute_notice_period(self):
        for rec in self:
            if rec.resignation_date and rec.last_working_date:
                delta = rec.last_working_date - rec.resignation_date
                rec.notice_period = delta.days
            else:
                rec.notice_period = 0

    @api.constrains('resignation_date', 'last_working_date')
    def _check_dates(self):
        for rec in self:
            if rec.last_working_date and rec.resignation_date:
                if rec.last_working_date <= rec.resignation_date:
                    raise ValidationError(
                        _('Last Working Day must be after Resignation Date.')
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'approvals.resignation') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        self.ensure_one()
        if not self.last_working_date:
            raise UserError(_('Please set the Last Working Day.'))
        self.write({
            'state': 'confirmed',
            'confirm_date': fields.Date.today(),
        })
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Resignation request confirmed.'))

    def action_approve(self):
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'approved'})
        self.message_post(body=_('Resignation approved.'))

    def action_refuse(self):
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'refused'})
        self.message_post(body=_('Resignation refused.'))

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Resignation request cancelled.'))

    def action_reset_draft(self):
        self.ensure_one()
        self.write({'state': 'draft', 'confirm_date': False})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Resignation reset to draft.'))
