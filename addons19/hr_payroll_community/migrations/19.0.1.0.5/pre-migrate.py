# -*- coding: utf-8 -*-
# Migration 19.0.1.0.5
# Add verify/done/paid states to hr_payslip_run
# Drop old CHECK constraints so new state values are accepted


def migrate(cr, version):
    # Drop CHECK constraints on hr_payslip_run.state
    cr.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'hr_payslip_run'
        AND constraint_type = 'CHECK'
    """)
    for (cname,) in cr.fetchall():
        cr.execute(
            "ALTER TABLE hr_payslip_run DROP CONSTRAINT IF EXISTS \"%s\"" % cname)

    # Drop CHECK constraints on hr_payslip.state (for paid state from earlier)
    cr.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'hr_payslip'
        AND constraint_type = 'CHECK'
    """)
    for (cname,) in cr.fetchall():
        cr.execute(
            "ALTER TABLE hr_payslip DROP CONSTRAINT IF EXISTS \"%s\"" % cname)

    # Add input_type_id column if still missing
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
