
from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # 80C
    epf_file = fields.Binary()
    epf_amount = fields.Float()

    life_insurance_file = fields.Binary()
    life_insance_amount = fields.Float()

    elss_file = fields.Binary()
    elss_amount = fields.Float()

    ppf_file = fields.Binary()
    ppf_amount = fields.Float()

    nsc_file = fields.Binary()
    nsc_amount = fields.Float()

    fd_file = fields.Binary()
    fd_amount = fields.Float()

    home_loan_principal_file = fields.Binary()
    home_loan_principal_amount = fields.Float()

    tuition_file = fields.Binary()
    tuition_amount = fields.Float()

    ssy_file = fields.Binary()
    ssy_amount = fields.Float()

    total_80c = fields.Float()

    # 80D
    health_insurance = fields.Binary()
    policy_copy = fields.Binary()
    payment_proof = fields.Binary()

    medical_self_family = fields.Float()
    medical_parents_below60 = fields.Float()
    medical_parents_above60 = fields.Float()
    total_80d = fields.Float()

    # 80E
    edu_interest_cert = fields.Binary()
    loan_sanction = fields.Binary()
    repayment_schedule = fields.Binary()
    total_80e = fields.Float()

    # 80CCD
    nps_statement = fields.Binary()
    pran_card = fields.Binary()
    total_nps = fields.Float()

    # 80G
    donation_receipt = fields.Binary()
    donation_proof = fields.Binary()
    donee_pan = fields.Binary()
    total_donation = fields.Float()

    # 80TTA
    bank_statement = fields.Binary()
    interest_cert = fields.Binary()
    form16a = fields.Binary()
    total_interest = fields.Float()

    # 80EE
    home_interest_cert = fields.Binary()
    loan_agreement = fields.Binary()
    property_docs = fields.Binary()
    housing_interest = fields.Float()

    # HRA
    rent_receipts = fields.Binary()
    rent_agreement = fields.Binary()
    landlord_pan = fields.Binary()
    total_rent_paid = fields.Float()
    hra_exemption = fields.Float()

    # NEW TAX
    bank_interest_new = fields.Binary()
    capital_gain = fields.Binary()
    other_income = fields.Binary()
    total_new_tax = fields.Float()
