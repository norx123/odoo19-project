# -*- coding: utf-8 -*-
{
    'name': 'Custom Approval',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Approval Dashboard with Advance Salary, Loan, Resignation, Travel Request and Early Logout Gate Pass',
    'description': """
        Custom Approval Module for Odoo 19 Community
        =============================================
        Features:
        - Approval Dashboard with 5 categories
        - Advance Salary Request
        - Request for Loan
        - Employee Resignation
        - Travel Request
        - Early Logout Gate Pass (with downloadable PDF gate pass)
        - Multiple Approvers support for all forms
    """,
    'author': 'Krishn Dev',
    'depends': ['hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/approval_dashboard_views.xml',
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
            'custom_approval/static/src/css/approval_dashboard.css',
            'custom_approval/static/src/xml/approval_dashboard.xml',
            'custom_approval/static/src/js/approval_dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
