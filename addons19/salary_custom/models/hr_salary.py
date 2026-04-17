from odoo import models, fields, api


class HrVersion(models.Model):
    _inherit = 'hr.version'

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    x_annual_ctc = fields.Monetary(string="Annual CTC", currency_field='currency_id')

    x_monthly_ctc = fields.Monetary(
        string="Monthly CTC",
        currency_field='currency_id',
        compute="_compute_monthly_ctc",
        store=True
    )

    x_monthly_gross = fields.Monetary(string="Monthly Gross", currency_field='currency_id')

    x_basic_percent = fields.Float(string="Basic %")

    x_basic = fields.Monetary(
        string="Basic",
        currency_field='currency_id',
        compute="_compute_basic",
        store=True
    )

    x_hra_percent = fields.Float(string="HRA %")

    x_hra = fields.Monetary(
        string="HRA",
        currency_field='currency_id',
        compute="_compute_hra",
        store=True
    )

    @api.depends('x_annual_ctc')
    def _compute_monthly_ctc(self):
        for rec in self:
            rec.x_monthly_ctc = (rec.x_annual_ctc or 0.0) / 12.0

    @api.depends('x_basic_percent', 'x_monthly_gross')
    def _compute_basic(self):
        for rec in self:
            rec.x_basic = (rec.x_monthly_gross or 0.0) * (rec.x_basic_percent or 0.0) / 100.0

    @api.depends('x_hra_percent', 'x_monthly_ctc')
    def _compute_hra(self):
        for rec in self:
            rec.x_hra = (rec.x_monthly_ctc or 0.0) * (rec.x_hra_percent or 0.0) / 100.0


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    version_id = fields.Many2one('hr.version', string="Contract Version")

    x_annual_ctc = fields.Monetary(related='version_id.x_annual_ctc', store=True)
    x_monthly_ctc = fields.Monetary(related='version_id.x_monthly_ctc', store=True)
    x_monthly_gross = fields.Monetary(related='version_id.x_monthly_gross', store=True)

    x_basic = fields.Monetary(related='version_id.x_basic', store=True)
    x_basic_percent = fields.Float(related='version_id.x_basic_percent', store=True)

    x_hra = fields.Monetary(related='version_id.x_hra', store=True)
    x_hra_percent = fields.Float(related='version_id.x_hra_percent', store=True)
