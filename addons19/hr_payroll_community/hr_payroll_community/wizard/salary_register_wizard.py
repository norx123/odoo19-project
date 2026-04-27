# -*- coding: utf-8 -*-
import io
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class SalaryRegisterWizard(models.TransientModel):
    """Wizard to generate Salary Register XLSX report"""
    _name = 'salary.register.wizard'
    _description = 'Salary Register Wizard'

    date_from = fields.Date(string='Start Date', required=True,
                             default=lambda self: fields.Date.today().replace(day=1))
    date_to = fields.Date(string='End Date', required=True,
                           default=fields.Date.today)
    salary_structure_id = fields.Many2one('hr.payroll.structure',
                                           string='Salary Structure')
    state_paid = fields.Boolean(string='Paid', default=True)
    state_done = fields.Boolean(string='Done', default=False)
    employee_ids = fields.Many2many(
        'hr.employee', string='Employees',
        help="Leave empty to include all employees")

    def _get_payslip_domain(self):
        states = []
        if self.state_paid:
            states.append('done')
        if self.state_done:
            states.append('done')
        if not states:
            states = ['done']
        domain = [
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('state', 'in', list(set(states))),
        ]
        if self.salary_structure_id:
            domain.append(('struct_id', '=', self.salary_structure_id.id))
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
        return domain

    def action_export_xlsx(self):
        if not xlsxwriter:
            raise UserError(_('xlsxwriter library is not installed. Please install it.'))

        payslips = self.env['hr.payslip'].search(self._get_payslip_domain())
        if not payslips:
            raise UserError(_('No payslips found for the selected criteria.'))

        # Collect all salary rule codes/names (columns)
        rule_map = {}  # code -> name
        for slip in payslips:
            for line in slip.line_ids.filtered(lambda l: l.appears_on_payslip):
                rule_map[line.code] = line.name

        rule_codes = sorted(rule_map.keys())

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Salary Register')

        # Formats
        header_fmt = workbook.add_format({
            'bold': True, 'bg_color': '#6c5fc7', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        data_fmt = workbook.add_format({'border': 1, 'align': 'left'})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'align': 'right'})
        total_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'num_format': '#,##0.00',
            'bg_color': '#e8e4ff', 'align': 'right'
        })

        # Title row
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter'
        })
        total_cols = 4 + len(rule_codes)
        worksheet.merge_range(0, 0, 0, total_cols - 1, 'SALARY REGISTER', title_fmt)
        period_fmt = workbook.add_format({'align': 'center', 'italic': True})
        worksheet.merge_range(1, 0, 1, total_cols - 1,
                               f'Period: {self.date_from} to {self.date_to}', period_fmt)

        # Header row
        row = 3
        headers = ['#', 'Employee', 'Department', 'Job Position'] + \
                  [f'{rule_map[c]}\n({c})' for c in rule_codes] + ['NET']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_fmt)
            worksheet.set_column(col, col, 18 if col > 1 else (5 if col == 0 else 25))

        # Group payslips by employee
        employee_data = {}
        for slip in payslips:
            emp_id = slip.employee_id.id
            if emp_id not in employee_data:
                employee_data[emp_id] = {
                    'name': slip.employee_id.name,
                    'dept': slip.employee_id.department_id.name or '',
                    'job': slip.employee_id.job_id.name or '',
                    'lines': {}
                }
            for line in slip.line_ids.filtered(lambda l: l.appears_on_payslip):
                employee_data[emp_id]['lines'][line.code] = \
                    employee_data[emp_id]['lines'].get(line.code, 0) + line.total

        row += 1
        col_totals = {code: 0 for code in rule_codes}
        col_totals['NET'] = 0

        for idx, (emp_id, data) in enumerate(employee_data.items(), start=1):
            worksheet.write(row, 0, idx, data_fmt)
            worksheet.write(row, 1, data['name'], data_fmt)
            worksheet.write(row, 2, data['dept'], data_fmt)
            worksheet.write(row, 3, data['job'], data_fmt)
            net = 0
            for col_idx, code in enumerate(rule_codes):
                amount = data['lines'].get(code, 0)
                worksheet.write(row, 4 + col_idx, amount, money_fmt)
                col_totals[code] += amount
                net += amount
            worksheet.write(row, 4 + len(rule_codes), net, money_fmt)
            col_totals['NET'] += net
            row += 1

        # Totals row
        worksheet.write(row, 0, 'TOTAL', header_fmt)
        worksheet.merge_range(row, 1, row, 3, '', header_fmt)
        for col_idx, code in enumerate(rule_codes):
            worksheet.write(row, 4 + col_idx, col_totals[code], total_fmt)
        worksheet.write(row, 4 + len(rule_codes), col_totals['NET'], total_fmt)

        workbook.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': f'Salary_Register_{self.date_from}_{self.date_to}.xlsx',
            'type': 'binary',
            'datas': xlsx_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
