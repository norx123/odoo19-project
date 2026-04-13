from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    basic = fields.Float(related='contract_id.basic', store=True)
    hra = fields.Float(related='contract_id.hra', store=True)
    pf_employee = fields.Float(related='contract_id.pf_employee', store=True)
