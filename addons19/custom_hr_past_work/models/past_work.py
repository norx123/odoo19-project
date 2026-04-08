from odoo import models, fields

class HrPastWork(models.Model):
    _name = 'hr.past.work'
    _description = 'Past Work Profile'

    employee_id = fields.Many2one('hr.employee', string="Employee")

    company_name = fields.Char(string="Company Name")
    designation = fields.Char(string="Designation")
    organization = fields.Char(string="Organization")
    date_joining = fields.Date(string="Date of Joining")
    date_relieving = fields.Date(string="Date of Relieving")


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    past_work_ids = fields.One2many(
        'hr.past.work',
        'employee_id',
        string="Past Work Profile"
    )
