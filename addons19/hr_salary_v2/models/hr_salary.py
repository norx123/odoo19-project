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

    annual_gross  = fields.Monetary(string="Annual Gross",  currency_field='currency_id')
    monthly_gross = fields.Monetary(string="Monthly Gross", currency_field='currency_id')

    # ── Manual Toggle ────────────────────────────────────────
    manual_basic = fields.Boolean(string="Manual Basic")

    # ── Earnings ─────────────────────────────────────────────
    basic = fields.Monetary(
        string="Basic + DA",
        currency_field='currency_id',
        compute="_compute_basic",
        store=True,
        readonly=False,
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

    @api.depends('basic_percent', 'monthly_gross', 'manual_basic')
    def _compute_basic(self):
        for rec in self:
            if rec.manual_basic:
                continue
            gross = rec.monthly_gross or 0.0
            if gross > 30000:
                rec.basic = gross * (rec.basic_percent or 0.0) / 100.0
            elif 15000 < gross <= 30000:
                rec.basic = 15000.0
            else:
                rec.basic = gross

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

    @api.depends('basic', 'pf_employer_percent')
    def _compute_pf_employer(self):
        for rec in self:
            pf_basic = min(rec.basic or 0.0, PF_WAGE_CEILING)
            rec.pf_employer = pf_basic * (rec.pf_employer_percent or PF_RATE_EMPLOYER) / 100.0

    @api.depends('monthly_gross', 'esi_employer_percent')
    def _compute_esi_employer(self):
        for rec in self:
            gross = rec.monthly_gross or 0.0
            if gross <= ESI_WAGE_CEILING:
                rec.esi_employer = gross * (rec.esi_employer_percent or ESI_RATE_EMPLOYER) / 100.0
            else:
                rec.esi_employer = 0.0

    @api.depends('basic', 'bonus_percent')
    def _compute_bonus(self):
        for rec in self:
            rec.bonus = (rec.basic or 0.0) * (rec.bonus_percent or 0.0) / 100.0

    @api.depends('basic', 'pf_employee_percent')
    def _compute_pf_employee(self):
        for rec in self:
            pf_basic = min(rec.basic or 0.0, PF_WAGE_CEILING)
            rec.pf_employee = pf_basic * (rec.pf_employee_percent or PF_RATE_EMPLOYEE) / 100.0

    @api.depends('monthly_gross', 'esi_employee_percent')
    def _compute_esi_employee(self):
        for rec in self:
            gross = rec.monthly_gross or 0.0
            if gross <= ESI_WAGE_CEILING:
                rec.esi_employee = gross * (rec.esi_employee_percent or ESI_RATE_EMPLOYEE) / 100.0
            else:
                rec.esi_employee = 0.0

    @api.depends('basic', 'ltc_percent')
    def _compute_gratuity(self):
        for rec in self:
            rec.ltc = (rec.basic or 0.0) * (rec.ltc_percent or GRATUITY_RATE) / 100.0


# ─────────────────────────────────────────────────────────────
#  HrEmployee  ──  NO store=True on salary fields
#  ─────────────────────────────────────────────────────────────
#  KEY FIX: Salary fields on hr.employee are computed on-the-fly
#  from the CURRENTLY selected version_id.  We do NOT store them,
#  so switching version_id immediately shows the new version's data
#  without any stale cached values bleeding through.
# ─────────────────────────────────────────────────────────────

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    version_id = fields.Many2one('hr.version', string="Contract Version")

    # ── currency (needed for Monetary fields) ────────────────
    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_salary_fields',
        string="Currency",
    )

    # ── Annual / Gross ────────────────────────────────────────
    manual_basic  = fields.Boolean(compute='_compute_salary_fields', inverse='_set_manual_basic',  string="Manual Basic")
    annual_ctc    = fields.Monetary(compute='_compute_salary_fields', inverse='_set_annual_ctc',    currency_field='currency_id', string="Annual CTC")
    monthly_ctc   = fields.Monetary(compute='_compute_salary_fields',                               currency_field='currency_id', string="Monthly CTC")
    annual_gross  = fields.Monetary(compute='_compute_salary_fields', inverse='_set_annual_gross',  currency_field='currency_id', string="Annual Gross")
    monthly_gross = fields.Monetary(compute='_compute_salary_fields', inverse='_set_monthly_gross', currency_field='currency_id', string="Monthly Gross")

    # ── Earnings ─────────────────────────────────────────────
    basic         = fields.Monetary(compute='_compute_salary_fields', inverse='_set_basic',         currency_field='currency_id', string="Basic + DA")
    basic_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_basic_percent',                               string="Basic %", digits=(5,2))

    hra           = fields.Monetary(compute='_compute_salary_fields',                               currency_field='currency_id', string="HRA")
    hra_percent   = fields.Float(   compute='_compute_salary_fields', inverse='_set_hra_percent',                                 string="HRA %", digits=(5,2))

    uniform_allowance         = fields.Monetary(compute='_compute_salary_fields',                                   currency_field='currency_id', string="Uniform Allowance")
    uniform_allowance_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_uniform_pct',                                     string="Uniform Allowance %", digits=(5,2))

    children_edu_allowance         = fields.Monetary(compute='_compute_salary_fields',                                      currency_field='currency_id', string="Children Education Allowance")
    children_edu_allowance_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_children_pct',                                          string="Children Education Allowance %", digits=(5,2))

    helper_allowance         = fields.Monetary(compute='_compute_salary_fields',                                  currency_field='currency_id', string="Helper Allowance")
    helper_allowance_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_helper_pct',                                      string="Helper Allowance %", digits=(5,2))

    medical_reimbursement         = fields.Monetary(compute='_compute_salary_fields',                                      currency_field='currency_id', string="Medical Reimbursement")
    medical_reimbursement_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_medical_pct',                                          string="Medical Reimbursement %", digits=(5,2))

    transport_allowance         = fields.Monetary(compute='_compute_salary_fields',                                    currency_field='currency_id', string="Transport Allowance")
    transport_allowance_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_transport_pct',                                      string="Transport Allowance %", digits=(5,2))

    special_allowance = fields.Monetary(compute='_compute_salary_fields', currency_field='currency_id', string="Special Allowance")

    # ── Employer Contribution ─────────────────────────────────
    pf_employer         = fields.Monetary(compute='_compute_salary_fields',                               currency_field='currency_id', string="PF Employer")
    pf_employer_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_pf_emp_pct',                                 string="PF Employer %", digits=(5,2))

    esi_employer         = fields.Monetary(compute='_compute_salary_fields',                                currency_field='currency_id', string="ESI Employer")
    esi_employer_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_esi_emp_pct',                                  string="ESI Employer %", digits=(5,2))

    bonus         = fields.Monetary(compute='_compute_salary_fields',                           currency_field='currency_id', string="Bonus")
    bonus_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_bonus_pct',                                 string="Bonus %", digits=(5,2))

    # ── Deductions ────────────────────────────────────────────
    pf_employee         = fields.Monetary(compute='_compute_salary_fields',                               currency_field='currency_id', string="PF Employee")
    pf_employee_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_pf_ee_pct',                                   string="PF Employee %", digits=(5,2))

    esi_employee         = fields.Monetary(compute='_compute_salary_fields',                                currency_field='currency_id', string="ESI Employee")
    esi_employee_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_esi_ee_pct',                                   string="ESI Employee %", digits=(5,2))

    tds         = fields.Monetary(compute='_compute_salary_fields', inverse='_set_tds',         currency_field='currency_id', string="TDS")
    tds_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_tds_pct',                                   string="TDS %", digits=(5,2))

    ltc         = fields.Monetary(compute='_compute_salary_fields',                    currency_field='currency_id', string="Gratuity")
    ltc_percent = fields.Float(   compute='_compute_salary_fields', inverse='_set_ltc_pct',                            string="Gratuity %", digits=(5,2))

    # ══════════════════════════════════════════════════════════
    #  MASTER COMPUTE  –  reads from version_id on every render
    # ══════════════════════════════════════════════════════════
    @api.depends('version_id',
                 'version_id.currency_id',
                 'version_id.manual_basic',
                 'version_id.annual_ctc', 'version_id.monthly_ctc',
                 'version_id.annual_gross', 'version_id.monthly_gross',
                 'version_id.basic', 'version_id.basic_percent',
                 'version_id.hra', 'version_id.hra_percent',
                 'version_id.uniform_allowance', 'version_id.uniform_allowance_percent',
                 'version_id.children_edu_allowance', 'version_id.children_edu_allowance_percent',
                 'version_id.helper_allowance', 'version_id.helper_allowance_percent',
                 'version_id.medical_reimbursement', 'version_id.medical_reimbursement_percent',
                 'version_id.transport_allowance', 'version_id.transport_allowance_percent',
                 'version_id.special_allowance',
                 'version_id.pf_employer', 'version_id.pf_employer_percent',
                 'version_id.esi_employer', 'version_id.esi_employer_percent',
                 'version_id.bonus', 'version_id.bonus_percent',
                 'version_id.pf_employee', 'version_id.pf_employee_percent',
                 'version_id.esi_employee', 'version_id.esi_employee_percent',
                 'version_id.tds', 'version_id.tds_percent',
                 'version_id.ltc', 'version_id.ltc_percent',
                 )
    def _compute_salary_fields(self):
        for emp in self:
            v = emp.version_id
            emp.currency_id               = v.currency_id             if v else self.env.company.currency_id
            emp.manual_basic              = v.manual_basic             if v else False
            emp.annual_ctc                = v.annual_ctc               if v else 0.0
            emp.monthly_ctc               = v.monthly_ctc              if v else 0.0
            emp.annual_gross              = v.annual_gross             if v else 0.0
            emp.monthly_gross             = v.monthly_gross            if v else 0.0
            emp.basic                     = v.basic                    if v else 0.0
            emp.basic_percent             = v.basic_percent            if v else 0.0
            emp.hra                       = v.hra                      if v else 0.0
            emp.hra_percent               = v.hra_percent              if v else 0.0
            emp.uniform_allowance         = v.uniform_allowance        if v else 0.0
            emp.uniform_allowance_percent = v.uniform_allowance_percent if v else 0.0
            emp.children_edu_allowance         = v.children_edu_allowance        if v else 0.0
            emp.children_edu_allowance_percent = v.children_edu_allowance_percent if v else 0.0
            emp.helper_allowance         = v.helper_allowance         if v else 0.0
            emp.helper_allowance_percent = v.helper_allowance_percent if v else 0.0
            emp.medical_reimbursement         = v.medical_reimbursement        if v else 0.0
            emp.medical_reimbursement_percent = v.medical_reimbursement_percent if v else 0.0
            emp.transport_allowance         = v.transport_allowance        if v else 0.0
            emp.transport_allowance_percent = v.transport_allowance_percent if v else 0.0
            emp.special_allowance         = v.special_allowance        if v else 0.0
            emp.pf_employer               = v.pf_employer              if v else 0.0
            emp.pf_employer_percent       = v.pf_employer_percent      if v else 0.0
            emp.esi_employer              = v.esi_employer             if v else 0.0
            emp.esi_employer_percent      = v.esi_employer_percent     if v else 0.0
            emp.bonus                     = v.bonus                    if v else 0.0
            emp.bonus_percent             = v.bonus_percent            if v else 0.0
            emp.pf_employee               = v.pf_employee              if v else 0.0
            emp.pf_employee_percent       = v.pf_employee_percent      if v else 0.0
            emp.esi_employee              = v.esi_employee             if v else 0.0
            emp.esi_employee_percent      = v.esi_employee_percent     if v else 0.0
            emp.tds                       = v.tds                      if v else 0.0
            emp.tds_percent               = v.tds_percent              if v else 0.0
            emp.ltc                       = v.ltc                      if v else 0.0
            emp.ltc_percent               = v.ltc_percent              if v else 0.0

    # ══════════════════════════════════════════════════════════
    #  INVERSE METHODS  –  write back to version_id
    # ══════════════════════════════════════════════════════════
    def _set_manual_basic(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.manual_basic = emp.manual_basic

    def _set_annual_ctc(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.annual_ctc = emp.annual_ctc

    def _set_annual_gross(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.annual_gross = emp.annual_gross

    def _set_monthly_gross(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.monthly_gross = emp.monthly_gross

    def _set_basic(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.basic = emp.basic

    def _set_basic_percent(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.basic_percent = emp.basic_percent

    def _set_hra_percent(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.hra_percent = emp.hra_percent

    def _set_uniform_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.uniform_allowance_percent = emp.uniform_allowance_percent

    def _set_children_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.children_edu_allowance_percent = emp.children_edu_allowance_percent

    def _set_helper_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.helper_allowance_percent = emp.helper_allowance_percent

    def _set_medical_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.medical_reimbursement_percent = emp.medical_reimbursement_percent

    def _set_transport_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.transport_allowance_percent = emp.transport_allowance_percent

    def _set_pf_emp_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.pf_employer_percent = emp.pf_employer_percent

    def _set_esi_emp_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.esi_employer_percent = emp.esi_employer_percent

    def _set_bonus_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.bonus_percent = emp.bonus_percent

    def _set_pf_ee_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.pf_employee_percent = emp.pf_employee_percent

    def _set_esi_ee_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.esi_employee_percent = emp.esi_employee_percent

    def _set_tds(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.tds = emp.tds

    def _set_tds_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.tds_percent = emp.tds_percent

    def _set_ltc_pct(self):
        for emp in self:
            if emp.version_id:
                emp.version_id.ltc_percent = emp.ltc_percent
