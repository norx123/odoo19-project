{
    'name': 'HR Salary Components',
    'version': '17.0.2.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Indian Payroll – CTC, Earnings, Employer Contribution & Deductions with per-version isolation',
    'description': """
        HR Salary Components v2
        ========================
        - All salary fields stored on hr.version (Contract Version) only
        - Employee form reads live from selected version → switching version shows that version's data
        - Annual CTC / Gross / Monthly fields per version
        - Earnings: Basic+DA (auto or manual), HRA, Uniform, Children Edu, Helper, Medical, Transport, Special
        - Employer: PF (12%, capped ₹15k), ESI (3.25%, if gross ≤ ₹21k), Bonus
        - Deductions: PF Employee (12%, capped ₹15k), ESI (0.75%, if gross ≤ ₹21k), TDS, Gratuity (4.81%)
        - Contract Templates form now shows full Salary Components tab
    """,
    'author': 'HRMS',
    'depends': ['hr', 'hr_contract'],
    'data': [
        'security/ir_model_access.csv',
        'views/hr_version_view.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
