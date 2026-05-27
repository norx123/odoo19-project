# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ApprovalsTravelRequest(models.Model):
    """Employee Travel Request Model."""
    _name = 'approvals.travel.request'
    _description = 'Travel Request'
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

    # Travel Details
    travel_from = fields.Char(string='From (City/Country)', required=True)
    travel_to = fields.Char(string='To (City/Country)', required=True)
    departure_date = fields.Date(string='Departure Date', required=True)
    return_date = fields.Date(string='Return Date', required=True)
    duration_days = fields.Integer(
        string='Duration (Days)',
        compute='_compute_duration', store=True
    )
    purpose_of_travel = fields.Text(string='Purpose of Travel', required=True)
    travel_mode = fields.Selection([
        ('flight', 'Flight'),
        ('train', 'Train'),
        ('bus', 'Bus'),
        ('car', 'Car/Road'),
        ('other', 'Other'),
    ], string='Mode of Travel', default='flight')

    # Hotel
    hotel_required = fields.Boolean(string='Hotel Required', default=True)
    hotel_name = fields.Char(string='Hotel Name')
    check_in_date = fields.Date(string='Check-In Date')
    check_out_date = fields.Date(string='Check-Out Date')

    # Budget
    estimated_budget = fields.Float(string='Estimated Budget')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id
    )

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
        'approvals.approver.line', 'travel_request_id',
        string='Approver(s)'
    )

    @api.depends('departure_date', 'return_date')
    def _compute_duration(self):
        for rec in self:
            if rec.departure_date and rec.return_date:
                delta = rec.return_date - rec.departure_date
                rec.duration_days = delta.days + 1
            else:
                rec.duration_days = 0

    @api.constrains('departure_date', 'return_date')
    def _check_dates(self):
        for rec in self:
            if rec.departure_date and rec.return_date:
                if rec.return_date < rec.departure_date:
                    raise ValidationError(
                        _('Return Date cannot be before Departure Date.')
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'approvals.travel.request') or _('New')
        return super().create(vals_list)

    def action_submit(self):
        self.ensure_one()
        if not self.departure_date or not self.return_date:
            raise UserError(_('Please set Departure and Return dates.'))
        self.write({'state': 'submitted'})
        self.approver_ids.write({'status': 'pending'})
        self.message_post(body=_('Travel request submitted for approval.'))

    def action_approve(self):
        self.ensure_one()
        self.write({'state': 'approved'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'approved'})
        self.message_post(body=_('Travel request approved.'))

    def action_refuse(self):
        self.ensure_one()
        self.write({'state': 'refused'})
        self.approver_ids.filtered(lambda a: a.status == 'pending').write({'status': 'refused'})
        self.message_post(body=_('Travel request refused.'))

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        self.message_post(body=_('Travel request cancelled.'))

    def action_reset_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.approver_ids.write({'status': 'new'})
        self.message_post(body=_('Travel request reset to draft.'))
