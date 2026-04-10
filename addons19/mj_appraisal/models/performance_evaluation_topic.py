from odoo import api, fields, models
from odoo.exceptions import AccessError

class PerformanceEvaluationTopic(models.Model):
    _name = 'performance.evaluation.topic'
    _description = 'Performance Evaluation Topic'

    name = fields.Char(required=True)
    description = fields.Text()
