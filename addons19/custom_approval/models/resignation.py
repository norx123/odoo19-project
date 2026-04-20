# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


RESIGNATION_TYPE = [
    ('resigned', 'Normal Resignation'),
    ('fired', 'Fired by the Company'),
]


class CustomResignation(models.Model):
    """Employee Resignation Request Model."""
    _name = 'custom.resignation'
    _description = 'Employee Resignation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default=lambda self: _('New'),
        help='Sequence reference for resignation'
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id.id,
        help='Employee submitting resignation'
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True,
        help='Department of the employee'
    )
    job_id = fields.Many2one(
        'hr.job', string='Job Position',
        related='employee_id.job_id', store=True,
        help='Job position of the employee'
    )

    @api.depends('employee_id')
    def _compute_joining_date(self):
        """Safely compute joining date from employee."""
        for rec in self:
            emp = rec.employee_id
            if emp and hasattr(emp, 'joining_date'):
                rec.joining_date = emp.joining_date
            else:
                rec.joining_date = False
    joining_date = fields.Date(
        string='Joining Date',
        compute='_compute_joining_date',
        store=True,
        help='Date employee joined the company'
    )
    resignation_date = fields.Date(
        string='Resignation Date', required=True,
        default=fields.Date.today,
        help='Date the employee submits resignation'
    )
    last_working_date = fields.Date(
        string='Last Working Day', required=True,
        help='Expected last working day of the employee'
    )
    notice_period = fields.Integer(
        string='Notice Period (Days)',
        compute='_compute_notice_period',
        help='Notice period in days'
    )
    resignation_type = fields.Selection(
        selection=RESIGNATION_TYPE,
        string='Resignation Type',
        default='resigned',
        help='Type of resignation'
    )
    reason = fields.Text(
        string='Reason for Leaving', required=True,
        help='Reason provided by employee for resignation'
    )
    confirm_date = fields.Date(
        string='Confirmed Date', readonly=True,
        help='Date resignation was confirmed by manager'
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company,
        help='Company of the employee'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft',
        tracking=True, copy=False,
        help='State of the resignation request'
    )
    approver_ids = fields.One2many(
        'approval.approver.line', 'resignation_id',
        string='Approver(s)',
        help='List of approvers for this resignation request'
    )

    @api.depends('resignation_date', 'last_working_date')
    def _compute_notice_period(self):
        """Compute notice period in days."""
        for rec in self:
            if rec.resignation_date and rec.last_working_date:
                delta = rec.last_working_date - rec.resignation_date
                rec.notice_period = delta.days
            else:
                rec.notice_period = 0

    @api.constrains('resignation_date', 'last_working_date')
    def _check_dates(self):
        """Validate that last working day is after resignation date."""
        for rec in self:
            if rec.last_working_date and rec.resignation_date:
                if rec.last_working_date <= rec.resignation_date:
                    raise ValidationError(
                        _('Last Working Day must be after Resignation Date.')
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign sequence."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'custom.resignation') or _('New')
        return super().create(vals_list)

    def action_confirm(self):
        """Confirm the resignation request."""
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
        """Approve the resignation."""
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'approved'})
        self.message_post(body=_('Resignation approved.'))

    def action_refuse(self):
        """Refuse the resignation."""
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'refused'})
        self.message_post(body=_('Resignation refused.'))

    def action_cancel(self):
        """Cancel the resignation."""
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Resignation request cancelled.'))

    def action_reset_draft(self):
        """Reset to draft."""
        self.ensure_one()
        self.write({'state': 'draft', 'confirm_date': False})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Resignation reset to draft.'))
