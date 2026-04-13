from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    # ===== EARNINGS =====
    basic = fields.Float("Basic")
    hra = fields.Float("HRA (40%)", compute="_compute_hra", store=True)
    uniform_allowance = fields.Float("Uniform (1.5%)", compute="_compute_uniform", store=True)
    children_education = fields.Float("Children Education")
    helper_allowance = fields.Float("Helper Allowance")
    medical_reimbursement = fields.Float("Medical Reimbursement")
    transport_allowance = fields.Float("Transport")
    special_allowance = fields.Float("Special")

    gross_salary = fields.Float("Gross Salary", compute="_compute_gross", store=True)

    # ===== EXTRA =====
    pf_employer = fields.Float("PF Employer", compute="_compute_pf_emp", store=True)
    esi_employer = fields.Float("ESI Employer")
    lta = fields.Float("LTA (6.5%)", compute="_compute_lta", store=True)
    bonus = fields.Float("Bonus", compute="_compute_bonus", store=True)

    # ===== DEDUCTIONS =====
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

    @api.depends('basic')
    def _compute_pf_emp(self):
        for rec in self:
            rec.pf_employer = rec.basic * 0.1336

    @api.depends('basic')
    def _compute_lta(self):
        for rec in self:
            rec.lta = rec.basic * 0.065

    @api.depends('basic')
    def _compute_bonus(self):
        for rec in self:
            rec.bonus = 8758 * 0.0833

    @api.depends(
        'basic','hra','uniform_allowance','children_education',
        'helper_allowance','medical_reimbursement',
        'transport_allowance','special_allowance'
    )
    def _compute_gross(self):
        for rec in self:
            rec.gross_salary = sum([
                rec.basic, rec.hra, rec.uniform_allowance,
                rec.children_education, rec.helper_allowance,
                rec.medical_reimbursement, rec.transport_allowance,
                rec.special_allowance
            ])