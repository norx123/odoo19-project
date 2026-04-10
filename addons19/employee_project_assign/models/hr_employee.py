from odoo import models, fields

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    project_ids = fields.One2many(
        'employee.project.line',
        'employee_id',
        string="Projects"
    )

class EmployeeProjectLine(models.Model):
    _name = 'employee.project.line'
    _description = 'Employee Project Line'

    employee_id = fields.Many2one('hr.employee')
    project_id = fields.Many2one('project.detail', string="Project")

    customer = fields.Char(related='project_id.customer', store=True)
    function = fields.Char(related='project_id.function', store=True)
