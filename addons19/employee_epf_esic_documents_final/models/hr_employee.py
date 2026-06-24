from odoo import models, fields, api
from odoo.exceptions import ValidationError
import re

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ======================
    # WORK DETAILS
    # ======================
    employee_code = fields.Char("Employee Code")

    pf_number = fields.Char("PF Number")
    uan_number = fields.Char("UAN Number")
    esic_number = fields.Char("ESIC Number")
    pan_number = fields.Char("PAN Number")

    aadhar_number = fields.Char("Aadhar Number")
    aadhar_file = fields.Binary("Upload Aadhar")
    aadhar_file_name = fields.Char("Aadhar File Name")  # filename store karne ke liye

    pan_file = fields.Binary("Upload PAN")
    pan_file_name = fields.Char("PAN File Name")  # filename store karne ke liye

    driving_license = fields.Char("Driving License")
    driving_file = fields.Binary("Upload License")
    driving_file_name = fields.Char("License File Name")  # filename store karne ke liye

    address_proof_type = fields.Selection([
        ('aadhar', 'Aadhar'),
        ('voter', 'Voter ID'),
        ('passport', 'Passport'),
        ('other', 'Other')
    ], string="Address Proof Type")

    address_proof_file = fields.Binary("Upload Address Proof")
    address_proof_file_name = fields.Char("Address Proof File Name")  # filename store karne ke liye

    reference_contact_ids = fields.One2many(
        'hr.employee.reference',
        'employee_id',
        string="Reference Contacts"
    )

    emergency_contact_ids = fields.One2many(
        'hr.employee.emergency',
        'employee_id',
        string="Emergency Contacts"
    )

    @api.constrains('uan_number')
    def _check_uan(self):
        for rec in self:
            if rec.uan_number and not re.match(r'^\d{12}$', rec.uan_number):
                raise ValidationError("UAN must be 12 digits.")

    @api.constrains('pan_number')
    def _check_pan(self):
        for rec in self:
            if rec.pan_number and not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', rec.pan_number):
                raise ValidationError("Invalid PAN format (ABCDE1234F).")


class HrEmployeeReference(models.Model):
    _name = 'hr.employee.reference'
    _description = 'Employee Reference Contacts'

    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete='cascade')

    ref_name = fields.Char("Name")
    ref_relation = fields.Char("Relation")
    ref_mobile = fields.Char("Mobile Number")
    ref_email = fields.Char("Email ID")


class HrEmployeeEmergency(models.Model):
    _name = 'hr.employee.emergency'
    _description = 'Employee Emergency Contacts'

    employee_id = fields.Many2one('hr.employee', string="Employee", ondelete='cascade')

    contact_name = fields.Char("Name")
    contact_relation = fields.Char("Relation")
    contact_number = fields.Char("Contact No")
    contact_description = fields.Char("Description")
