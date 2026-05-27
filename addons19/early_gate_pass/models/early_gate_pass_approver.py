# -*- coding: utf-8 -*-
from odoo import fields, models


class EarlyGatePassApprover(models.Model):
    """Approver line model for Early Gate Pass requests."""
    _name = 'early.gate.pass.approver'
    _description = 'Early Gate Pass Approver Line'

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
    gate_pass_id = fields.Many2one(
        'early.gate.pass', string='Gate Pass',
        ondelete='cascade'
    )
