{
    "name": "HR Sign Work",
    "version": "19.0.1.0.0",
    "summary": "Employee Document Signing Module",
    "description": """
Custom PDF Sign Module
- PDF Preview
- Drag & Drop Sign Fields
- Sign Requests
- Dynamic Field Placement
- Signature Fields Configuration (Settings / Fields / Tags)
- Odoo 19 Compatible
- No Enterprise Dependency
""",
    "category": "Human Resources",
    "author": "Custom Development",
    "website": "",
    "license": "LGPL-3",

    # =====================================================
    # DEPENDENCIES
    # =====================================================

    "depends": [
        "base",
        "web",
        "mail",
        "hr",
    ],

    # =====================================================
    # DATA FILES
    # =====================================================

    "data": [
        "security/ir.model.access.csv",

        "views/sign_template_views.xml",
        "views/sign_request_views.xml",
        "views/sign_item_views.xml",
        "views/sign_item_type_views.xml",
        "views/sign_settings_views.xml",
        "views/sign_wizard_views.xml",
        "views/sign_doc_views.xml",
        "views/menu.xml",

        "data/sign_item_type_data.xml",
    ],

    # =====================================================
    # ASSETS
    # =====================================================

    "assets": {
        "web.assets_backend": [
            "hr_sign_work/static/src/css/sign.css",
            "hr_sign_work/static/src/js/sign_editor.js",
            "hr_sign_work/static/src/js/sign_doc.js",
        ],
    },

    # =====================================================
    # MODULE FLAGS
    # =====================================================

    "installable": True,
    "application": True,
    "auto_install": False,
}