from odoo import models, fields

class HrVersion(models.Model):
    _inherit = 'hr.version'

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    annual_ctc = fields.Monetary(string="Annual CTC", currency_field='currency_id')
    monthly_ctc = fields.Monetary(string="Monthly CTC", currency_field='currency_id')
    annual_gross = fields.Monetary(string="Annual Gross", currency_field='currency_id')
    monthly_gross = fields.Monetary(string="Monthly Gross", currency_field='currency_id')
    basic = fields.Monetary(string="Basic", currency_field='currency_id')
    hra = fields.Monetary(string="HRA", currency_field='currency_id')
    uniform_allowance = fields.Monetary(string="Uniform Allowance", currency_field='currency_id')
    children_edu_allowance = fields.Monetary(string="Children Education Allowance", currency_field='currency_id')
    helper_allowance = fields.Monetary(string="Helper Allowance", currency_field='currency_id')
    medical_reimbursement = fields.Monetary(string="Medical Reimbursement", currency_field='currency_id')
    transport_allowance = fields.Monetary(string="Transport Allowance", currency_field='currency_id')
    special_allowance = fields.Monetary(string="Special Allowance", currency_field='currency_id')
    gross_salary = fields.Monetary(string="Gross Salary", currency_field='currency_id')

    pf_employer = fields.Monetary(string="PF Employer", currency_field='currency_id')
    esi_employer = fields.Monetary(string="ESI Employer", currency_field='currency_id')
    ltc = fields.Monetary(string="LTC", currency_field='currency_id')
    bonus = fields.Monetary(string="Bonus", currency_field='currency_id')

    pf_employee = fields.Monetary(string="PF Employee", currency_field='currency_id')
    esi_employee = fields.Monetary(string="ESI Employee", currency_field='currency_id')
    tds = fields.Monetary(string="TDS", currency_field='currency_id')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    version_id = fields.Many2one('hr.version', string="Contract Version")

    annual_ctc = fields.Monetary(related='version_id.annual_ctc', store=True, readonly=False)
    monthly_ctc = fields.Monetary(related='version_id.monthly_ctc', store=True, readonly=False)
    annual_gross = fields.Monetary(related='version_id.annual_gross', store=True, readonly=False)
    monthly_gross = fields.Monetary(related='version_id.monthly_gross', store=True, readonly=False)
    basic = fields.Monetary(related='version_id.basic', store=True, readonly=False)
    hra = fields.Monetary(related='version_id.hra', store=True, readonly=False)
    uniform_allowance = fields.Monetary(related='version_id.uniform_allowance', store=True, readonly=False)
    children_edu_allowance = fields.Monetary(related='version_id.children_edu_allowance', store=True, readonly=False)
    helper_allowance = fields.Monetary(related='version_id.helper_allowance', store=True, readonly=False)
    medical_reimbursement = fields.Monetary(related='version_id.medical_reimbursement', store=True, readonly=False)
    transport_allowance = fields.Monetary(related='version_id.transport_allowance', store=True, readonly=False)
    special_allowance = fields.Monetary(related='version_id.special_allowance', store=True, readonly=False)
    gross_salary = fields.Monetary(related='version_id.gross_salary', store=True, readonly=False)

    pf_employer = fields.Monetary(related='version_id.pf_employer', store=True, readonly=False)
    esi_employer = fields.Monetary(related='version_id.esi_employer', store=True, readonly=False)
    ltc = fields.Monetary(related='version_id.ltc', store=True, readonly=False)
    bonus = fields.Monetary(related='version_id.bonus', store=True, readonly=False)

    pf_employee = fields.Monetary(related='version_id.pf_employee', store=True, readonly=False)
    esi_employee = fields.Monetary(related='version_id.esi_employee', store=True, readonly=False)
    tds = fields.Monetary(related='version_id.tds', store=True, readonly=False)
