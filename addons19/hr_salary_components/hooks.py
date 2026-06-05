from odoo import api, SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)

SALARY_ARCH = """<data>
<xpath expr="//sheet" position="inside">

    <group string="Annual CTC">
        <group>
            <field name="annual_ctc" readonly="1"/>
            <field name="monthly_ctc" readonly="1"/>
        </group>
        <group>
            <field name="annual_gross" readonly="1"/>
            <field name="monthly_gross"/>
        </group>
    </group>

    <group>
        <field name="manual_basic"/>
        <field name="esi_enable"/>
    </group>

    <group string="Earnings" col="6">
        <!-- BASIC + DA: Manual ON → editable; Manual OFF → computed readonly -->
        <field name="basic" colspan="2" readonly="not manual_basic"/>
        <span>/ month</span>
        <field name="manual_basic" nolabel="1" invisible="1"/>
        <field name="basic_percent" nolabel="1" invisible="manual_basic" readonly="manual_basic"/>
        <span invisible="manual_basic">%</span>

        <!-- HRA: Manual ON → editable; Manual OFF → computed readonly -->
        <field name="hra" colspan="2" readonly="not manual_basic"/>
        <span>/ month</span>
        <field name="hra_percent" nolabel="1" invisible="manual_basic" readonly="manual_basic"/>
        <span invisible="manual_basic">%</span>

        <field name="uniform_allowance" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="uniform_allowance_percent" nolabel="1"/>
        <span>%</span>

        <field name="children_edu_allowance" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="children_edu_allowance_percent" nolabel="1"/>
        <span>%</span>

        <field name="helper_allowance" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="helper_allowance_percent" nolabel="1"/>
        <span>%</span>

        <field name="medical_reimbursement" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="medical_reimbursement_percent" nolabel="1"/>
        <span>%</span>

        <field name="transport_allowance" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="transport_allowance_percent" nolabel="1"/>
        <span>%</span>

        <field name="bonus" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="bonus_percent" nolabel="1"/>
        <span>%</span>

        <field name="special_allowance" colspan="2" readonly="1"/>
        <span>/ month</span>
        <span colspan="6"/>
    </group>

    <group string="Employer Contribution" col="6">
        <field name="pf_employer" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="pf_employer_percent"/>
        <span>%</span>

        <field name="esi_employer" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="esi_employer_percent"/>
        <span>%</span>

        <field name="gratuity" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="gratuity_percent"/>
        <span>%</span>

        <field name="edli_pf_admin" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="edli_pf_admin_percent"/>
        <span>%</span>
    </group>

    <group string="Deductions" col="6">
        <field name="pf_employee" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="pf_employee_percent"/>
        <span>%</span>

        <field name="esi_employee" colspan="2" readonly="1"/>
        <span>/ month</span>
        <field name="esi_employee_percent"/>
        <span>%</span>

        <field name="tds" colspan="2"/>
        <span>/ month</span>
        <field name="tds_percent"/>
        <span>%</span>
    </group>

</xpath>
</data>"""


def _inject_version_view(env):
    IrUiView = env['ir.ui.view']

    # Find ALL form views for hr.version (primary ones)
    primary_views = IrUiView.search([
        ('model', '=', 'hr.version'),
        ('type', '=', 'form'),
        ('mode', '=', 'primary'),
    ], order='priority asc')

    if not primary_views:
        _logger.warning('hr_salary_components: No primary form view found for hr.version')
        return

    parent_view = primary_views[0]
    _logger.info('hr_salary_components: Injecting salary fields into view id=%s name=%s',
                 parent_view.id, parent_view.name)

    # Remove any existing injection
    existing = IrUiView.search([
        ('name', '=', 'hr.version.salary.inject'),
        ('model', '=', 'hr.version'),
    ])
    if existing:
        existing.unlink()

    # Create fresh injection
    IrUiView.create({
        'name':       'hr.version.salary.inject',
        'model':      'hr.version',
        'type':       'form',
        'mode':       'extension',
        'inherit_id': parent_view.id,
        'arch':       SALARY_ARCH,
        'priority':   16,
        'active':     True,
    })
    _logger.info('hr_salary_components: Salary fields successfully injected into hr.version form')


def post_init_hook(env):
    _inject_version_view(env)


def post_migrate_hook(env):
    _inject_version_view(env)
