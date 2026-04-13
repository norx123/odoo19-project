from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    pf_number = fields.Char(string="PF Number")
    uan_number = fields.Char(string="UAN Number")
    esic_number = fields.Char(string="ESIC Number")
    pan_number = fields.Char(string="PAN Number")