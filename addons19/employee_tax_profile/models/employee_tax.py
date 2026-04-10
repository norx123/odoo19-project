from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    hra_bill = fields.Float("HRA Bill")
    pf_employee = fields.Float("PF Employee")
    house_loan = fields.Float("House Loan")
    tuition_fees = fields.Float("Tuition Fees")
    sukanya = fields.Float("Sukanya Scheme")
    health_insurance = fields.Float("Health Insurance")
    nps = fields.Float("NPS")
    preventive_health = fields.Float("Preventive Health")

    previous_employer = fields.Char("Previous Employer")
    previous_salary = fields.Float("Previous Salary")
    previous_tax = fields.Float("Previous Tax Paid")

    basic_apr = fields.Float("Basic April")
    basic_may = fields.Float("Basic May")
    basic_jun = fields.Float("Basic June")

    hra_apr = fields.Float("HRA April")
    hra_may = fields.Float("HRA May")
    hra_jun = fields.Float("HRA June")

    special_apr = fields.Float("Special April")
    special_may = fields.Float("Special May")
    special_jun = fields.Float("Special June")

    gross_salary = fields.Float("Gross Salary")
    total_tax = fields.Float("Total Tax")
