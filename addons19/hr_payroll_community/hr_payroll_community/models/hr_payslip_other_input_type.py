# -*- coding: utf-8 -*-
from odoo import fields, models


class HrPayslipOtherInputType(models.Model):
    """Model for managing Other Input Types for payslips"""
    _name = 'hr.payslip.other.input.type'
    _description = 'Payslip Other Input Type'
    _order = 'name'

    name = fields.Char(string='Description', required=True,
                       help="Description of the other input type (e.g. Child Support, Bonus)")
    code = fields.Char(string='Code', required=True,
                       help="Unique code used in salary rules (e.g. CHILDSUPPORT)")
    country_id = fields.Many2one('res.country', string='Country',
                                 default=lambda self: self.env.company.country_id)
    available_in_attachments = fields.Boolean(
        string='Available in Attachments',
        help="If checked, this input type will be available in Salary Attachments")
    struct_ids = fields.Many2many(
        'hr.payroll.structure',
        string='Availability in Structure',
        help="Salary structures where this input type is available. Leave empty for all structures.")

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code for Other Input Type must be unique!')
    ]
