
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    employer_name = fields.Char()
    office_address = fields.Char()

    date_joining = fields.Date()
    exit_date = fields.Date()

    gross_salary = fields.Float()
    hra_exemption = fields.Float()
    gratuity = fields.Float()
    leave_encashment = fields.Float()
    perquisites = fields.Float()

    pf_80c = fields.Float()
    medical_self_80d = fields.Float()
    medical_parents_80d = fields.Float()
    medical_senior_80d = fields.Float()

    income_tax = fields.Float()
    professional_tax = fields.Float()

    added_by = fields.Char()
    added_date = fields.Date()
    updated_by = fields.Char()
    updated_date = fields.Date()
