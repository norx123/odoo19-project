{
    'name': 'Employee Bonus Calculator',
    'version': '1.0',
    'summary': 'Bonus calculation based on Indian Bonus Act',
    'category': 'HR',
    'author': 'Custom',
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/bonus_calculator_views.xml',
    ],
    'installable': True,
    'application': True,
}