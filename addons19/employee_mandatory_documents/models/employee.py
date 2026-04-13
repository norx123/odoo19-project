from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    aadhar_number = fields.Char("Aadhar Number")
    aadhar_file = fields.Binary("Upload Aadhar")
    aadhar_issue_date = fields.Date("Issue Date")
    aadhar_expiry_date = fields.Date("Expiry Date")

    pan_number = fields.Char("PAN Number")
    pan_file = fields.Binary("Upload PAN")

    passport_number = fields.Char("Passport Number")
    passport_file = fields.Binary("Upload Passport")
    passport_issue_date = fields.Date("Issue Date")
    passport_expiry_date = fields.Date("Expiry Date")

    driving_license = fields.Char("Driving License")
    driving_file = fields.Binary("Upload License")
    driving_issue_date = fields.Date("Issue Date")
    driving_expiry_date = fields.Date("Expiry Date")

    address_proof_type = fields.Selection([
        ('aadhar', 'Aadhar'),
        ('voter', 'Voter ID'),
        ('electricity', 'Electricity Bill'),
    ], string="Address Proof Type")

    address_proof_file = fields.Binary("Upload Address Proof")

    tenth_certificate = fields.Binary("10th Certificate")
    tenth_board = fields.Char("Board")
    tenth_year = fields.Char("Year")

    twelfth_certificate = fields.Binary("12th Certificate")
    twelfth_board = fields.Char("Board")
    twelfth_year = fields.Char("Year")

    graduation_certificate = fields.Binary("Graduation Certificate")
    graduation_university = fields.Char("University")
    graduation_year = fields.Char("Year")

    post_graduation_certificate = fields.Binary("Post Graduation Certificate")

    bank_account = fields.Char("Account Number")
    bank_name = fields.Char("Bank Name")
    ifsc_code = fields.Char("IFSC Code")
    branch_name = fields.Char("Branch")
    bank_proof = fields.Binary("Upload Bank Proof")

    resume = fields.Binary("Resume")
    offer_letter = fields.Binary("Offer Letter")
    appointment_letter = fields.Binary("Appointment Letter")
    experience_letter = fields.Binary("Experience Letter")
    relieving_letter = fields.Binary("Relieving Letter")

    document_status = fields.Selection([
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
    ], string="Status", default='pending')

    remarks = fields.Text("Remarks")
