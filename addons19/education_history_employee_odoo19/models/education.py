from odoo import models, fields

class EducationHistory(models.Model):
    _name = 'education.history'
    _description = 'Employee Work History'

    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete='cascade')

    name = fields.Char(string="Company Name", required=True)
    institute = fields.Char(string="Designation ")
    organization = fields.Char(string="Organization ")
    start_date = fields.Date(string="Date of Joining")
    end_date = fields.Date(string="Date of Reliving")
    percentage = fields.Float(string="CTC")