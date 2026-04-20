# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class YearlySalaryWizard(models.TransientModel):
    """Wizard to generate Yearly Salary by Employee PDF report"""
    _name = 'yearly.salary.wizard'
    _description = 'Yearly Salary by Employee Wizard'

    year = fields.Integer(string='Year', required=True,
                           default=lambda self: fields.Date.today().year)
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    employee_ids = fields.Many2many(
        'hr.employee', string='Employees',
        help="Select employees. Leave empty to include all.")

    def action_print(self):
        # Include both 'done' and 'paid' payslips
        domain = [
            ('date_from', '>=', '%s-01-01' % self.year),
            ('date_to', '<=', '%s-12-31' % self.year),
            ('state', 'in', ['done', 'paid']),
        ]
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.department_id:
            domain.append(('employee_id.department_id', '=', self.department_id.id))
        if self.job_id:
            domain.append(('employee_id.job_id', '=', self.job_id.id))

        payslips = self.env['hr.payslip'].search(domain)
        if not payslips:
            raise UserError(_(
                'No payslips found for the selected criteria.\n'
                'Make sure payslips are in "Done" or "Paid" state for year %s.') % self.year)

        return self.env.ref(
            'hr_payroll_community.action_yearly_salary_report'
        ).report_action(self, data={
            'year': self.year,
            'employee_ids': self.employee_ids.ids,
            'department_id': self.department_id.id,
            'job_id': self.job_id.id,
        })
