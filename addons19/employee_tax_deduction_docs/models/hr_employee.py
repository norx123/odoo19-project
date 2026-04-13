from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    epf_file = fields.Binary("EPF Statement")
    epf_amount = fields.Float()

    life_insurance_file = fields.Binary("Life Insurance")
    life_insurance_amount = fields.Float()

    elss_file = fields.Binary("ELSS Mutual Funds")
    elss_amount = fields.Float()

    ppf_file = fields.Binary("PPF Passbook")
    ppf_amount = fields.Float()

    nsc_file = fields.Binary("NSC Certificate")
    nsc_amount = fields.Float()

    fd_file = fields.Binary("5 Year FD")
    fd_amount = fields.Float()

    home_loan_principal_file = fields.Binary("Home Loan Principal")
    home_loan_principal_amount = fields.Float()

    tuition_file = fields.Binary("Tuition Fees")
    tuition_amount = fields.Float()

    ssy_file = fields.Binary("SSY Account")
    ssy_amount = fields.Float()

    health_insurance_file = fields.Binary("Health Insurance")
    policy_copy = fields.Binary("Policy Copy")
    payment_proof = fields.Binary("Payment Proof")

    medical_self = fields.Float()
    medical_parents_below = fields.Float()
    medical_parents_above = fields.Float()

    edu_loan_file = fields.Binary("Education Loan Interest")
    sanction_letter = fields.Binary("Loan Sanction")
    repayment_schedule = fields.Binary("Repayment Schedule")
    edu_interest_amount = fields.Float()

    nps_file = fields.Binary("NPS Statement")
    pran_copy = fields.Binary("PRAN Copy")
    nps_amount = fields.Float()

    donation_file = fields.Binary("Donation Receipt")
    donation_proof = fields.Binary("Donation Proof")
    donee_pan = fields.Binary("Donee PAN")
    donation_amount = fields.Float()

    rent_receipt = fields.Binary("Rent Receipt")
    rent_agreement = fields.Binary("Rent Agreement")
    landlord_pan = fields.Binary("Landlord PAN")
    total_rent = fields.Float()
