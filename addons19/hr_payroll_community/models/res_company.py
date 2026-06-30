# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    """Inherit res.company to store default Payroll settings"""
    _inherit = 'res.company'

    payslip_default_struct_id = fields.Many2one(
        'hr.payroll.structure',
        string='Default Salary Structure',
        help="Default salary structure used when generating payslips "
             "(individually or in batch) if none is selected manually.")
    payslip_default_journal_id = fields.Many2one(
        'account.journal',
        string='Default Salary Journal',
        domain="[('type', '=', 'general')]",
        help="Default journal used when generating payslips "
             "(individually or in batch) if none is selected manually.")
