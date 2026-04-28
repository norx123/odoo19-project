from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    education_ids = fields.One2many(
        'education.history',
        'employee_id',
        string="Past Work Profile"
    )
