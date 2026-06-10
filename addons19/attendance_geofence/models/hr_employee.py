# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    assigned_work_location_ids = fields.Many2many(
        comodel_name='hr.work.location',
        relation='hr_employee_assigned_location_rel',
        column1='employee_id',
        column2='location_id',
        string='Assigned Locations',
        help='Locations from which this employee is permitted to check in.',
    )
