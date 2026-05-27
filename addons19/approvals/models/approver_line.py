# -*- coding: utf-8 -*-
from odoo import fields, models


class ApprovalsApproverLine(models.Model):
    """Common approver line for all approvals models."""
    _name = 'approvals.approver.line'
    _description = 'Approvals Approver Line'

    approver_id = fields.Many2one(
        'res.users', string='Approver', required=True,
        help='User assigned as approver'
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

    # Reverse links to parent records (one of these will be set)
    advance_salary_id = fields.Many2one(
        'approvals.advance.salary', string='Advance Salary',
        ondelete='cascade'
    )
    loan_request_id = fields.Many2one(
        'approvals.loan.request', string='Loan Request',
        ondelete='cascade'
    )
    resignation_id = fields.Many2one(
        'approvals.resignation', string='Resignation',
        ondelete='cascade'
    )
    travel_request_id = fields.Many2one(
        'approvals.travel.request', string='Travel Request',
        ondelete='cascade'
    )
    early_gate_pass_id = fields.Many2one(
        'approvals.early.gate.pass', string='Early Gate Pass',
        ondelete='cascade'
    )
