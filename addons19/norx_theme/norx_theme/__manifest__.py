{
    'name': 'Norx ERP Theme',
    'version': '19.0.1.0.1',
    'category': 'Theme',
    'summary': 'Custom UI Theme for Odoo 18 Community',
    'author': 'Norx ERP',
    'license': 'LGPL-3',

    'depends': ['web'],

    'data': [
        'views/assets.xml',
        'views/auth_pages.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'norx_theme/static/src/css/norx_theme.css',
        ],
        'web.assets_frontend': [
            'norx_theme/static/src/css/norx_theme.css',
        ],
        'web.assets_common': [
            'norx_theme/static/src/css/norx_theme.css',
        ],
    },

    'installable': True,
    'application': False,
}
