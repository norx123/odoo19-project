from odoo import models, fields

class SalaryAttachment(models.Model):
    _name = 'hr.salary.attachment'
    _description = 'Salary Attachment'

    employee_id = fields.Many2one('hr.employee', required=True)
    description = fields.Char(required=True)

    type = fields.Selection([
        ('loan', 'Loan'),
        ('attachment', 'Attachment'),
        ('bonus', 'Bonus')
    ], required=True)

    payslip_amount = fields.Float()
    total_amount = fields.Float()

    start_date = fields.Date()
    end_date = fields.Date()

    negative_value = fields.Boolean(string="Negative Value")
    occurrences = fields.Integer(string="Occurrences")
    no_end_date = fields.Boolean(string="No End Date")

    document = fields.Binary(string="Document")
    document_name = fields.Char(string="File Name")

    state = fields.Selection([
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='running')

    # ✅ ADD THIS (IMPORTANT)
    payslip_ids = fields.One2many(
        'hr.payslip',          # target model
        'salary_attachment_id',  # field in hr.payslip
        string="Payslips"
    )

    def mark_as_completed(self):
        for rec in self:
            rec.state = 'completed'

    def cancel(self):
        for rec in self:
            rec.state = 'cancelled'