# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrSalaryAttachment(models.Model):
    """Model for managing Salary Attachments (deductions/additions) for employees"""
    _name = 'hr.salary.attachment'
    _description = 'Salary Attachment'
    _inherit = 'mail.thread'
    _order = 'employee_id, date_start'

    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True,
        tracking=True, help="Employee for whom this attachment applies")
    description = fields.Char(string='Description', required=True,
                               help="Description of this salary attachment")
    other_input_type_id = fields.Many2one(
        'hr.payslip.other.input.type',
        string='Type', required=True,
        help="Select the Other Input Type for this attachment")
    date_start = fields.Date(string='Start Date', required=True,
                              default=fields.Date.today,
                              help="Date from which this attachment applies")
    date_end = fields.Date(string='End Date',
                            help="Date until which this attachment applies. Leave empty for no end date.")
    no_end_date = fields.Boolean(string='No End Date', default=False)
    monthly_amount = fields.Float(string='Payslip Amount',
                                   help="Amount to be deducted/added per payslip")
    total_amount = fields.Float(string='Total Amount',
                                 help="Total amount for this attachment (0 = unlimited)")
    negative_value = fields.Boolean(
        string='Negative Value',
        help="If checked, the amount will be subtracted from the salary")
    document = fields.Binary(string='Document', attachment=True)
    document_filename = fields.Char(string='Document Filename')
    state = fields.Selection([
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='running', tracking=True)

    @api.onchange('no_end_date')
    def _onchange_no_end_date(self):
        if self.no_end_date:
            self.date_end = False

    def action_mark_completed(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_running(self):
        self.write({'state': 'running'})

    def _get_active_attachments(self, employee_id, date_from, date_to):
        """Return active salary attachments for an employee within a date range"""
        domain = [
            ('employee_id', '=', employee_id),
            ('state', '=', 'running'),
            ('date_start', '<=', date_to),
            '|',
            ('no_end_date', '=', True),
            '|',
            ('date_end', '=', False),
            ('date_end', '>=', date_from),
        ]
        return self.search(domain)
