# -*- coding: utf-8 -*-
import io
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


class HrMasterReport(models.Model):
    """Master Report - Employee-wise salary component report with rule filter.
    Stored model (not transient) so the form saves and shows Generate button."""
    _name = 'hr.master.report'
    _description = 'Payroll Master Report'
    _order = 'date_from desc'

    name = fields.Char(
        string='Report Name',
        compute='_compute_name',
        store=True)

    date_from = fields.Date(
        string='Date From',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1))

    date_to = fields.Date(
        string='Date To',
        required=True,
        default=fields.Date.today)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company)

    salary_rule_ids = fields.Many2many(
        'hr.salary.rule',
        'hr_master_report_rule_rel',
        'report_id',
        'rule_id',
        string='Restrict to Rules',
        help="Select specific salary rules/components to include. "
             "Leave empty to include all rules that appear on payslip.")

    @api.depends('date_from', 'date_to')
    def _compute_name(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                rec.name = _('Master Report from %s to %s') % (
                    rec.date_from, rec.date_to)
            else:
                rec.name = _('Master Report')

    def _get_report_data(self):
        """Collect all payslip lines for the period, grouped by employee."""
        self.ensure_one()

        # Get all done/paid payslips in the period
        domain = [
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to),
            ('state', 'in', ['done', 'paid']),
            ('company_id', '=', self.company_id.id),
        ]
        payslips = self.env['hr.payslip'].search(domain)

        if not payslips:
            raise UserError(
                _('No payslips found for the selected period.\n'
                  'Please make sure payslips are in "Done" or "Paid" state.'))

        # Determine which rules to show
        if self.salary_rule_ids:
            rule_ids_filter = self.salary_rule_ids.ids
        else:
            rule_ids_filter = None  # all rules that appear on payslip

        # Collect unique rules (ordered by sequence) across all payslips
        rule_map = {}   # rule_id -> {'name': ..., 'code': ..., 'sequence': ...}
        for slip in payslips:
            for line in slip.line_ids.filtered(lambda l: l.appears_on_payslip):
                if rule_ids_filter is None or line.salary_rule_id.id in rule_ids_filter:
                    if line.salary_rule_id.id not in rule_map:
                        rule_map[line.salary_rule_id.id] = {
                            'name': line.name,
                            'code': line.code,
                            'sequence': line.sequence,
                        }

        # Sort rules by sequence
        sorted_rules = sorted(rule_map.items(), key=lambda x: x[1]['sequence'])

        # Build employee data
        # employee_id -> { 'employee': ..., rule_id: total_amount, ... }
        emp_data = {}
        for slip in payslips:
            emp = slip.employee_id
            if emp.id not in emp_data:
                # Try to get joining date — Odoo 19 uses 'date_start' on hr.employee
                joining_date = False
                for field_name in ('date_start', 'joining_date', 'joining'):
                    if hasattr(emp, field_name):
                        joining_date = getattr(emp, field_name, False)
                        break
                emp_data[emp.id] = {
                    'employee': emp,
                    'name': emp.name,
                    'joining_date': joining_date,
                    'department': emp.department_id.name or '',
                    'job': emp.job_id.name or '',
                    'amounts': {},
                }
            for line in slip.line_ids.filtered(lambda l: l.appears_on_payslip):
                if rule_ids_filter is None or line.salary_rule_id.id in rule_ids_filter:
                    prev = emp_data[emp.id]['amounts'].get(line.salary_rule_id.id, 0.0)
                    emp_data[emp.id]['amounts'][line.salary_rule_id.id] = prev + line.total

        # Sort employees by name
        sorted_employees = sorted(emp_data.values(), key=lambda x: x['name'])

        return sorted_rules, sorted_employees

    def action_generate_xlsx(self):
        """Generate and download the Master Report XLSX."""
        if not xlsxwriter:
            raise UserError(
                _('xlsxwriter library is not installed. '
                  'Run: pip install xlsxwriter'))

        sorted_rules, sorted_employees = self._get_report_data()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Master Report')

        # ── Formats ────────────────────────────────────────────────────────
        title_fmt = workbook.add_format({
            'bold': True, 'font_size': 14,
            'align': 'center', 'valign': 'vcenter',
            'font_color': '#FFFFFF', 'bg_color': '#4B3FA0',
        })
        subtitle_fmt = workbook.add_format({
            'italic': True, 'font_size': 10,
            'align': 'center', 'valign': 'vcenter',
            'font_color': '#555555',
        })
        header_fixed_fmt = workbook.add_format({
            'bold': True, 'font_size': 10,
            'align': 'center', 'valign': 'vcenter',
            'bg_color': '#4B3FA0', 'font_color': '#FFFFFF',
            'border': 1, 'text_wrap': True,
        })
        header_rule_fmt = workbook.add_format({
            'bold': True, 'font_size': 10,
            'align': 'center', 'valign': 'vcenter',
            'bg_color': '#7B6FCF', 'font_color': '#FFFFFF',
            'border': 1, 'text_wrap': True,
        })
        header_total_fmt = workbook.add_format({
            'bold': True, 'font_size': 10,
            'align': 'center', 'valign': 'vcenter',
            'bg_color': '#2E1F7A', 'font_color': '#FFFFFF',
            'border': 1,
        })
        data_fmt = workbook.add_format({
            'font_size': 10, 'align': 'left',
            'valign': 'vcenter', 'border': 1,
        })
        data_center_fmt = workbook.add_format({
            'font_size': 10, 'align': 'center',
            'valign': 'vcenter', 'border': 1,
        })
        money_fmt = workbook.add_format({
            'font_size': 10, 'align': 'right',
            'valign': 'vcenter', 'border': 1,
            'num_format': '#,##0.00',
        })
        money_neg_fmt = workbook.add_format({
            'font_size': 10, 'align': 'right',
            'valign': 'vcenter', 'border': 1,
            'num_format': '#,##0.00',
            'font_color': '#CC0000',
        })
        total_row_fmt = workbook.add_format({
            'bold': True, 'font_size': 10,
            'align': 'right', 'valign': 'vcenter',
            'bg_color': '#E8E4FF', 'border': 1,
            'num_format': '#,##0.00',
        })
        total_label_fmt = workbook.add_format({
            'bold': True, 'font_size': 10,
            'align': 'center', 'valign': 'vcenter',
            'bg_color': '#4B3FA0', 'font_color': '#FFFFFF',
            'border': 1,
        })
        sno_fmt = workbook.add_format({
            'font_size': 10, 'align': 'center',
            'valign': 'vcenter', 'border': 1,
        })

        # ── Fixed columns ──────────────────────────────────────────────────
        FIXED_COLS = ['S.No', 'Employee Name', 'Joining Date', 'Department', 'Designation']
        total_cols = len(FIXED_COLS) + len(sorted_rules) + 1  # +1 for NET

        # ── Title rows ─────────────────────────────────────────────────────
        worksheet.set_row(0, 28)
        worksheet.set_row(1, 18)
        worksheet.set_row(2, 18)
        worksheet.set_row(3, 14)

        worksheet.merge_range(0, 0, 0, total_cols - 1,
                               self.company_id.name or 'Master Salary Report',
                               title_fmt)
        worksheet.merge_range(1, 0, 1, total_cols - 1,
                               'MASTER SALARY REPORT', subtitle_fmt)
        worksheet.merge_range(2, 0, 2, total_cols - 1,
                               'Period: %s  to  %s' % (self.date_from, self.date_to),
                               subtitle_fmt)

        # ── Header row ─────────────────────────────────────────────────────
        header_row = 4
        worksheet.set_row(header_row, 36)

        # Fixed headers
        col_widths = [5, 28, 14, 20, 22]
        for col_idx, (header, width) in enumerate(zip(FIXED_COLS, col_widths)):
            worksheet.write(header_row, col_idx, header, header_fixed_fmt)
            worksheet.set_column(col_idx, col_idx, width)

        # Rule headers
        col = len(FIXED_COLS)
        for rule_id, rule_info in sorted_rules:
            header_text = '%s\n(%s)' % (rule_info['name'], rule_info['code'])
            worksheet.write(header_row, col, header_text, header_rule_fmt)
            worksheet.set_column(col, col, 16)
            col += 1

        # NET total header
        worksheet.write(header_row, col, 'NET\nSALARY', header_total_fmt)
        worksheet.set_column(col, col, 16)

        # ── Data rows ──────────────────────────────────────────────────────
        row = header_row + 1
        col_totals = {rule_id: 0.0 for rule_id, _ in sorted_rules}
        col_totals['NET'] = 0.0

        for sno, emp in enumerate(sorted_employees, start=1):
            worksheet.set_row(row, 18)

            # Joining date formatting
            joining = ''
            if emp.get('joining_date'):
                joining = str(emp['joining_date'])

            worksheet.write(row, 0, sno, sno_fmt)
            worksheet.write(row, 1, emp['name'], data_fmt)
            worksheet.write(row, 2, joining, data_center_fmt)
            worksheet.write(row, 3, emp['department'], data_fmt)
            worksheet.write(row, 4, emp['job'], data_fmt)

            col = len(FIXED_COLS)
            net = 0.0
            for rule_id, rule_info in sorted_rules:
                amount = emp['amounts'].get(rule_id, 0.0)
                fmt = money_neg_fmt if amount < 0 else money_fmt
                worksheet.write(row, col, amount, fmt)
                col_totals[rule_id] += amount
                net += amount
                col += 1

            # NET
            net_fmt = money_neg_fmt if net < 0 else money_fmt
            worksheet.write(row, col, net, net_fmt)
            col_totals['NET'] += net

            row += 1

        # ── Totals row ─────────────────────────────────────────────────────
        worksheet.set_row(row, 20)
        worksheet.write(row, 0, '', total_label_fmt)
        worksheet.merge_range(row, 1, row, len(FIXED_COLS) - 1, 'TOTAL', total_label_fmt)

        col = len(FIXED_COLS)
        for rule_id, _ in sorted_rules:
            worksheet.write(row, col, col_totals[rule_id], total_row_fmt)
            col += 1
        worksheet.write(row, col, col_totals['NET'], total_row_fmt)

        # ── Freeze panes (header + fixed cols) ─────────────────────────────
        worksheet.freeze_panes(header_row + 1, len(FIXED_COLS))

        workbook.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())

        filename = 'Master_Report_%s_%s.xlsx' % (self.date_from, self.date_to)
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': xlsx_data,
            'mimetype': (
                'application/vnd.openxmlformats-officedocument'
                '.spreadsheetml.sheet'),
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % attachment.id,
            'target': 'self',
        }
