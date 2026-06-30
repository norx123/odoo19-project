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
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit res_config_settings model for adding some fields in Settings"""
    _inherit = 'res.config.settings'

    module_account_accountant = fields.Boolean(string='Account Accountant',
                                               help="Is Account Accountant")
    module_l10n_fr_hr_payroll = fields.Boolean(string='French Payroll',
                                               help="Is French Payroll")
    module_l10n_be_hr_payroll = fields.Boolean(string='Belgium Payroll',
                                               help="Is Belgium Payroll")
    module_l10n_in_hr_payroll = fields.Boolean(string='Indian Payroll',
                                               help="Is Indian Payroll")

    payslip_default_struct_id = fields.Many2one(
        'hr.payroll.structure',
        string='Default Salary Structure',
        help="Used automatically when generating payslips if none is "
             "selected manually.")
    payslip_default_journal_id = fields.Many2one(
        'account.journal',
        string='Default Salary Journal',
        domain="[('type', '=', 'general')]",
        help="Used automatically when generating payslips if none is "
             "selected manually.")

    @api.model
    def get_values(self):
        res = super().get_values()
        company = self.env.company
        res.update(
            payslip_default_struct_id=company.payslip_default_struct_id.id,
            payslip_default_journal_id=company.payslip_default_journal_id.id,
        )
        return res

    def set_values(self):
        super().set_values()
        self.env.company.write({
            'payslip_default_struct_id': self.payslip_default_struct_id.id,
            'payslip_default_journal_id': self.payslip_default_journal_id.id,
        })
