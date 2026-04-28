{
    'name': 'Employee Work History',
    'version': '19.0.1.0.0',
    'summary': 'Manage Employee Work History',
    'category': 'Human Resources',
    'author': 'Krishn Dev',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/education_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
