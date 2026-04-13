from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    contract_id = fields.Many2one('hr.contract', string="Contract")

    # Earnings (Readonly Report)
    basic = fields.Float(related='contract_id.basic', readonly=True)
    hra = fields.Float(related='contract_id.hra', readonly=True)
    uniform_allowance = fields.Float(related='contract_id.uniform_allowance', readonly=True)
    children_education = fields.Float(related='contract_id.children_education', readonly=True)
    helper_allowance = fields.Float(related='contract_id.helper_allowance', readonly=True)
    medical_reimbursement = fields.Float(related='contract_id.medical_reimbursement', readonly=True)
    transport_allowance = fields.Float(related='contract_id.transport_allowance', readonly=True)
    special_allowance = fields.Float(related='contract_id.special_allowance', readonly=True)
    gross_salary = fields.Float(related='contract_id.gross_salary', readonly=True)

    # Deductions
    pf_employee = fields.Float(related='contract_id.pf_employee', readonly=True)
    esi_employee = fields.Float(related='contract_id.esi_employee', readonly=True)
    tds = fields.Float(related='contract_id.tds', readonly=True)