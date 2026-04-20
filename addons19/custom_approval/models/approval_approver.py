# -*- coding: utf-8 -*-
from odoo import fields, models


class ApprovalApproverLine(models.Model):
    """Common Approver Line model used across all approval types."""
    _name = 'approval.approver.line'
    _description = 'Approval Approver Line'

    approver_id = fields.Many2one(
        'res.users', string='Approver', required=True,
        help='User who is assigned as approver'
    )
    required = fields.Boolean(
        string='Required',
        help='If checked, this approver must approve before the request moves forward'
    )
    status = fields.Selection([
        ('new', 'New'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], string='Status', default='new', readonly=True)

    # Relations to parent models
    advance_salary_id = fields.Many2one(
        'custom.advance.salary', string='Advance Salary',
        ondelete='cascade'
    )
    loan_request_id = fields.Many2one(
        'custom.loan.request', string='Loan Request',
        ondelete='cascade'
    )
    resignation_id = fields.Many2one(
        'custom.resignation', string='Resignation',
        ondelete='cascade'
    )
    travel_request_id = fields.Many2one(
        'custom.travel.request', string='Travel Request',
        ondelete='cascade'
    )
