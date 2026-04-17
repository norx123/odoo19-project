# -*- coding: utf-8 -*-
# Migration 19.0.1.0.3 — add input_type_id column (if missing from 1.0.2)
# and create hr_master_report tables


def migrate(cr, version):
    # Add input_type_id to hr_payslip_input if missing
    cr.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name='hr_payslip_input' AND column_name='input_type_id'
    """)
    if not cr.fetchone():
        cr.execute("""
            ALTER TABLE hr_payslip_input
            ADD COLUMN input_type_id INTEGER
            REFERENCES hr_payslip_other_input_type(id) ON DELETE SET NULL
        """)
