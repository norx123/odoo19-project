from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ================= NEW TAX REGIME =================
    new_gross_salary = fields.Float("Gross salary")
    new_total_reimbursement = fields.Float("Total Reimbursement")
    new_prev_employer_salary = fields.Float("Previous employer gross salary")
    new_extra_payment = fields.Float("Total extra payment")

    new_total_salary = fields.Float(compute="_compute_new_total", store=True)
    new_standard_deduction = fields.Float("Standard Deduction", default=75000)

    new_taxfree = fields.Float("(Taxfree)")
    new_hra_bill = fields.Float("Section 10(13A) HRA Bill")
    new_pf_employee = fields.Float("PF Employee (Gross)")
    new_house_loan_payment = fields.Float("House Loan Payment")
    new_tuition_fees = fields.Float("Tuition Fees")
    new_sukanya = fields.Float("Sukanya Samriddhi Scheme")
    new_home_loan_interest = fields.Float("Housing Loan Interest Amount u/s 24")
    new_additional_home_loan = fields.Float("Additional Home Loan Interest Deduction (U/S/ECB/RBFE)")
    new_health_insurance_self = fields.Float("Health Insurance self")
    new_medical_insurance_parents = fields.Float("Medical Insurance Parents")
    new_nps = fields.Float("National Pension Scheme (NPS) u/s 80CCD1(B)")
    new_health_checkup = fields.Float("Preventive Health Checkup")
    new_health_checkup_parents = fields.Float("Preventive Health Checkup-Dependant Parents")

    new_net_taxable_salary = fields.Float(compute="_compute_new_taxable", store=True)
    new_tax_on_salary = fields.Float(compute="_compute_new_tax", store=True)

    new_rebate_87a = fields.Float("Less: Income tax rebate u/s 87A")
    new_surcharge = fields.Float("Surcharge")
    new_marginal_relief = fields.Float("Marginal Relief")
    new_cess = fields.Float("Education cess")

    new_total_tax = fields.Float(compute="_compute_new_final_tax", store=True)
    new_tax_paid = fields.Float("Tax deducted till date")
    new_remaining_tax = fields.Float(compute="_compute_new_remaining", store=True)
    new_remaining_months = fields.Integer("Remaining months", default=12)
    new_monthly_tds = fields.Float(compute="_compute_new_remaining", store=True)

    # ================= OLD TAX REGIME =================
    old_gross_salary = fields.Float("Gross salary")
    old_prev_employer_salary = fields.Float("Previous employer gross salary")
    old_extra_payment = fields.Float("Total extra payment")

    old_total_salary = fields.Float(compute="_compute_old_total", store=True)
    old_standard_deduction = fields.Float("Standard Deduction", default=50000)

    old_net_taxable_salary = fields.Float(compute="_compute_old_taxable", store=True)
    old_tax_on_salary = fields.Float(compute="_compute_old_tax", store=True)

    old_rebate_87a = fields.Float("Less: Income tax rebate u/s 87A")
    old_remaining_tax = fields.Float(compute="_compute_old_remaining", store=True)
    old_remaining_months = fields.Integer("Remaining months", default=12)
    old_monthly_tds = fields.Float(compute="_compute_old_remaining", store=True)

    # ================= CALCULATIONS =================

    @api.depends('new_gross_salary','new_prev_employer_salary','new_extra_payment')
    def _compute_new_total(self):
        for rec in self:
            rec.new_total_salary = rec.new_gross_salary + rec.new_prev_employer_salary + rec.new_extra_payment

    @api.depends('new_total_salary','new_standard_deduction','new_taxfree')
    def _compute_new_taxable(self):
        for rec in self:
            deductions = rec.new_standard_deduction + rec.new_taxfree
            rec.new_net_taxable_salary = max(rec.new_total_salary - deductions, 0)

    def _calculate_tax(self, amount):
        if amount <= 300000:
            return 0
        elif amount <= 600000:
            return (amount - 300000) * 0.05
        elif amount <= 900000:
            return 15000 + (amount - 600000) * 0.10
        elif amount <= 1200000:
            return 45000 + (amount - 900000) * 0.15
        elif amount <= 1500000:
            return 90000 + (amount - 1200000) * 0.20
        else:
            return 150000 + (amount - 1500000) * 0.30

    @api.depends('new_net_taxable_salary')
    def _compute_new_tax(self):
        for rec in self:
            rec.new_tax_on_salary = rec._calculate_tax(rec.new_net_taxable_salary)

    @api.depends('new_tax_on_salary','new_rebate_87a','new_surcharge','new_cess')
    def _compute_new_final_tax(self):
        for rec in self:
            tax = rec.new_tax_on_salary - rec.new_rebate_87a
            tax += rec.new_surcharge + rec.new_cess
            rec.new_total_tax = max(tax, 0)

    @api.depends('new_total_tax','new_tax_paid','new_remaining_months')
    def _compute_new_remaining(self):
        for rec in self:
            remaining = rec.new_total_tax - rec.new_tax_paid
            rec.new_remaining_tax = remaining
            rec.new_monthly_tds = remaining / rec.new_remaining_months if rec.new_remaining_months else 0

    # OLD

    @api.depends('old_gross_salary','old_prev_employer_salary','old_extra_payment')
    def _compute_old_total(self):
        for rec in self:
            rec.old_total_salary = rec.old_gross_salary + rec.old_prev_employer_salary + rec.old_extra_payment

    @api.depends('old_total_salary','old_standard_deduction')
    def _compute_old_taxable(self):
        for rec in self:
            rec.old_net_taxable_salary = max(rec.old_total_salary - rec.old_standard_deduction, 0)

    @api.depends('old_net_taxable_salary')
    def _compute_old_tax(self):
        for rec in self:
            rec.old_tax_on_salary = rec._calculate_tax(rec.old_net_taxable_salary)

    @api.depends('old_tax_on_salary','old_rebate_87a','old_remaining_months')
    def _compute_old_remaining(self):
        for rec in self:
            remaining = rec.old_tax_on_salary - rec.old_rebate_87a
            rec.old_remaining_tax = remaining
            rec.old_monthly_tds = remaining / rec.old_remaining_months if rec.old_remaining_months else 0