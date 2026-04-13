from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'

    basic = fields.Float("Basic")
    hra = fields.Float(compute="_compute_hra", store=True)
    pf_employee = fields.Float("PF Employee")

    @api.depends('basic')
    def _compute_hra(self):
        for rec in self:
            rec.hra = rec.basic * 0.40
