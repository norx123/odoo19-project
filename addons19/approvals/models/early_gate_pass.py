# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ApprovalsEarlyGatePass(models.Model):
    """Early Logout Gate Pass Request Model."""
    _name = 'approvals.early.gate.pass'
    _description = 'Early Logout Gate Pass'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'request_date desc, id desc'

    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default=lambda self: _('New')
    )
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id.id
    )
    employee_code = fields.Char(
        string='Employee Code',
        compute='_compute_employee_code', store=True
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True
    )
    job_id = fields.Many2one(
        'hr.job', string='Job Position',
        related='employee_id.job_id', store=True
    )
    manager_id = fields.Many2one(
        'hr.employee', string='Manager',
        compute='_compute_manager_id',
        store=True, readonly=False
    )
    request_date = fields.Date(
        string='Date', required=True,
        default=fields.Date.today
    )
    location = fields.Char(
        string='Location', required=True,
        help='Place the employee is going to'
    )

    # ---- Out Time (Hour / Minute / AM-PM) ----
    out_hour = fields.Selection(
        selection=[(str(h), '%02d' % h) for h in range(1, 13)],
        string='Out Hour', default='9', required=True)
    out_minute = fields.Selection(
        selection=[('%02d' % m, '%02d' % m) for m in range(0, 60, 5)],
        string='Out Minute', default='00', required=True)
    out_ampm = fields.Selection(
        [('AM', 'AM'), ('PM', 'PM')],
        string='Out AM/PM', default='AM', required=True)

    # ---- In Time (Hour / Minute / AM-PM) ----
    in_hour = fields.Selection(
        selection=[(str(h), '%02d' % h) for h in range(1, 13)],
        string='In Hour', default='6', required=True)
    in_minute = fields.Selection(
        selection=[('%02d' % m, '%02d' % m) for m in range(0, 60, 5)],
        string='In Minute', default='00', required=True)
    in_ampm = fields.Selection(
        [('AM', 'AM'), ('PM', 'PM')],
        string='In AM/PM', default='PM', required=True)

    # ---- Logout Timing (Hour / Minute / AM-PM) - optional ----
    logout_hour = fields.Selection(
        selection=[('', '--')] + [(str(h), '%02d' % h) for h in range(1, 13)],
        string='Logout Hour', default='')
    logout_minute = fields.Selection(
        selection=[('', '--')] + [('%02d' % m, '%02d' % m) for m in range(0, 60, 5)],
        string='Logout Minute', default='')
    logout_ampm = fields.Selection(
        [('', '--'), ('AM', 'AM'), ('PM', 'PM')],
        string='Logout AM/PM', default='')

    # ---- Computed float values (for duration + PDF) ----
    login_time = fields.Float(
        string='Out Time', compute='_compute_time_floats', store=True,
        help='Time the employee leaves the office')
    logout_time = fields.Float(
        string='In Time', compute='_compute_time_floats', store=True,
        help='Time the employee returns to the office')
    final_logout_time = fields.Float(
        string='Logout Timing', compute='_compute_time_floats', store=True,
        help='Final logout / office leaving time for the day')
    duration_hours = fields.Float(
        string='Office Out Duration',
        compute='_compute_duration_hours', store=True,
        help='Duration the employee stays out of office (In Time - Out Time)'
    )
    reason = fields.Text(string='Purpose of Going Outside', required=True)

    gate_pass_type = fields.Selection([
        ('official', 'Official'),
        ('personal', 'Personal'),
    ], string='Gate Pass Type', default='official', required=True,
        help='Official = company work, Personal = private work')
    pay_status = fields.Selection([
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ], string='Paid / Unpaid',
        compute='_compute_pay_status', store=True, readonly=False,
        help='Whether the time outside is paid or deducted')
    contact_number = fields.Char(
        string='Contact Number',
        compute='_compute_contact_number', store=True, readonly=False,
        help='Mobile number to reach the employee while outside'
    )
    vehicle_number = fields.Char(
        string='Vehicle Number',
        help='Vehicle registration number (if any)'
    )
    travel_mode = fields.Selection([
        ('walk', 'Walk-in'),
        ('bike', 'Bike'),
        ('car', 'Car'),
        ('cab', 'Cab'),
    ], string='Mode of Travel', default='walk',
        help='How the employee is travelling')

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
        'approvals.approver.line', 'early_gate_pass_id',
        string='Approver(s)'
    )

    # -----------------------------------------------------------------
    # Compute methods
    # -----------------------------------------------------------------
    @api.depends('employee_id')
    def _compute_employee_code(self):
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
        for rec in self:
            rec.manager_id = rec.employee_id.parent_id.id if rec.employee_id else False

    @api.depends('gate_pass_type')
    def _compute_pay_status(self):
        """Official -> Paid, Personal -> Unpaid (manager can override)."""
        for rec in self:
            rec.pay_status = 'paid' if rec.gate_pass_type == 'official' else 'unpaid'

    @api.depends('employee_id')
    def _compute_contact_number(self):
        """Auto-fill mobile from employee record (multiple fallbacks)."""
        for rec in self:
            emp = rec.employee_id
            number = False
            if emp:
                for fname in ('mobile_phone', 'work_phone', 'private_phone'):
                    if hasattr(emp, fname):
                        val = getattr(emp, fname)
                        if val:
                            number = val
                            break
            rec.contact_number = number or ''

    @staticmethod
    def _hms_to_float(hour, minute, ampm):
        """Convert 12-hour (hour, minute, AM/PM) selection into float hours."""
        if not hour or not ampm:
            return 0.0
        h = int(hour)
        m = int(minute) if minute else 0
        if ampm == 'AM':
            if h == 12:
                h = 0
        else:  # PM
            if h != 12:
                h += 12
        return h + (m / 60.0)

    @api.depends('out_hour', 'out_minute', 'out_ampm',
                 'in_hour', 'in_minute', 'in_ampm',
                 'logout_hour', 'logout_minute', 'logout_ampm')
    def _compute_time_floats(self):
        for rec in self:
            rec.login_time = rec._hms_to_float(rec.out_hour, rec.out_minute, rec.out_ampm)
            rec.logout_time = rec._hms_to_float(rec.in_hour, rec.in_minute, rec.in_ampm)
            rec.final_logout_time = rec._hms_to_float(
                rec.logout_hour, rec.logout_minute, rec.logout_ampm)

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
            if rec.login_time and rec.logout_time and rec.logout_time <= rec.login_time:
                raise ValidationError(_('In Time must be later than Out Time.'))

    # -----------------------------------------------------------------
    # Overrides
    # -----------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'approvals.early.gate.pass') or _('New')
        return super().create(vals_list)

    # -----------------------------------------------------------------
    # Workflow Actions
    # -----------------------------------------------------------------
    def action_submit(self):
        self.ensure_one()
        if not self.reason or not self.reason.strip():
            raise UserError(_('Please provide a reason for the early logout.'))
        if not self.approver_ids:
            raise UserError(_('Please add at least one approver before submitting.'))
        self.write({'state': 'submitted'})
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Early Logout Gate Pass submitted for approval.'))

    def action_approve(self):
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'approved'})
        self.message_post(body=_('Early Logout Gate Pass approved.'))

    def action_refuse(self):
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'refused'})
        self.message_post(body=_('Early Logout Gate Pass refused.'))

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Early Logout Gate Pass cancelled.'))

    def action_reset_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Early Logout Gate Pass reset to draft.'))

    def action_print_gate_pass(self):
        """Download approved gate pass as PDF (A6, 1/4 of A4)."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Gate Pass can only be downloaded after approval.'))
        return self.env.ref(
            'approvals.action_report_early_gate_pass'
        ).report_action(self)

    # -----------------------------------------------------------------
    # Helpers for the report
    # -----------------------------------------------------------------
    def _format_float_time(self, value):
        """Format float hours to 12-hour 'HH:MM AM/PM' string."""
        if not value:
            return '--:--'
        hours = int(value)
        minutes = int(round((value - hours) * 60))
        if minutes == 60:
            hours += 1
            minutes = 0
        suffix = 'AM' if hours < 12 else 'PM'
        display_hour = hours % 12
        if display_hour == 0:
            display_hour = 12
        return '%02d:%02d %s' % (display_hour, minutes, suffix)

    def get_login_time_str(self):
        self.ensure_one()
        return self._format_float_time(self.login_time)

    def get_logout_time_str(self):
        self.ensure_one()
        return self._format_float_time(self.logout_time)

    def get_final_logout_time_str(self):
        self.ensure_one()
        return self._format_float_time(self.final_logout_time)
