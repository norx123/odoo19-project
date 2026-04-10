from odoo import models, fields

class EducationHistory(models.Model):
    _name = 'education.history'
    _description = 'Education History'

    name = fields.Char(string="Degree", required=True)
    institute = fields.Char(string="Institute")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    percentage = fields.Float(string="Percentage")
