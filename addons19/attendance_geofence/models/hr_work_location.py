# -*- coding: utf-8 -*-

from odoo import models, fields


class HrWorkLocation(models.Model):
    _inherit = 'hr.work.location'

    geofence_enabled = fields.Boolean(
        string='Enable Geofence',
        default=False,
        help='If enabled, employees can only punch in from within the defined radius.',
    )

    geofence_latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
    )

    geofence_longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
    )

    geofence_radius = fields.Integer(
        string='Allowed Radius (meters)',
        default=100,
    )

    geofence_location_name = fields.Char(
        string='Location Name',
        help='Saved location name shown in the search box when the form is reopened.',
    )
