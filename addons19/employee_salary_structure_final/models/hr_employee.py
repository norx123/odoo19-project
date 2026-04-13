from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    basic = fields.Float("Basic")
    hra = fields.Float(compute="_compute_hra", store=True)
    uniform_allowance = fields.Float(compute="_compute_uniform", store=True)
    children_education = fields.Float("Children Education Allowance")
    helper_allowance = fields.Float("Helper Allowance")
    medical_reimbursement = fields.Float("Medical Reimbursement")
    transport_allowance = fields.Float("Transport Allowance")
    special_allowance = fields.Float("Special Allowance")
    gross_salary = fields.Float(compute="_compute_gross", store=True)

    pf_employee = fields.Float("PF Employee")
    esi_employee = fields.Float("ESI Employee")
    tds = fields.Float("TDS")

    @api.depends('basic')
    def _compute_hra(self):
        for rec in self:
            rec.hra = rec.basic * 0.40

    @api.depends('basic')
    def _compute_uniform(self):
        for rec in self:
            rec.uniform_allowance = rec.basic * 0.015

    @api.depends('basic','hra','uniform_allowance','children_education','helper_allowance','medical_reimbursement','transport_allowance','special_allowance')
    def _compute_gross(self):
        for rec in self:
            rec.gross_salary = sum([
                rec.basic, rec.hra, rec.uniform_allowance,
                rec.children_education, rec.helper_allowance,
                rec.medical_reimbursement, rec.transport_allowance,
                rec.special_allowance
            ])
