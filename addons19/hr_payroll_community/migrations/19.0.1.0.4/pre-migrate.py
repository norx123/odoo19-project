# -*- coding: utf-8 -*-
# Migration 19.0.1.0.4 — add 'paid' to hr_payslip state selection
# PostgreSQL CHECK constraint update for the new state value


def migrate(cr, version):
    # Drop old check constraint on state if exists, so 'paid' value is accepted
    cr.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'hr_payslip'
        AND constraint_type = 'CHECK'
        AND constraint_name LIKE '%state%'
    """)
    for row in cr.fetchall():
        cr.execute("ALTER TABLE hr_payslip DROP CONSTRAINT IF EXISTS %s" % row[0])

    # Also add input_type_id if not done yet (from earlier migrations)
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
