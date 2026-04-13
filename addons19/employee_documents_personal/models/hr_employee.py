from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Aadhar
    aadhar_number = fields.Char(string="Aadhar Number")
    aadhar_file = fields.Binary(string="Upload Aadhar")

    # PAN
    pan_number = fields.Char(string="PAN Number")
    pan_file = fields.Binary(string="Upload PAN")

    # Driving License
    driving_license = fields.Char(string="Driving License")
    driving_file = fields.Binary(string="Upload License")

    # Address Proof
    address_proof_type = fields.Selection([
        ('aadhar', 'Aadhar'),
        ('voter', 'Voter ID'),
        ('passport', 'Passport'),
        ('dl', 'Driving License')
    ], string="Address Proof Type")

    address_proof_file = fields.Binary(string="Upload Address Proof")