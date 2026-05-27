# -*- coding: utf-8 -*-
{
    'name': 'Early Logout Gate Pass',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Employee Early Logout Gate Pass with PDF download and approver workflow',
    'description': """
        Early Logout Gate Pass Module for Odoo 19 Community
        ===================================================
        Features:
        - Employee selects request, manager auto-fills
        - Date, Login (Check-in) time, Logout (Check-out) time
        - Reason and multi-approver workflow
        - Downloadable PDF Gate Pass after approval
          with Employee Name, Employee Code, Manager,
          Date, Check-In & Check-Out times and Signature blocks
    """,
    'author': 'Krishn Dev',
    'depends': ['hr', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/early_gate_pass_views.xml',
        'views/early_gate_pass_report.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
