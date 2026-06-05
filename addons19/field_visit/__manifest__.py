# -*- coding: utf-8 -*-
{
    'name': 'Field Visit Management',
    'version': '1.0.0',
    'category': 'Human Resources',
    'summary': 'Employee field visit tracking — meetings, shops, project sites and more',
    'author': 'Custom',
    'depends': ['hr', 'mail', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/visit_views.xml',
        'views/dashboard_action.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'field_visit/static/src/css/style.css',
            'field_visit/static/src/js/dashboard.js',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
