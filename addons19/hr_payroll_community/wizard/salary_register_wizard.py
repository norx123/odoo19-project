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
    state_done = fields.Boolean(string='Done', default=True)
    employee_ids = fields.Many2many(
        'hr.employee', string='Employees',
        help="Leave empty to include all employees")

    def _get_payslip_domain(self):
        # Collect selected states — 'paid' and/or 'done'
        states = []
        if self.state_paid:
            states.append('paid')
        if self.state_done:
            states.append('done')
        if not states:
            states = ['done', 'paid']
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
            raise UserError(_(
                'No payslips found for the selected criteria.\n'
                'Make sure payslips are in "Done" or "Paid" state for the selected period.'))

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
            'bold': True, 'bg_color': '#4B3FA0', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        data_fmt = workbook.add_format({'border': 1, 'align': 'left', 'valign': 'vcenter'})
        money_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'align': 'right', 'valign': 'vcenter'})
        total_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'num_format': '#,##0.00',
            'bg_color': '#e8e4ff', 'align': 'right', 'valign': 'vcenter'
        })
        total_label_fmt = workbook.add_format({
            'bold': True, 'border': 1, 'bg_color': '#4B3FA0',
            'font_color': 'white', 'align': 'center', 'valign': 'vcenter'
        })
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter',
            'bg_color': '#4B3FA0', 'font_color': 'white'
        })
        sub_fmt = workbook.add_format({'align': 'center', 'italic': True, 'font_color': '#555555'})

        total_cols = 4 + len(rule_codes) + 1

        # Title
        worksheet.set_row(0, 28)
        worksheet.set_row(1, 16)
        worksheet.merge_range(0, 0, 0, total_cols - 1, 'SALARY REGISTER', title_fmt)
        worksheet.merge_range(1, 0, 1, total_cols - 1,
                               'Period: %s  to  %s' % (self.date_from, self.date_to), sub_fmt)

        # Header row
        row = 3
        worksheet.set_row(row, 36)
        headers = ['#', 'Employee', 'Department', 'Job Position'] + \
                  ['%s\n(%s)' % (rule_map[c], c) for c in rule_codes] + ['NET SALARY']
        col_widths = [5, 28, 20, 22] + [16] * len(rule_codes) + [16]
        for col_idx, (header, width) in enumerate(zip(headers, col_widths)):
            worksheet.write(row, col_idx, header, header_fmt)
            worksheet.set_column(col_idx, col_idx, width)

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
            worksheet.set_row(row, 18)
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
        worksheet.set_row(row, 20)
        worksheet.write(row, 0, '', total_label_fmt)
        worksheet.merge_range(row, 1, row, 3, 'TOTAL', total_label_fmt)
        for col_idx, code in enumerate(rule_codes):
            worksheet.write(row, 4 + col_idx, col_totals[code], total_fmt)
        worksheet.write(row, 4 + len(rule_codes), col_totals['NET'], total_fmt)

        worksheet.freeze_panes(4, 4)
        workbook.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())

        attachment = self.env['ir.attachment'].create({
            'name': 'Salary_Register_%s_%s.xlsx' % (self.date_from, self.date_to),
            'type': 'binary',
            'datas': xlsx_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % attachment.id,
            'target': 'self',
        }
