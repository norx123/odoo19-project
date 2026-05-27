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
    login_time = fields.Float(string='Login Time', required=True)
    logout_time = fields.Float(string='Logout Time', required=True)
    duration_hours = fields.Float(
        string='Working Hours',
        compute='_compute_duration_hours', store=True
    )
    reason = fields.Text(string='Reason', required=True)
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
