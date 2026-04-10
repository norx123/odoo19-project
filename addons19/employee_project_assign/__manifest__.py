{
    'name': 'Employee Project Assign',
    'version': '1.0',
    'depends': ['hr'],
    'author': 'Custom',
    'category': 'HR',
    'summary': 'Assign Projects to Employees',
    'data': [
        'security/ir.model.access.csv',
        'views/project_detail_views.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': True,
}