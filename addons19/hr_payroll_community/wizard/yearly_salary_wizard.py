# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class YearlySalaryWizard(models.TransientModel):
    """Wizard to generate Yearly Salary by Employee PDF report"""
    _name = 'yearly.salary.wizard'
    _description = 'Yearly Salary by Employee Wizard'

    year = fields.Integer(string='Year', required=True,
                           default=lambda self: fields.Date.today().year - 1)
    department_id = fields.Many2one('hr.department', string='Department')
    job_id = fields.Many2one('hr.job', string='Job Position')
    employee_ids = fields.Many2many(
        'hr.employee', string='Employees',
        help="Select employees. Leave empty to include all employees with paid payslips in the year.")

    def action_print(self):
        domain = [
            ('date_from', '>=', f'{self.year}-01-01'),
            ('date_to', '<=', f'{self.year}-12-31'),
            ('state', '=', 'done'),
        ]
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        if self.department_id:
            domain.append(('employee_id.department_id', '=', self.department_id.id))
        if self.job_id:
            domain.append(('employee_id.job_id', '=', self.job_id.id))

        payslips = self.env['hr.payslip'].search(domain)
        if not payslips:
            raise UserError(_('No paid payslips found for the selected criteria.'))

        return self.env.ref(
            'hr_payroll_community.action_yearly_salary_report'
        ).report_action(self, data={
            'year': self.year,
            'employee_ids': self.employee_ids.ids,
            'department_id': self.department_id.id,
            'job_id': self.job_id.id,
        })
