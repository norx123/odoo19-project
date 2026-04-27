
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # 80C
    epf_file = fields.Binary("EPF Statement")
    epf_amount = fields.Float("EPF Amount")

    life_insurance_file = fields.Binary("Life Insurance")
    life_insance_amount = fields.Float("Life Insurance Amount")

    elss_file = fields.Binary("ELSS Mutual Funds")
    elss_amount = fields.Float("ELSS Amount")

    ppf_file = fields.Binary("PPF Passbook")
    ppf_amount = fields.Float("PPF Amount")

    nsc_file = fields.Binary("NSC Certificate")
    nsc_amount = fields.Float("NSC Amount")

    fd_file = fields.Binary("5-year FD Receipt")
    fd_amount = fields.Float("5-year FD Amount")

    home_loan_principal_file = fields.Binary("Home Loan Principal")
    home_loan_principal_amount = fields.Float("Home Loan Principal Amount")

    tuition_file = fields.Binary("Tuition Fees Receipts (2 children)")
    tuition_amount = fields.Float("Tuition Amount")

    ssy_file = fields.Binary("SSY Account Passbook")
    ssy_amount = fields.Float("SSY Amount")

    total_80c = fields.Float("Total Benfits of 80C")

    # 80D
    health_insurance = fields.Binary("Health Insurance Premium Receipts")
    policy_copy = fields.Binary("Policy Copy")
    payment_proof = fields.Binary("Payment Proof")

    medical_self_family = fields.Float("Medical Self Family")
    medical_parents_below60 = fields.Float("Medical Parents Below 60y")
    medical_parents_above60 = fields.Float("Medical Parents above 60y")
    total_80d = fields.Float("Total Benfits of 80D")

    # 80E
    edu_interest_cert = fields.Binary("Education Loan Interest Certificate")
    loan_sanction = fields.Binary("Loan Sanction Letter")
    repayment_schedule = fields.Binary("Repayment Schedule")
    total_80e = fields.Float()

    # 80CCD
    nps_statement = fields.Binary("NPS Contribution Statement")
    pran_card = fields.Binary("PRAN Card Copy")
    total_nps = fields.Float("Total Contribution for NPS")

    # 80G
    donation_receipt = fields.Binary("Donation Receipt")
    donation_proof = fields.Binary("Donation Proof")
    donee_pan = fields.Binary("Donee Pan Card")
    total_donation = fields.Float("Total Contribution for DONATION")

    # 80TTA
    bank_statement = fields.Binary("Bank Statement")
    interest_cert = fields.Binary("Interest Certificate")
    form16a = fields.Binary("Form 16A Receipt")
    total_interest = fields.Float("Total Contribution for Interest")

    # 80EE
    home_interest_cert = fields.Binary("Home Interest Certificate")
    loan_agreement = fields.Binary("Loan Agreement")
    property_docs = fields.Binary("Property Documents")
    housing_interest = fields.Float("Housing Interest Receipt")

    # HRA
    rent_receipts = fields.Binary("Rent Receipts")
    rent_agreement = fields.Binary("Rent Agreement")
    landlord_pan = fields.Binary("Landlord PAN Card")
    total_rent_paid = fields.Float("Total Contribution for Rent PAID")
    hra_exemption = fields.Float("HRA Exemption")

    # NEW TAX
    bank_interest_new = fields.Binary("Bank Interest New")
    capital_gain = fields.Binary("Capital Gain")
    other_income = fields.Binary("Other Income")
    total_new_tax = fields.Float("Total Contribution for New Tax")
