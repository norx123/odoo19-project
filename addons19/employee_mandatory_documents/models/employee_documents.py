from odoo import models, fields, api
import os


EXT_MAP = {
    'pdf':  'PDF',
    'jpg':  'JPEG',
    'jpeg': 'JPEG',
    'png':  'PNG',
    'doc':  'DOC',
    'docx': 'DOCX',
    'xls':  'Excel',
    'xlsx': 'Excel',
    'ppt':  'PPT',
    'pptx': 'PPTX',
    'txt':  'TXT',
    'csv':  'CSV',
    'zip':  'ZIP',
}


def _get_file_type(file_name):
    if not file_name:
        return ''
    ext = os.path.splitext(file_name)[1].lstrip('.').lower()
    return EXT_MAP.get(ext, ext.upper() if ext else '')


class EmployeeDocument(models.Model):
    _name = 'employee.document'
    _description = 'Employee Document'

    name = fields.Char(string="Document Name", required=True)
    description = fields.Char(string="Description")

    file = fields.Binary(string="Attachment", attachment=True)
    file_name = fields.Char(string="File Name")
    file_type = fields.Char(string="Document Type")

    employee_id = fields.Many2one('hr.employee', string="Employee")

    document_type = fields.Selection([
        ('onboarding', 'OnBoarding'),
        ('exit', 'Exit'),
        ('other', 'Others')
    ], default='other')

    @api.onchange('file_name')
    def _onchange_file_name(self):
        for rec in self:
            rec.file_type = _get_file_type(rec.file_name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            fn = vals.get('file_name', '')
            if fn:
                vals['file_type'] = _get_file_type(fn)
        return super().create(vals_list)

    def write(self, vals):
        fn = vals.get('file_name')
        if fn is not None:
            vals['file_type'] = _get_file_type(fn)
        return super().write(vals)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    onboarding_document_ids = fields.One2many(
        'employee.document', 'employee_id',
        domain=[('document_type', '=', 'onboarding')],
        context={'default_document_type': 'onboarding'}
    )
    exit_document_ids = fields.One2many(
        'employee.document', 'employee_id',
        domain=[('document_type', '=', 'exit')],
        context={'default_document_type': 'exit'}
    )
    other_document_ids = fields.One2many(
        'employee.document', 'employee_id',
        domain=[('document_type', '=', 'other')],
        context={'default_document_type': 'other'}
    )
