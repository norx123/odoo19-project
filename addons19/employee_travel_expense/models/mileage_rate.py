# -*- coding: utf-8 -*-
from odoo import models, fields


class MileageRate(models.Model):
    _name = 'travel.mileage.rate'
    _description = 'Mileage Rate Master'
    _rec_name = 'name'

    name = fields.Char(string='Rate Name', required=True)
    vehicle_type = fields.Selection([
        ('bike', 'Bike / Two Wheeler'),
        ('car', 'Car'),
        ('auto', 'Auto Rickshaw'),
        ('van', 'Van / MUV'),
        ('other', 'Other'),
    ], string='Vehicle Type')
    fuel_type = fields.Selection([
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('ev', 'Electric (EV)'),
        ('cng', 'CNG'),
        ('any', 'Any'),
    ], string='Fuel Type', default='any')
    rate_per_km = fields.Float(string='Rate Per KM (Rs.)', required=True, digits=(10, 2))
    effective_from = fields.Date(string='Effective From', required=True)
    active = fields.Boolean(default=True)
