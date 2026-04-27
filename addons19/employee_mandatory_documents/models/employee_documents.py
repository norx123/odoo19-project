from odoo import models, fields


class EmployeeDocument(models.Model):
    _name = 'employee.document'
    _description = 'Employee Document'

    name = fields.Char(string="Document Name", required=True)
    description = fields.Char(string="Description")

    file = fields.Binary(string="Attachment", attachment=True)
    file_name = fields.Char(string="File Name")

    employee_id = fields.Many2one('hr.employee', string="Employee")

    document_type = fields.Selection([
        ('onboarding', 'OnBoarding'),
        ('exit', 'Exit'),
        ('other', 'Others')
    ], default='other')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    onboarding_document_ids = fields.One2many(
        'employee.document',
        'employee_id',
        domain=[('document_type', '=', 'onboarding')],
        context={'default_document_type': 'onboarding'}
    )

    exit_document_ids = fields.One2many(
        'employee.document',
        'employee_id',
        domain=[('document_type', '=', 'exit')],
        context={'default_document_type': 'exit'}
    )

    other_document_ids = fields.One2many(
        'employee.document',
        'employee_id',
        domain=[('document_type', '=', 'other')],
        context={'default_document_type': 'other'}
    )