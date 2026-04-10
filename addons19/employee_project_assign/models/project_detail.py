from odoo import models, fields

class ProjectDetail(models.Model):
    _name = 'project.detail'
    _description = 'Project Detail'

    name = fields.Char(string="Project Name", required=True)
    customer = fields.Char(string="Customer")
    function = fields.Char(string="Function")
