# -*- coding: utf-8 -*-
{
    'name': 'Employee Travel Expense (Local & Outstation)',
    'version': '19.0.2.0.0',
    'summary': 'Local & Outstation Travel Expense - Integrated with Expenses',
    'category': 'Human Resources',
    'author': 'Krishn Dev',
    'depends': ['hr_expense', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence_data.xml',
        'data/stage_data.xml',
        'views/vehicle_registration_views.xml',
        'views/travel_expense_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
