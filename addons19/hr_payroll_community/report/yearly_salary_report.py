# -*- coding: utf-8 -*-
from odoo import api, models


class YearlySalaryReport(models.AbstractModel):
    _name = 'report.hr_payroll_community.yearly_salary_report_template'
    _description = 'Yearly Salary by Employee Report'

    MONTHS = [
        (1, 'Jan'), (2, 'Feb'), (3, 'Mar'), (4, 'Apr'),
        (5, 'May'), (6, 'Jun'), (7, 'Jul'), (8, 'Aug'),
        (9, 'Sep'), (10, 'Oct'), (11, 'Nov'), (12, 'Dec'),
    ]

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        year = data.get('year', 2025)
        employee_ids = data.get('employee_ids', [])
        department_id = data.get('department_id', False)
        job_id = data.get('job_id', False)

        # Include both done AND paid payslips
        domain = [
            ('date_from', '>=', '%s-01-01' % year),
            ('date_to', '<=', '%s-12-31' % year),
            ('state', 'in', ['done', 'paid']),
        ]
        if employee_ids:
            domain.append(('employee_id', 'in', employee_ids))
        if department_id:
            domain.append(('employee_id.department_id', '=', department_id))
        if job_id:
            domain.append(('employee_id.job_id', '=', job_id))

        payslips = self.env['hr.payslip'].search(
            domain, order='employee_id, date_from')

        # Collect all rule codes/names (appears_on_payslip only)
        rule_map = {}  # code -> name
        for slip in payslips:
            for line in slip.line_ids.filtered(lambda l: l.appears_on_payslip):
                rule_map[line.code] = line.name
        rule_codes = sorted(rule_map.keys())

        # Build per-employee monthly data
        employee_data = {}
        for slip in payslips:
            emp = slip.employee_id
            if emp.id not in employee_data:
                employee_data[emp.id] = {
                    'employee': emp,
                    'monthly': {},   # month_num -> {code: amount}
                    'totals': {},    # code -> yearly_total
                }
            month_num = slip.date_from.month
            if month_num not in employee_data[emp.id]['monthly']:
                employee_data[emp.id]['monthly'][month_num] = {}
            for line in slip.line_ids.filtered(lambda l: l.appears_on_payslip):
                prev = employee_data[emp.id]['monthly'][month_num].get(line.code, 0)
                employee_data[emp.id]['monthly'][month_num][line.code] = prev + line.total
                prev_total = employee_data[emp.id]['totals'].get(line.code, 0)
                employee_data[emp.id]['totals'][line.code] = prev_total + line.total

        company = self.env.company

        return {
            'docs': list(employee_data.values()),
            'rule_codes': rule_codes,
            'rule_map': rule_map,
            'months': self.MONTHS,
            'year': year,
            'company': company,
        }
