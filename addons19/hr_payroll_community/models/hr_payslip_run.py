# -*- coding: utf-8 -*-
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipRun(models.Model):
    """Payslip Batches - Draft → Waiting → Done → Paid workflow"""
    _name = 'hr.payslip.run'
    _description = 'Payslip Batches'

    name = fields.Char(required=True, string="Name",
                       help="Name for Payslip Batches")
    slip_ids = fields.One2many('hr.payslip', 'payslip_run_id',
                               string='Payslips',
                               help="Payslips in this batch")
    state = fields.Selection([
        ('draft',  'Draft'),
        ('verify', 'Waiting'),
        ('done',   'Done'),
        ('paid',   'Paid'),
        ('close',  'Close'),
    ], string='Status', index=True, readonly=True,
       copy=False, default='draft',
       help="Status of the payslip batch")

    date_start = fields.Date(
        string='Date From', required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=1)))
    date_end = fields.Date(
        string='Date To', required=True,
        default=lambda self: fields.Date.to_string(
            (datetime.now() + relativedelta(months=+1, day=1, days=-1)).date()))
    credit_note = fields.Boolean(
        string='Credit Note',
        help="If checked, all payslips generated are refund payslips.")

    # ── Workflow actions ────────────────────────────────────────────────────

    def action_payslip_run(self):
        """Reset batch to Draft"""
        return self.write({'state': 'draft'})

    def action_payslip_verify(self):
        """Move batch to Waiting — also move all draft payslips to verify"""
        for run in self:
            run.slip_ids.filtered(
                lambda s: s.state == 'draft'
            ).write({'state': 'verify'})
        return self.write({'state': 'verify'})

    def action_payslip_done(self):
        """Validate batch → Done — compute & confirm all waiting payslips"""
        for run in self:
            waiting_slips = run.slip_ids.filtered(
                lambda s: s.state == 'verify')
            for slip in waiting_slips:
                slip.action_compute_sheet()
            waiting_slips.write({'state': 'done'})
        return self.write({'state': 'done'})

    def action_payslip_paid(self):
        """Mark batch as Paid — mark all done payslips as paid"""
        for run in self:
            run.slip_ids.filtered(
                lambda s: s.state == 'done'
            ).write({'state': 'paid', 'paid': True})
        return self.write({'state': 'paid'})

    def close_payslip_run(self):
        """Close the batch"""
        return self.write({'state': 'close'})
