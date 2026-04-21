# -*- coding: utf-8 -*-
from odoo import models, fields, api


class VehicleRegistration(models.Model):
    _name = 'travel.vehicle.registration'
    _description = 'Employee Vehicle Registration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name_computed'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        default=lambda self: self.env.user.employee_id,
        tracking=True
    )
    department_id = fields.Many2one(
        related='employee_id.department_id',
        string='Department', store=True, readonly=True
    )
    vehicle_type = fields.Selection([
        ('bike', 'Bike / Two Wheeler'),
        ('car', 'Car'),
        ('auto', 'Auto Rickshaw'),
        ('van', 'Van / MUV'),
        ('other', 'Other'),
    ], string='Vehicle Type', required=True, tracking=True)

    vehicle_name = fields.Char(string='Vehicle Name / Model', required=True)
    vehicle_number = fields.Char(string='Vehicle Number', required=True)
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('ev', 'Electric (EV)'),
        ('cng', 'CNG'),
        ('hybrid', 'Hybrid'),
    ], string='Fuel Type', required=True, tracking=True)

    mileage = fields.Float(string='Mileage (KM/L)', digits=(10, 2))
    color = fields.Char(string='Vehicle Color')
    year = fields.Integer(string='Year')

    # Driver
    has_driver = fields.Boolean(string='Has Driver?', default=False)
    driver_name = fields.Char(string='Driver Name')
    driver_license = fields.Char(string='Driver License No')
    driver_phone = fields.Char(string='Driver Phone')

    active = fields.Boolean(default=True)

    display_name_computed = fields.Char(
        string='Display Name', compute='_compute_display_name_field', store=True
    )

    @api.depends('vehicle_number', 'vehicle_name')
    def _compute_display_name_field(self):
        for rec in self:
            rec.display_name_computed = f"{rec.vehicle_number} - {rec.vehicle_name}" if rec.vehicle_number else rec.vehicle_name or ''

    @api.onchange('has_driver')
    def _onchange_has_driver(self):
        if not self.has_driver:
            self.driver_name = False
            self.driver_license = False
            self.driver_phone = False
