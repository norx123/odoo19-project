{
    "name": "Custom Sign",
    "version": "19.0.1.0.0",
    "summary": "PDF Sign Templates, Requests, and Docs (no Enterprise required)",
    "description": """
Custom Sign - PDF Signing Module for Odoo 19 Community
------------------------------------------------------
* PDF Preview with drag-and-drop sign fields
* Field types: Signature, Initials, Name, Email, Phone, Company,
  Text, Multiline, Checkbox, Radio, Selection, Date, Stamp, Strikethrough
* Sign Requests with multiple signers
* Online signing UI - fill the placed fields, sign with mouse/touch
* Signed PDF generation (fields are stamped onto the original PDF)
* Download signed PDF
* Document editor (custom.sign.doc) - lightweight Google-Docs-like editor
* No Enterprise dependency
""",
    "category": "Human Resources",
    "author": "Custom Development",
    "website": "",
    "license": "LGPL-3",

    "depends": [
        "base",
        "web",
        "mail",
        "hr",
    ],

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

    "assets": {
        "web.assets_backend": [
            "custom_sign/static/src/css/sign.css",
            "custom_sign/static/src/js/sign_editor.js",
            "custom_sign/static/src/js/sign_doc.js",
        ],
    },

    "external_dependencies": {
        "python": ["PyPDF2", "reportlab"],
    },

    "installable": True,
    "application": True,
    "auto_install": False,
}
