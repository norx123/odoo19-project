# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class EarlyGatePass(models.Model):
    """Early Logout Gate Pass Request Model."""
    _name = 'early.gate.pass'
    _description = 'Early Logout Gate Pass'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'request_date desc, id desc'

    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default=lambda self: _('New'),
        help='Sequence reference for early logout gate pass'
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id.id,
        help='Employee requesting early logout'
    )
    employee_code = fields.Char(
        string='Employee Code',
        compute='_compute_employee_code',
        store=True,
        help='Identification code of the employee'
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
    manager_id = fields.Many2one(
        'hr.employee', string='Manager',
        compute='_compute_manager_id',
        store=True, readonly=False,
        help='Manager of the employee (auto-filled from employee record)'
    )

    request_date = fields.Date(
        string='Date', required=True,
        default=fields.Date.today,
        help='Date for which early logout is requested'
    )
    login_time = fields.Float(
        string='Login Time', required=True,
        help='Check-in time (24h format, e.g. 9.5 = 09:30 AM)'
    )
    logout_time = fields.Float(
        string='Logout Time', required=True,
        help='Requested early logout time (24h format)'
    )
    duration_hours = fields.Float(
        string='Working Hours',
        compute='_compute_duration_hours',
        store=True,
        help='Total working hours on that day'
    )
    reason = fields.Text(
        string='Reason', required=True,
        help='Reason for requesting early logout'
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
        help='State of the gate pass request'
    )
    approver_ids = fields.One2many(
        'early.gate.pass.approver', 'gate_pass_id',
        string='Approver(s)',
        help='List of approvers for this gate pass request'
    )

    # -----------------------------------------------------------------
    # Compute methods
    # -----------------------------------------------------------------
    @api.depends('employee_id')
    def _compute_employee_code(self):
        """Pick up employee code from hr.employee (multiple fallbacks)."""
        for rec in self:
            emp = rec.employee_id
            code = False
            if emp:
                for fname in ('employee_code', 'barcode', 'identification_id', 'pin'):
                    if hasattr(emp, fname):
                        val = getattr(emp, fname)
                        if val:
                            code = val
                            break
            rec.employee_code = code or ''

    @api.depends('employee_id')
    def _compute_manager_id(self):
        """Auto-fill manager when employee is selected."""
        for rec in self:
            rec.manager_id = rec.employee_id.parent_id.id if rec.employee_id else False

    @api.depends('login_time', 'logout_time')
    def _compute_duration_hours(self):
        for rec in self:
            if rec.logout_time and rec.login_time:
                rec.duration_hours = max(rec.logout_time - rec.login_time, 0.0)
            else:
                rec.duration_hours = 0.0

    # -----------------------------------------------------------------
    # Constraints
    # -----------------------------------------------------------------
    @api.constrains('login_time', 'logout_time')
    def _check_times(self):
        for rec in self:
            if rec.login_time < 0 or rec.login_time >= 24:
                raise ValidationError(_('Login Time must be between 00:00 and 23:59.'))
            if rec.logout_time < 0 or rec.logout_time >= 24:
                raise ValidationError(_('Logout Time must be between 00:00 and 23:59.'))
            if rec.logout_time <= rec.login_time:
                raise ValidationError(_('Logout Time must be later than Login Time.'))

    # -----------------------------------------------------------------
    # Overrides
    # -----------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to assign sequence."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'early.gate.pass') or _('New')
        return super().create(vals_list)

    # -----------------------------------------------------------------
    # Workflow Actions
    # -----------------------------------------------------------------
    def action_submit(self):
        """Submit the gate pass request."""
        self.ensure_one()
        if not self.reason or not self.reason.strip():
            raise UserError(_('Please provide a reason for the early logout.'))
        if not self.approver_ids:
            raise UserError(_('Please add at least one approver before submitting.'))
        self.write({'state': 'submitted'})
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Early Logout Gate Pass submitted for approval.'))

    def action_approve(self):
        """Approve the gate pass request."""
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'approved'})
        self.message_post(body=_('Early Logout Gate Pass approved.'))

    def action_refuse(self):
        """Refuse the gate pass request."""
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(
            lambda a: a.status == 'pending'
        ).write({'status': 'refused'})
        self.message_post(body=_('Early Logout Gate Pass refused.'))

    def action_cancel(self):
        """Cancel the gate pass request."""
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Early Logout Gate Pass cancelled.'))

    def action_reset_draft(self):
        """Reset to draft state."""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Early Logout Gate Pass reset to draft.'))

    # -----------------------------------------------------------------
    # Print Gate Pass (PDF) - available only after approval
    # -----------------------------------------------------------------
    def action_print_gate_pass(self):
        """Print the approved gate pass."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Gate Pass can only be downloaded after approval.'))
        return self.env.ref(
            'early_gate_pass.action_report_early_gate_pass'
        ).report_action(self)

    # -----------------------------------------------------------------
    # Helpers for the report
    # -----------------------------------------------------------------
    def _format_float_time(self, value):
        """Convert float hours (e.g. 9.5) to 'HH:MM' string."""
        if not value:
            return '--:--'
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        if minutes == 60:
            hours += 1
            minutes = 0
        return '%02d:%02d' % (hours, minutes)

    def get_login_time_str(self):
        self.ensure_one()
        return self._format_float_time(self.login_time)

    def get_logout_time_str(self):
        self.ensure_one()
        return self._format_float_time(self.logout_time)
