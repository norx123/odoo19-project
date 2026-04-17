# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#############################################################################
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models


class HrPayslipInput(models.Model):
    """Payslip Input - Other Inputs tab on payslip form"""
    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'

    # Primary field: select from configured Other Input Types
    input_type_id = fields.Many2one(
        'hr.payslip.other.input.type',
        string='Type',
        help="Select from configured Other Input Types. "
             "Description and Code will be auto-filled.")

    name = fields.Char(
        string='Description',
        required=True,
        help='Name of the input')

    payslip_id = fields.Many2one(
        'hr.payslip',
        string='Pay Slip',
        required=True,
        help='Payslip related to the input',
        ondelete='cascade',
        index=True)

    sequence = fields.Integer(
        required=True,
        index=True,
        default=10,
        string="Sequence",
        help='Sequence to identify the record')

    code = fields.Char(
        required=True,
        string='Code',
        help="The code that can be used in the salary rules")

    date_from = fields.Date(
        string='Date From',
        help="Starting Date for Payslip Lines",
        required=True,
        default=datetime.now().strftime('%Y-%m-01'))

    date_to = fields.Date(
        string='Date To',
        help="Ending Date for Payslip Lines",
        required=True,
        default=str(
            datetime.now() + relativedelta.relativedelta(
                months=+1, day=1, days=-1))[:10])

    amount = fields.Float(
        string="Amount",
        help="Amount used in salary rule computation. "
             "For salary attachments this is auto-filled.")

    contract_id = fields.Many2one(
        'hr.version',
        string='Contract',
        required=True,
        help="The contract for which this input applies")

    @api.onchange('input_type_id')
    def _onchange_input_type_id(self):
        """Auto-fill Description and Code when Input Type is selected"""
        if self.input_type_id:
            self.name = self.input_type_id.name
            self.code = self.input_type_id.code
