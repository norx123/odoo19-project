# -*- coding: utf-8 -*-
# Post-migration: clear ir.ui.view cache so new fields are visible


def migrate(cr, version):
    """Invalidate cached views so input_type_id field appears"""
    cr.execute("""
        UPDATE ir_ui_view SET write_date = NOW()
        WHERE model IN ('hr.payslip', 'hr.payslip.input')
    """)
