from odoo import models, fields, api

# ─────────────────────────────────────────────────────────────
#  Indian Statutory Limits (Monthly)
# ─────────────────────────────────────────────────────────────
PF_WAGE_CEILING   = 15000   # PF calculated on max ₹15,000 basic
PF_RATE_EMPLOYER  = 12.0    # 12% employer share
PF_RATE_EMPLOYEE  = 12.0    # 12% employee share

ESI_WAGE_CEILING  = 21000   # ESI applicable if gross <= ₹21,000
ESI_RATE_EMPLOYER = 3.25    # 3.25% employer share
ESI_RATE_EMPLOYEE = 0.75    # 0.75% employee share

GRATUITY_RATE     = 4.81    # 4.81% of basic (15/26 ÷ 12 × 100)


class HrVersion(models.Model):
    _inherit = 'hr.version'

    # ── Currency ─────────────────────────────────────────────
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ── Annual CTC ───────────────────────────────────────────
    annual_ctc = fields.Monetary(string="Annual CTC", currency_field='currency_id')

    monthly_ctc = fields.Monetary(
        string="Monthly CTC",
        currency_field='currency_id',
        compute="_compute_monthly_ctc",
        store=True,
    )

    annual_gross = fields.Monetary(string="Annual Gross", currency_field='currency_id')
    monthly_gross = fields.Monetary(string="Monthly Gross", currency_field='currency_id')

    # ── Manual Toggle ────────────────────────────────────────
    manual_basic = fields.Boolean(string="Manual Basic")

    # ── Earnings ─────────────────────────────────────────────
    basic = fields.Monetary(
        string="Basic + DA",
        currency_field='currency_id',
        compute="_compute_basic",
        store=True,
        readonly=False,          # Allow manual override when manual_basic=True
    )
    basic_percent = fields.Float(string="Basic %", digits=(5, 2))

    hra = fields.Monetary(
        string="HRA",
        currency_field='currency_id',
        compute="_compute_hra",
        store=True,
    )
    hra_percent = fields.Float(string="HRA %", digits=(5, 2))

    uniform_allowance = fields.Monetary(
        string="Uniform Allowance",
        currency_field='currency_id',
        compute="_compute_uniform_allowance",
        store=True,
    )
    uniform_allowance_percent = fields.Float(string="Uniform Allowance %", digits=(5, 2))

    children_edu_allowance = fields.Monetary(
        string="Children Education Allowance",
        currency_field='currency_id',
        compute="_compute_children_allowance",
        store=True,
    )
    children_edu_allowance_percent = fields.Float(string="Children Education Allowance %", digits=(5, 2))

    helper_allowance = fields.Monetary(
        string="Helper Allowance",
        currency_field='currency_id',
        compute="_compute_helper_allowance",
        store=True,
    )
    helper_allowance_percent = fields.Float(string="Helper Allowance %", digits=(5, 2))

    medical_reimbursement = fields.Monetary(
        string="Medical Reimbursement",
        currency_field='currency_id',
        compute="_compute_medical",
        store=True,
    )
    medical_reimbursement_percent = fields.Float(string="Medical Reimbursement %", digits=(5, 2))

    transport_allowance = fields.Monetary(
        string="Transport Allowance",
        currency_field='currency_id',
        compute="_compute_transport",
        store=True,
    )
    transport_allowance_percent = fields.Float(string="Transport Allowance %", digits=(5, 2))

    special_allowance = fields.Monetary(
        string="Special Allowance",
        currency_field='currency_id',
        compute="_compute_special_allowance",
        store=True,
    )

    gross_salary = fields.Monetary(string="Gross Salary", currency_field='currency_id')

    # ── Employer Contribution ────────────────────────────────
    pf_employer = fields.Monetary(
        string="PF Employer",
        currency_field='currency_id',
        compute="_compute_pf_employer",
        store=True,
    )
    pf_employer_percent = fields.Float(
        string="PF Employer %", digits=(5, 2),
        default=PF_RATE_EMPLOYER,
    )

    esi_employer = fields.Monetary(
        string="ESI Employer",
        currency_field='currency_id',
        compute="_compute_esi_employer",
        store=True,
    )
    esi_employer_percent = fields.Float(
        string="ESI Employer %", digits=(5, 2),
        default=ESI_RATE_EMPLOYER,
    )

    bonus = fields.Monetary(
        string="Bonus",
        currency_field='currency_id',
        compute="_compute_bonus",
        store=True,
    )
    bonus_percent = fields.Float(string="Bonus %", digits=(5, 2))

    # ── Deductions ───────────────────────────────────────────
    pf_employee = fields.Monetary(
        string="PF Employee",
        currency_field='currency_id',
        compute="_compute_pf_employee",
        store=True,
    )
    pf_employee_percent = fields.Float(
        string="PF Employee %", digits=(5, 2),
        default=PF_RATE_EMPLOYEE,
    )

    esi_employee = fields.Monetary(
        string="ESI Employee",
        currency_field='currency_id',
        compute="_compute_esi_employee",
        store=True,
    )
    esi_employee_percent = fields.Float(
        string="ESI Employee %", digits=(5, 2),
        default=ESI_RATE_EMPLOYEE,
    )

    tds = fields.Monetary(string="TDS", currency_field='currency_id')
    tds_percent = fields.Float(string="TDS %", digits=(5, 2))

    ltc = fields.Monetary(
        string="Gratuity",
        currency_field='currency_id',
        compute="_compute_gratuity",
        store=True,
    )
    ltc_percent = fields.Float(
        string="Gratuity %", digits=(5, 2),
        default=GRATUITY_RATE,
    )

    # ══════════════════════════════════════════════════════════
    #  COMPUTE METHODS
    # ══════════════════════════════════════════════════════════

    @api.depends('annual_ctc')
    def _compute_monthly_ctc(self):
        for rec in self:
            rec.monthly_ctc = (rec.annual_ctc or 0.0) / 12.0

    # ── Basic + DA ───────────────────────────────────────────
    @api.depends('basic_percent', 'monthly_gross', 'manual_basic')
    def _compute_basic(self):
        """
        Manual Basic OFF  →  Auto-calculate from monthly_gross:
            - Gross > 30000  → basic_percent% of gross
            - 15000 < Gross <= 30000 → Fixed ₹15,000
            - Gross <= 15000 → Full gross

        Manual Basic ON  →  User enters basic manually; compute skips it
                            (readonly=False + store=True keeps the manual value).
        """
        for rec in self:
            if rec.manual_basic:
                # Do NOT overwrite the manually entered value.
                continue

            gross = rec.monthly_gross or 0.0
            if gross > 30000:
                rec.basic = gross * (rec.basic_percent or 0.0) / 100.0
            elif 15000 < gross <= 30000:
                rec.basic = 15000.0
            else:
                rec.basic = gross

    # ── Allowances (all depend on `basic`) ───────────────────
    @api.depends('hra_percent', 'basic')
    def _compute_hra(self):
        for rec in self:
            rec.hra = (rec.basic or 0.0) * (rec.hra_percent or 0.0) / 100.0

    @api.depends('uniform_allowance_percent', 'basic')
    def _compute_uniform_allowance(self):
        for rec in self:
            rec.uniform_allowance = (rec.basic or 0.0) * (rec.uniform_allowance_percent or 0.0) / 100.0

    @api.depends('children_edu_allowance_percent', 'basic')
    def _compute_children_allowance(self):
        for rec in self:
            rec.children_edu_allowance = (rec.basic or 0.0) * (rec.children_edu_allowance_percent or 0.0) / 100.0

    @api.depends('helper_allowance_percent', 'basic')
    def _compute_helper_allowance(self):
        for rec in self:
            rec.helper_allowance = (rec.basic or 0.0) * (rec.helper_allowance_percent or 0.0) / 100.0

    @api.depends('medical_reimbursement_percent', 'basic')
    def _compute_medical(self):
        for rec in self:
            rec.medical_reimbursement = (rec.basic or 0.0) * (rec.medical_reimbursement_percent or 0.0) / 100.0

    @api.depends('transport_allowance_percent', 'basic')
    def _compute_transport(self):
        for rec in self:
            rec.transport_allowance = (rec.basic or 0.0) * (rec.transport_allowance_percent or 0.0) / 100.0

    @api.depends(
        'monthly_gross', 'basic', 'hra',
        'uniform_allowance', 'children_edu_allowance',
        'helper_allowance', 'medical_reimbursement', 'transport_allowance',
    )
    def _compute_special_allowance(self):
        for rec in self:
            components = (
                (rec.basic or 0.0)
                + (rec.hra or 0.0)
                + (rec.uniform_allowance or 0.0)
                + (rec.children_edu_allowance or 0.0)
                + (rec.helper_allowance or 0.0)
                + (rec.medical_reimbursement or 0.0)
                + (rec.transport_allowance or 0.0)
            )
            rec.special_allowance = max((rec.monthly_gross or 0.0) - components, 0.0)

    # ── Employer Contribution ────────────────────────────────

    @api.depends('basic', 'pf_employer_percent')
    def _compute_pf_employer(self):
        """
        PF Employer = pf_employer_percent% of basic,
        capped at statutory ceiling (basic capped at ₹15,000).
        """
        for rec in self:
            pf_basic = min(rec.basic or 0.0, PF_WAGE_CEILING)
            rec.pf_employer = pf_basic * (rec.pf_employer_percent or PF_RATE_EMPLOYER) / 100.0

    @api.depends('monthly_gross', 'esi_employer_percent')
    def _compute_esi_employer(self):
        """
        ESI Employer applicable only if monthly gross <= ₹21,000.
        """
        for rec in self:
            gross = rec.monthly_gross or 0.0
            if gross <= ESI_WAGE_CEILING:
                rec.esi_employer = gross * (rec.esi_employer_percent or ESI_RATE_EMPLOYER) / 100.0
            else:
                rec.esi_employer = 0.0

    @api.depends('basic', 'bonus_percent')
    def _compute_bonus(self):
        """
        Bonus = bonus_percent% of basic.
        """
        for rec in self:
            rec.bonus = (rec.basic or 0.0) * (rec.bonus_percent or 0.0) / 100.0

    # ── Deductions ───────────────────────────────────────────

    @api.depends('basic', 'pf_employee_percent')
    def _compute_pf_employee(self):
        """
        PF Employee = pf_employee_percent% of basic,
        capped at statutory ceiling (basic capped at ₹15,000).
        """
        for rec in self:
            pf_basic = min(rec.basic or 0.0, PF_WAGE_CEILING)
            rec.pf_employee = pf_basic * (rec.pf_employee_percent or PF_RATE_EMPLOYEE) / 100.0

    @api.depends('monthly_gross', 'esi_employee_percent')
    def _compute_esi_employee(self):
        """
        ESI Employee applicable only if monthly gross <= ₹21,000.
        """
        for rec in self:
            gross = rec.monthly_gross or 0.0
            if gross <= ESI_WAGE_CEILING:
                rec.esi_employee = gross * (rec.esi_employee_percent or ESI_RATE_EMPLOYEE) / 100.0
            else:
                rec.esi_employee = 0.0

    @api.depends('basic', 'ltc_percent')
    def _compute_gratuity(self):
        """
        Gratuity = ltc_percent% of basic (default 4.81% = 15/26 per month).
        No statutory upper ceiling for monthly provision; just % of basic.
        """
        for rec in self:
            rec.ltc = (rec.basic or 0.0) * (rec.ltc_percent or GRATUITY_RATE) / 100.0


# ─────────────────────────────────────────────────────────────

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    version_id = fields.Many2one('hr.version', string="Contract Version")

    manual_basic = fields.Boolean(related='version_id.manual_basic', store=True, readonly=False)

    annual_ctc   = fields.Monetary(related='version_id.annual_ctc',   store=True, readonly=False)
    monthly_ctc  = fields.Monetary(related='version_id.monthly_ctc',  store=True, readonly=False)
    annual_gross = fields.Monetary(related='version_id.annual_gross', store=True, readonly=False)
    monthly_gross = fields.Monetary(related='version_id.monthly_gross', store=True, readonly=False)

    basic         = fields.Monetary(related='version_id.basic',         store=True, readonly=False)
    basic_percent = fields.Float(   related='version_id.basic_percent', store=True, readonly=False)

    hra         = fields.Monetary(related='version_id.hra',         store=True, readonly=False)
    hra_percent = fields.Float(   related='version_id.hra_percent', store=True, readonly=False)

    uniform_allowance         = fields.Monetary(related='version_id.uniform_allowance',         store=True, readonly=False)
    uniform_allowance_percent = fields.Float(   related='version_id.uniform_allowance_percent', store=True, readonly=False)

    children_edu_allowance         = fields.Monetary(related='version_id.children_edu_allowance',         store=True, readonly=False)
    children_edu_allowance_percent = fields.Float(   related='version_id.children_edu_allowance_percent', store=True, readonly=False)

    helper_allowance         = fields.Monetary(related='version_id.helper_allowance',         store=True, readonly=False)
    helper_allowance_percent = fields.Float(   related='version_id.helper_allowance_percent', store=True, readonly=False)

    medical_reimbursement         = fields.Monetary(related='version_id.medical_reimbursement',         store=True, readonly=False)
    medical_reimbursement_percent = fields.Float(   related='version_id.medical_reimbursement_percent', store=True, readonly=False)

    transport_allowance         = fields.Monetary(related='version_id.transport_allowance',         store=True, readonly=False)
    transport_allowance_percent = fields.Float(   related='version_id.transport_allowance_percent', store=True, readonly=False)

    special_allowance = fields.Monetary(related='version_id.special_allowance', store=True, readonly=False)

    # Employer
    pf_employer         = fields.Monetary(related='version_id.pf_employer',         store=True, readonly=False)
    pf_employer_percent = fields.Float(   related='version_id.pf_employer_percent', store=True, readonly=False)

    esi_employer         = fields.Monetary(related='version_id.esi_employer',         store=True, readonly=False)
    esi_employer_percent = fields.Float(   related='version_id.esi_employer_percent', store=True, readonly=False)

    bonus         = fields.Monetary(related='version_id.bonus',         store=True, readonly=False)
    bonus_percent = fields.Float(   related='version_id.bonus_percent', store=True, readonly=False)

    # Deductions
    pf_employee         = fields.Monetary(related='version_id.pf_employee',         store=True, readonly=False)
    pf_employee_percent = fields.Float(   related='version_id.pf_employee_percent', store=True, readonly=False)

    esi_employee         = fields.Monetary(related='version_id.esi_employee',         store=True, readonly=False)
    esi_employee_percent = fields.Float(   related='version_id.esi_employee_percent', store=True, readonly=False)

    tds         = fields.Monetary(related='version_id.tds',         store=True, readonly=False)
    tds_percent = fields.Float(   related='version_id.tds_percent', store=True, readonly=False)

    ltc         = fields.Monetary(related='version_id.ltc',         store=True, readonly=False)
    ltc_percent = fields.Float(   related='version_id.ltc_percent', store=True, readonly=False)
