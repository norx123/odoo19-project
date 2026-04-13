{
    'name': 'Employee EPF & ESIC Details',
    'version': '1.0',
    'summary': 'Add EPF & ESIC fields in Employee Personal Tab',
    'description': 'Adds PF, UAN, ESIC, PAN fields in Personal tab of Employee form',
    'category': 'Human Resources',
    'author': 'Custom',
    'depends': ['hr'],
    'data': [
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'application': False,
}