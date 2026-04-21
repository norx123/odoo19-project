# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class OutstationTravelExpense(models.Model):
    _name = 'travel.outstation.expense'
    _description = 'Employee Outstation Travel Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(
        string='Reference', readonly=True, copy=False,
        default='New', tracking=True
    )

    # Employee Details
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True
    )
    department_id = fields.Many2one(
        'hr.department', string='Department',
        related='employee_id.department_id', store=True, readonly=True
    )
    employee_phone = fields.Char(
        string='Contact No', related='employee_id.mobile_phone',
        store=True, readonly=True
    )
    employee_email = fields.Char(
        string='Email', related='employee_id.work_email',
        store=True, readonly=True
    )

    # Trip Info
    date_from = fields.Date(string='Trip Start Date', required=True)
    date_to = fields.Date(string='Trip End Date', required=True)
    destination = fields.Char(string='Destination / Place')
    purpose = fields.Text(string='Purpose of Visit')

    # Approvers
    approver_ids = fields.Many2many(
        'hr.employee', 'outstation_expense_approver_rel',
        'expense_id', 'employee_id',
        string='Approvers'
    )
    current_approver_id = fields.Many2one(
        'hr.employee', string='Current Approver', tracking=True
    )

    # State
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('waiting', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('refused', 'Refused'),
    ], string='Status', default='draft', tracking=True, copy=False)

    # Expense Lines
    journey_ids = fields.One2many(
        'travel.outstation.journey', 'expense_id', string='Journey Details'
    )
    meal_ids = fields.One2many(
        'travel.outstation.meal', 'expense_id', string='Meal Details'
    )
    gift_ids = fields.One2many(
        'travel.outstation.gift', 'expense_id', string='Gift / Entertainment'
    )

    # Totals
    journey_total = fields.Float(
        string='Journey Total (₹)', compute='_compute_totals', store=True, digits=(10, 2)
    )
    meal_total = fields.Float(
        string='Meal Total (₹)', compute='_compute_totals', store=True, digits=(10, 2)
    )
    gift_total = fields.Float(
        string='Gift Total (₹)', compute='_compute_totals', store=True, digits=(10, 2)
    )
    grand_total = fields.Float(
        string='Grand Total (₹)', compute='_compute_totals', store=True, digits=(10, 2)
    )

    notes = fields.Text(string='Remarks')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'travel.outstation.expense') or 'New'
        return super().create(vals_list)

    @api.depends(
        'journey_ids.amount', 'meal_ids.amount', 'gift_ids.amount'
    )
    def _compute_totals(self):
        for rec in self:
            rec.journey_total = sum(rec.journey_ids.mapped('amount'))
            rec.meal_total = sum(rec.meal_ids.mapped('amount'))
            rec.gift_total = sum(rec.gift_ids.mapped('amount'))
            rec.grand_total = rec.journey_total + rec.meal_total + rec.gift_total

    def action_submit(self):
        for rec in self:
            if not (rec.journey_ids or rec.meal_ids or rec.gift_ids):
                raise exceptions.UserError('Please add at least one expense entry before submitting.')
            rec.state = 'submitted'
            rec.message_post(body=f"Expense <b>{rec.name}</b> submitted for review.")

    def action_send_for_approval(self):
        for rec in self:
            rec.state = 'waiting'
            if rec.approver_ids:
                rec.current_approver_id = rec.approver_ids[0]
            rec.message_post(body=f"Sent for approval.")

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'
            rec.current_approver_id = False
            rec.message_post(body=f"Expense <b>{rec.name}</b> <b>APPROVED</b>.")

    def action_mark_paid(self):
        for rec in self:
            rec.state = 'paid'

    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'


class OutstationJourney(models.Model):
    _name = 'travel.outstation.journey'
    _description = 'Outstation Journey Line'

    expense_id = fields.Many2one(
        'travel.outstation.expense', string='Expense', ondelete='cascade'
    )
    date = fields.Date(string='Date', required=True)
    from_location = fields.Char(string='From', required=True)
    to_location = fields.Char(string='To', required=True)
    description = fields.Char(string='Description')
    vehicle_type = fields.Selection([
        ('self_vehicle', 'Self Vehicle'),
        ('auto', 'Auto'),
        ('cab', 'Cab / Taxi'),
        ('train', 'Train'),
        ('flight', 'Flight'),
        ('bus', 'Bus'),
        ('other', 'Other'),
    ], string='Vehicle / Travel Type', required=True)
    amount = fields.Float(string='Amount (₹)', required=True, digits=(10, 2))
    bill = fields.Binary(string='Upload Bill')
    bill_name = fields.Char(string='Bill Filename')


class OutstationMeal(models.Model):
    _name = 'travel.outstation.meal'
    _description = 'Outstation Meal Line'

    expense_id = fields.Many2one(
        'travel.outstation.expense', string='Expense', ondelete='cascade'
    )
    date = fields.Date(string='Date', required=True)
    meal_type = fields.Selection([
        ('breakfast', 'Breakfast'),
        ('brunch', 'Brunch'),
        ('lunch', 'Lunch'),
        ('snacks', 'Snacks / Tea'),
        ('dinner', 'Dinner'),
        ('other', 'Other'),
    ], string='Meal Type', required=True)
    place = fields.Char(string='Place / Restaurant')
    description = fields.Char(string='Description')
    amount = fields.Float(string='Amount (₹)', required=True, digits=(10, 2))
    bill = fields.Binary(string='Upload Bill')
    bill_name = fields.Char(string='Bill Filename')


class OutstationGift(models.Model):
    _name = 'travel.outstation.gift'
    _description = 'Outstation Gift / Entertainment Line'

    expense_id = fields.Many2one(
        'travel.outstation.expense', string='Expense', ondelete='cascade'
    )
    date = fields.Date(string='Date', required=True)
    gift_item = fields.Char(string='Gift / Item Description', required=True)
    recipient = fields.Char(string='Recipient / Purpose')
    description = fields.Char(string='Additional Notes')
    amount = fields.Float(string='Amount (₹)', required=True, digits=(10, 2))
    bill = fields.Binary(string='Upload Bill')
    bill_name = fields.Char(string='Bill Filename')
