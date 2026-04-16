
from odoo import models, fields, api

class EmployeeTaxSheetLine(models.Model):
    _name = 'employee.tax.sheet.line'
    _description = 'Employee Tax Sheet Line'

    employee_id = fields.Many2one('hr.employee')
    component_name = fields.Selection([
        ('basic', 'Basic Pay'),
        ('hra', 'HRA'),
        ('special', 'Special Allowance'),
        ('project', 'Project Allowance'),
        ('reimbursement', 'Reimbursement'),
    ])

    april = fields.Float()
    may = fields.Float()
    june = fields.Float()
    july = fields.Float()
    august = fields.Float()
    september = fields.Float()
    october = fields.Float()
    november = fields.Float()
    december = fields.Float()
    january = fields.Float()
    february = fields.Float()
    march = fields.Float()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tax_sheet_line_ids = fields.One2many(
        'employee.tax.sheet.line',
        'employee_id',
        string="Tax Sheet Lines"
    )

    total_salary = fields.Float(compute="_compute_total")

    @api.depends('tax_sheet_line_ids')
    def _compute_total(self):
        for rec in self:
            total = 0
            for line in rec.tax_sheet_line_ids:
                total += sum([
                    line.april, line.may, line.june, line.july,
                    line.august, line.september, line.october,
                    line.november, line.december, line.january,
                    line.february, line.march
                ])
            rec.total_salary = total
