# -*- coding: utf-8 -*-
import io
import base64
from odoo import api, fields, models, _
from odoo.exceptions import UserError

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None

MONTHS = [
    (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
    (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
    (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December'),
]

EPF_WAGE_CAP = 15000.0


class HrEpfReport(models.Model):
    """EPF Report - generates ECR-format XLSX and TXT for EPFO filing"""
    _name = 'hr.epf.report'
    _description = 'EPF Report'
    _order = 'year desc, month desc'

    name = fields.Char(string='Report Name', compute='_compute_name', store=True)
    year = fields.Integer(string='Year', required=True,
                          default=lambda self: fields.Date.today().year)
    month = fields.Selection([(str(m), n) for m, n in MONTHS],
                             string='Month', required=True,
                             default=lambda self: str(fields.Date.today().month))

    # Salary rule codes to use for EPF calculation
    # User must configure these to match their salary rules
    gross_rule_code = fields.Char(
        string='Gross Salary Rule Code',
        default='Monthy_Gross',
        help="Salary rule code for Monthly Gross (e.g. Monthy_Gross, GROSS). "
             "EPF wages = min(Gross, 15000)")
    epf_ee_rule_code = fields.Char(
        string='EPF Employee Rule Code',
        default='PF_EE',
        help="Salary rule code for Employee PF contribution (12%)")
    epf_er_rule_code = fields.Char(
        string='EPF Employer Rule Code',
        default='PF_ER',
        help="Salary rule code for Employer PF contribution")
    eps_rule_code = fields.Char(
        string='EPS Rule Code',
        default='EPS',
        help="Salary rule code for EPS (8.33% pension)")

    @api.depends('year', 'month')
    def _compute_name(self):
        for rec in self:
            month_name = dict(MONTHS).get(int(rec.month or 1), '')
            rec.name = '%s-%s' % (month_name, rec.year) if rec.year else 'EPF Report'

    def _get_payslip_lines_map(self, payslips):
        """Return {slip_id: {code: total}} from payslip lines"""
        result = {}
        for slip in payslips:
            result[slip.id] = {}
            for line in slip.line_ids.filtered(lambda l: l.appears_on_payslip):
                result[slip.id][line.code] = result[slip.id].get(line.code, 0.0) + line.total
        return result

    def _compute_epf_data(self):
        """Compute EPF data for all paid employees in selected month/year."""
        self.ensure_one()
        month_int = int(self.month)
        year_int = self.year

        # Date range for the selected month
        import calendar
        last_day = calendar.monthrange(year_int, month_int)[1]
        date_from = '%s-%02d-01' % (year_int, month_int)
        date_to = '%s-%02d-%02d' % (year_int, month_int, last_day)

        # Only PAID payslips
        domain = [
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', '=', 'paid'),
        ]
        payslips = self.env['hr.payslip'].search(domain)
        if not payslips:
            raise UserError(_(
                'No PAID payslips found for %s %s.\n'
                'Please make sure payslips are in "Paid" state.') % (
                dict(MONTHS)[month_int], year_int))

        lines_map = self._get_payslip_lines_map(payslips)

        rows = []
        # Group by employee (one row per employee)
        emp_slips = {}
        for slip in payslips:
            emp_id = slip.employee_id.id
            if emp_id not in emp_slips:
                emp_slips[emp_id] = []
            emp_slips[emp_id].append(slip)

        sno = 1
        for emp_id, slips in emp_slips.items():
            emp = slips[0].employee_id

            # Aggregate all payslip lines for this employee this month
            gross = 0.0
            epf_ee_from_rule = 0.0
            epf_er_from_rule = 0.0
            eps_from_rule = 0.0

            for slip in slips:
                lmap = lines_map.get(slip.id, {})
                gross += lmap.get(self.gross_rule_code, 0.0)
                epf_ee_from_rule += lmap.get(self.epf_ee_rule_code, 0.0)
                epf_er_from_rule += lmap.get(self.epf_er_rule_code, 0.0)
                eps_from_rule += lmap.get(self.eps_rule_code, 0.0)

            # EPF Wages = min(Gross, 15000)
            epf_wages = min(gross, EPF_WAGE_CAP) if gross > 0 else 0.0
            edli_wages = epf_wages  # same as EPF wages
            eps_wages = min(epf_wages, EPF_WAGE_CAP)  # EPS capped at 15000

            # If salary rules exist use them, else calculate
            epf_ee = abs(epf_ee_from_rule) if epf_ee_from_rule else round(epf_wages * 0.12)
            eps_er = abs(eps_from_rule) if eps_from_rule else round(eps_wages * 0.0833)
            epf_er = abs(epf_er_from_rule) if epf_er_from_rule else round(epf_ee - eps_er)

            rows.append({
                'sno': sno,
                'uan': emp.uan_number or '',
                'member_name': emp.name,
                'gross_wages': round(gross),
                'epf_wages': round(epf_wages),
                'eps_wages': round(eps_wages),
                'edli_wages': round(edli_wages),
                'epf_ee': round(epf_ee),
                'epf_er': round(epf_er),
                'eps_er': round(eps_er),
                'ncp_days': 0,
                'refund_adv': 0,
            })
            sno += 1

        return rows

    # ── XLSX Export ─────────────────────────────────────────────────────────

    def action_export_xlsx(self):
        if not xlsxwriter:
            raise UserError(_('xlsxwriter is not installed.'))

        rows = self._compute_epf_data()
        month_name = dict(MONTHS)[int(self.month)]

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = wb.add_worksheet('ECR_%s_%s' % (month_name[:3], self.year))

        # Formats
        title_fmt = wb.add_format({
            'bold': True, 'font_size': 13,
            'align': 'center', 'valign': 'vcenter',
            'bg_color': '#1F4E79', 'font_color': 'white'
        })
        sub_fmt = wb.add_format({
            'italic': True, 'align': 'center',
            'font_color': '#444444', 'font_size': 10
        })
        hdr_fmt = wb.add_format({
            'bold': True, 'bg_color': '#2E75B6', 'font_color': 'white',
            'border': 1, 'align': 'center', 'valign': 'vcenter',
            'text_wrap': True
        })
        data_fmt = wb.add_format({
            'border': 1, 'align': 'center', 'valign': 'vcenter'
        })
        name_fmt = wb.add_format({
            'border': 1, 'align': 'left', 'valign': 'vcenter'
        })
        num_fmt = wb.add_format({
            'border': 1, 'align': 'right', 'valign': 'vcenter',
            'num_format': '#,##0'
        })
        total_fmt = wb.add_format({
            'bold': True, 'bg_color': '#BDD7EE', 'border': 1,
            'align': 'right', 'valign': 'vcenter', 'num_format': '#,##0'
        })
        total_lbl = wb.add_format({
            'bold': True, 'bg_color': '#1F4E79', 'font_color': 'white',
            'border': 1, 'align': 'center'
        })

        COLS = [
            ('UAN', 14), ('Member_Name', 24), ('Gross_Wages', 12),
            ('EPF_Wages', 11), ('EPS_Wages', 11), ('EDLI_Wages', 11),
            ('EPF_EE', 10), ('EPF_ER', 10), ('EPS_ER', 10),
            ('NCP_Days', 10), ('Refund_Adv', 11),
        ]

        # Title rows
        ws.set_row(0, 26)
        ws.set_row(1, 16)
        ws.merge_range(0, 0, 0, len(COLS) - 1,
                       'EPF Report - %s %s' % (month_name, self.year), title_fmt)
        ws.merge_range(1, 0, 1, len(COLS) - 1,
                       'Electronic Challan cum Return (ECR)', sub_fmt)

        # Header row
        hdr_row = 3
        ws.set_row(hdr_row, 30)
        for col_idx, (col_name, col_w) in enumerate(COLS):
            ws.write(hdr_row, col_idx, col_name, hdr_fmt)
            ws.set_column(col_idx, col_idx, col_w)

        # Data rows
        data_row = hdr_row + 1
        totals = {k: 0 for k in ['gross_wages', 'epf_wages', 'eps_wages',
                                   'edli_wages', 'epf_ee', 'epf_er',
                                   'eps_er', 'ncp_days', 'refund_adv']}
        for r in rows:
            ws.set_row(data_row, 18)
            ws.write(data_row, 0, r['uan'], data_fmt)
            ws.write(data_row, 1, r['member_name'], name_fmt)
            ws.write(data_row, 2, r['gross_wages'], num_fmt)
            ws.write(data_row, 3, r['epf_wages'], num_fmt)
            ws.write(data_row, 4, r['eps_wages'], num_fmt)
            ws.write(data_row, 5, r['edli_wages'], num_fmt)
            ws.write(data_row, 6, r['epf_ee'], num_fmt)
            ws.write(data_row, 7, r['epf_er'], num_fmt)
            ws.write(data_row, 8, r['eps_er'], num_fmt)
            ws.write(data_row, 9, r['ncp_days'], data_fmt)
            ws.write(data_row, 10, r['refund_adv'], data_fmt)
            for k in totals:
                totals[k] += r[k]
            data_row += 1

        # Totals row
        ws.set_row(data_row, 20)
        ws.write(data_row, 0, '', total_lbl)
        ws.write(data_row, 1, 'Total=%d' % len(rows), total_lbl)
        ws.write(data_row, 2, totals['gross_wages'], total_fmt)
        ws.write(data_row, 3, totals['epf_wages'], total_fmt)
        ws.write(data_row, 4, totals['eps_wages'], total_fmt)
        ws.write(data_row, 5, totals['edli_wages'], total_fmt)
        ws.write(data_row, 6, totals['epf_ee'], total_fmt)
        ws.write(data_row, 7, totals['epf_er'], total_fmt)
        ws.write(data_row, 8, totals['eps_er'], total_fmt)
        ws.write(data_row, 9, totals['ncp_days'], total_fmt)
        ws.write(data_row, 10, totals['refund_adv'], total_fmt)

        ws.freeze_panes(hdr_row + 1, 2)
        wb.close()
        output.seek(0)
        xlsx_data = base64.b64encode(output.read())

        fname = 'EPF_ECR_%s_%s.xlsx' % (month_name[:3], self.year)
        att = self.env['ir.attachment'].create({
            'name': fname, 'type': 'binary', 'datas': xlsx_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % att.id,
            'target': 'self',
        }

    # ── TXT Export (ECR format for EPFO portal upload) ───────────────────────

    def action_export_txt(self):
        """Generate ECR text file for EPFO portal upload."""
        rows = self._compute_epf_data()
        month_name = dict(MONTHS)[int(self.month)]

        lines = []
        # ECR format: each field separated by #
        # Header line
        lines.append('#~#'.join([
            'UAN', 'MEMBER_NAME', 'GROSS_WAGES',
            'EPF_WAGES', 'EPS_WAGES', 'EDLI_WAGES',
            'EPF_CONTRI_REMITTED', 'EPF_ER_CONTRI_REMITTED',
            'EPS_CONTRI_REMITTED', 'NCP_DAYS', 'REFUND_OF_ADVANCES'
        ]))

        for r in rows:
            line = '#~#'.join([
                str(r['uan']),
                str(r['member_name']),
                str(r['gross_wages']),
                str(r['epf_wages']),
                str(r['eps_wages']),
                str(r['edli_wages']),
                str(r['epf_ee']),
                str(r['epf_er']),
                str(r['eps_er']),
                str(r['ncp_days']),
                str(r['refund_adv']),
            ])
            lines.append(line)

        txt_content = '\n'.join(lines)
        txt_data = base64.b64encode(txt_content.encode('utf-8'))

        fname = 'EPF_ECR_%s_%s.txt' % (month_name[:3], self.year)
        att = self.env['ir.attachment'].create({
            'name': fname, 'type': 'binary', 'datas': txt_data,
            'mimetype': 'text/plain',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % att.id,
            'target': 'self',
        }
