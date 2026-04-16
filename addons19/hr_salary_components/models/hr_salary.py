from odoo import models, fields, api


class HrVersion(models.Model):
    _inherit = 'hr.version'

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ── Annual CTC (Base values — no percentage) ─────────────────────────────
    annual_ctc = fields.Monetary(string="Annual CTC", currency_field='currency_id')
    monthly_ctc = fields.Monetary(string="Monthly CTC", currency_field='currency_id')
    annual_gross = fields.Monetary(string="Annual Gross", currency_field='currency_id')
    monthly_gross = fields.Monetary(string="Monthly Gross", currency_field='currency_id')

    # ── Earnings ─────────────────────────────────────────────────────────────
    basic = fields.Monetary(string="Basic", currency_field='currency_id')
    basic_percent = fields.Float(string="Basic %", digits=(5, 2))

    hra = fields.Monetary(string="HRA", currency_field='currency_id')
    hra_percent = fields.Float(string="HRA %", digits=(5, 2))

    uniform_allowance = fields.Monetary(string="Uniform Allowance", currency_field='currency_id')
    uniform_allowance_percent = fields.Float(string="Uniform Allowance %", digits=(5, 2))

    children_edu_allowance = fields.Monetary(string="Children Education Allowance", currency_field='currency_id')
    children_edu_allowance_percent = fields.Float(string="Children Education Allowance %", digits=(5, 2))

    helper_allowance = fields.Monetary(string="Helper Allowance", currency_field='currency_id')
    helper_allowance_percent = fields.Float(string="Helper Allowance %", digits=(5, 2))

    medical_reimbursement = fields.Monetary(string="Medical Reimbursement", currency_field='currency_id')
    medical_reimbursement_percent = fields.Float(string="Medical Reimbursement %", digits=(5, 2))

    transport_allowance = fields.Monetary(string="Transport Allowance", currency_field='currency_id')
    transport_allowance_percent = fields.Float(string="Transport Allowance %", digits=(5, 2))

    special_allowance = fields.Monetary(string="Special Allowance", currency_field='currency_id')
    special_allowance_percent = fields.Float(string="Special Allowance %", digits=(5, 2))

    gross_salary = fields.Monetary(string="Gross Salary", currency_field='currency_id')

    # ── Employer Contribution ────────────────────────────────────────────────
    pf_employer = fields.Monetary(string="PF Employer", currency_field='currency_id')
    pf_employer_percent = fields.Float(string="PF Employer %", digits=(5, 2))

    esi_employer = fields.Monetary(string="ESI Employer", currency_field='currency_id')
    esi_employer_percent = fields.Float(string="ESI Employer %", digits=(5, 2))

    # ltc = fields.Monetary(string="Gratuity", currency_field='currency_id')
    # ltc_percent = fields.Float(string="Gratuity %", digits=(5, 2))

    bonus = fields.Monetary(string="Bonus", currency_field='currency_id')
    bonus_percent = fields.Float(string="Bonus %", digits=(5, 2))

    # ── Deductions ───────────────────────────────────────────────────────────
    pf_employee = fields.Monetary(string="PF Employee", currency_field='currency_id')
    pf_employee_percent = fields.Float(string="PF Employee %", digits=(5, 2))

    esi_employee = fields.Monetary(string="ESI Employee", currency_field='currency_id')
    esi_employee_percent = fields.Float(string="ESI Employee %", digits=(5, 2))

    tds = fields.Monetary(string="TDS", currency_field='currency_id')
    tds_percent = fields.Float(string="TDS %", digits=(5, 2))

    ltc = fields.Monetary(string="Gratuity", currency_field='currency_id')
    ltc_percent = fields.Float(string="Gratuity %", digits=(5, 2))

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _pct_of_ctc(self, percent):
        """Calculate amount from monthly_ctc and percent."""
        return round((self.monthly_ctc or 0.0) * percent / 100.0, 2)

    def _pct_of_gross(self, percent):
        """Calculate amount from monthly_gross and percent."""
        return round((self.monthly_gross or 0.0) * percent / 100.0, 2)

    # ── Annual CTC → Monthly CTC (auto) ──────────────────────────────────────
    @api.onchange('annual_ctc')
    def _onchange_annual_ctc(self):
        if self.annual_ctc:
            self.monthly_ctc = round(self.annual_ctc / 12.0, 2)

    # ── Annual Gross → Monthly Gross (auto) + recalc Basic ───────────────────
    @api.onchange('annual_gross')
    def _onchange_annual_gross(self):
        if self.annual_gross:
            self.monthly_gross = round(self.annual_gross / 12.0, 2)
            if self.basic_percent:
                self.basic = self._pct_of_gross(self.basic_percent)

    # ── Basic: % of Monthly Gross ─────────────────────────────────────────────
    @api.onchange('basic_percent', 'monthly_gross')
    def _onchange_basic_percent(self):
        if self.basic_percent:
            self.basic = self._pct_of_gross(self.basic_percent)

    # ── All other % fields: base = monthly_ctc ───────────────────────────────
    @api.onchange('hra_percent', 'monthly_ctc')
    def _onchange_hra_percent(self):
        if self.hra_percent:
            self.hra = self._pct_of_ctc(self.hra_percent)

    @api.onchange('uniform_allowance_percent', 'monthly_ctc')
    def _onchange_uniform_allowance_percent(self):
        if self.uniform_allowance_percent:
            self.uniform_allowance = self._pct_of_ctc(self.uniform_allowance_percent)

    @api.onchange('children_edu_allowance_percent', 'monthly_ctc')
    def _onchange_children_edu_allowance_percent(self):
        if self.children_edu_allowance_percent:
            self.children_edu_allowance = self._pct_of_ctc(self.children_edu_allowance_percent)

    @api.onchange('helper_allowance_percent', 'monthly_ctc')
    def _onchange_helper_allowance_percent(self):
        if self.helper_allowance_percent:
            self.helper_allowance = self._pct_of_ctc(self.helper_allowance_percent)

    @api.onchange('medical_reimbursement_percent', 'monthly_ctc')
    def _onchange_medical_reimbursement_percent(self):
        if self.medical_reimbursement_percent:
            self.medical_reimbursement = self._pct_of_ctc(self.medical_reimbursement_percent)

    @api.onchange('transport_allowance_percent', 'monthly_ctc')
    def _onchange_transport_allowance_percent(self):
        if self.transport_allowance_percent:
            self.transport_allowance = self._pct_of_ctc(self.transport_allowance_percent)

    @api.onchange('special_allowance_percent', 'monthly_ctc')
    def _onchange_special_allowance_percent(self):
        if self.special_allowance_percent:
            self.special_allowance = self._pct_of_ctc(self.special_allowance_percent)

    @api.onchange('pf_employer_percent', 'monthly_ctc')
    def _onchange_pf_employer_percent(self):
        if self.pf_employer_percent:
            self.pf_employer = self._pct_of_ctc(self.pf_employer_percent)

    @api.onchange('esi_employer_percent', 'monthly_ctc')
    def _onchange_esi_employer_percent(self):
        if self.esi_employer_percent:
            self.esi_employer = self._pct_of_ctc(self.esi_employer_percent)

    @api.onchange('ltc_percent', 'monthly_ctc')
    def _onchange_ltc_percent(self):
        if self.ltc_percent:
            self.ltc = self._pct_of_ctc(self.ltc_percent)

    @api.onchange('bonus_percent', 'monthly_ctc')
    def _onchange_bonus_percent(self):
        if self.bonus_percent:
            self.bonus = self._pct_of_ctc(self.bonus_percent)

    @api.onchange('pf_employee_percent', 'monthly_ctc')
    def _onchange_pf_employee_percent(self):
        if self.pf_employee_percent:
            self.pf_employee = self._pct_of_ctc(self.pf_employee_percent)

    @api.onchange('esi_employee_percent', 'monthly_ctc')
    def _onchange_esi_employee_percent(self):
        if self.esi_employee_percent:
            self.esi_employee = self._pct_of_ctc(self.esi_employee_percent)

    @api.onchange('tds_percent', 'monthly_ctc')
    def _onchange_tds_percent(self):
        if self.tds_percent:
            self.tds = self._pct_of_ctc(self.tds_percent)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    version_id = fields.Many2one('hr.version', string="Contract Version")

    # ── Annual CTC ───────────────────────────────────────────────────────────
    annual_ctc = fields.Monetary(related='version_id.annual_ctc', store=True, readonly=False)
    monthly_ctc = fields.Monetary(related='version_id.monthly_ctc', store=True, readonly=False)
    annual_gross = fields.Monetary(related='version_id.annual_gross', store=True, readonly=False)
    monthly_gross = fields.Monetary(related='version_id.monthly_gross', store=True, readonly=False)

    # ── Earnings ─────────────────────────────────────────────────────────────
    basic = fields.Monetary(related='version_id.basic', store=True, readonly=False)
    basic_percent = fields.Float(related='version_id.basic_percent', store=True, readonly=False)

    hra = fields.Monetary(related='version_id.hra', store=True, readonly=False)
    hra_percent = fields.Float(related='version_id.hra_percent', store=True, readonly=False)

    uniform_allowance = fields.Monetary(related='version_id.uniform_allowance', store=True, readonly=False)
    uniform_allowance_percent = fields.Float(related='version_id.uniform_allowance_percent', store=True, readonly=False)

    children_edu_allowance = fields.Monetary(related='version_id.children_edu_allowance', store=True, readonly=False)
    children_edu_allowance_percent = fields.Float(related='version_id.children_edu_allowance_percent', store=True, readonly=False)

    helper_allowance = fields.Monetary(related='version_id.helper_allowance', store=True, readonly=False)
    helper_allowance_percent = fields.Float(related='version_id.helper_allowance_percent', store=True, readonly=False)

    medical_reimbursement = fields.Monetary(related='version_id.medical_reimbursement', store=True, readonly=False)
    medical_reimbursement_percent = fields.Float(related='version_id.medical_reimbursement_percent', store=True, readonly=False)

    transport_allowance = fields.Monetary(related='version_id.transport_allowance', store=True, readonly=False)
    transport_allowance_percent = fields.Float(related='version_id.transport_allowance_percent', store=True, readonly=False)

    special_allowance = fields.Monetary(related='version_id.special_allowance', store=True, readonly=False)
    special_allowance_percent = fields.Float(related='version_id.special_allowance_percent', store=True, readonly=False)

    gross_salary = fields.Monetary(related='version_id.gross_salary', store=True, readonly=False)

    # ── Employer Contribution ────────────────────────────────────────────────
    pf_employer = fields.Monetary(related='version_id.pf_employer', store=True, readonly=False)
    pf_employer_percent = fields.Float(related='version_id.pf_employer_percent', store=True, readonly=False)

    esi_employer = fields.Monetary(related='version_id.esi_employer', store=True, readonly=False)
    esi_employer_percent = fields.Float(related='version_id.esi_employer_percent', store=True, readonly=False)

    # ltc = fields.Monetary(related='version_id.ltc', store=True, readonly=False)
    # ltc_percent = fields.Float(related='version_id.ltc_percent', store=True, readonly=False)

    bonus = fields.Monetary(related='version_id.bonus', store=True, readonly=False)
    bonus_percent = fields.Float(related='version_id.bonus_percent', store=True, readonly=False)

    # ── Deductions ───────────────────────────────────────────────────────────
    pf_employee = fields.Monetary(related='version_id.pf_employee', store=True, readonly=False)
    pf_employee_percent = fields.Float(related='version_id.pf_employee_percent', store=True, readonly=False)

    esi_employee = fields.Monetary(related='version_id.esi_employee', store=True, readonly=False)
    esi_employee_percent = fields.Float(related='version_id.esi_employee_percent', store=True, readonly=False)

    tds = fields.Monetary(related='version_id.tds', store=True, readonly=False)
    tds_percent = fields.Float(related='version_id.tds_percent', store=True, readonly=False)

    ltc = fields.Monetary(related='version_id.ltc', store=True, readonly=False)
    ltc_percent = fields.Float(related='version_id.ltc_percent', store=True, readonly=False)
