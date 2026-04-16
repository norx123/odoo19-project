{
    'name': 'Employee Salary Components (HR Version)',
    'version': '1.0.0',
    'summary': 'Add detailed salary component fields with percentage-based calculation to HR Employee',
    'description': """
        This module adds a 'Salary Components' tab to the Employee form with:
        - Annual CTC, Monthly CTC, Annual Gross, Monthly Gross
        - Earnings: Basic, HRA, Uniform Allowance, Children Education Allowance,
          Helper Allowance, Medical Reimbursement, Transport Allowance, Special Allowance, Gross Salary
        - Employer Contribution: PF Employer, ESI Employer, LTC, Bonus
        - Deductions: PF Employee, ESI Employee, TDS

        All components support percentage-based auto-calculation from Monthly CTC.
    """,
    'author': 'Custom',
    'category': 'Human Resources',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_version_view.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
