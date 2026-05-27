# -*- coding: utf-8 -*-
{
    'name': 'Approvals',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Approvals Dashboard - Advance Salary, Loan, Resignation, Travel Request and Early Logout Gate Pass',
    'description': """
        Approvals Module for Odoo 19 Community
        ======================================
        Features:
        - Approvals Dashboard with 5 categories
        - Advance Salary Request
        - Request for Loan
        - Employee Resignation
        - Travel Request
        - Early Logout Gate Pass (downloadable A6 size PDF)
        - Multiple Approvers support for all forms
    """,
    'author': 'Krishn Dev',
    'depends': ['hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/approvals_dashboard_views.xml',
        'views/advance_salary_views.xml',
        'views/loan_request_views.xml',
        'views/resignation_views.xml',
        'views/travel_request_views.xml',
        'views/early_gate_pass_views.xml',
        'views/early_gate_pass_report.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'approvals/static/src/css/approvals_dashboard.css',
            'approvals/static/src/js/approvals_dashboard.js',
            'approvals/static/src/xml/approvals_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
