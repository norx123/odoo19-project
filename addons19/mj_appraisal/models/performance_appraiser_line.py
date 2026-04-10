from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError, UserError

class PerformanceAppraiserLine(models.Model):
    _name = 'performance.appraiser.line'
    _description = 'Performance Appraiser Line'

    name = fields.Many2one(
        'performance.evaluation.topic',
        string="Evaluation Line (task / goal)",
        required=True
    )

    performance_appraiser_id = fields.Many2one(
        'performance.appraiser',
        ondelete='cascade',
        copy=False
    )

    score = fields.Integer(
        required=True, tracking=True, string="Obtained Score", default=1,
        help="The score obtained for this evaluation topic. Must be less than or equal to the allocated points.",
        copy=False 
    )

    weightage = fields.Integer(
        default=1, max=100, min=1, tracking=True, string="Allocated Points (Σ=100)",
        help="The allocated points for this evaluation topic. Must be between 1 and 100. The total weightage across all topics should ideally sum up to 100."
    )
    
    @api.constrains('weightage', 'score')
    def _check_weightage_range(self):
        for rec in self:
            if rec.weightage < 1:
                raise ValidationError(
                    "Allocated points must be a positive number."
                )

            if rec.score < 1:
                raise ValidationError(
                    "Obtained score must be a positive number."
                )

            if rec.score > rec.weightage:
                raise ValidationError(
                    "Obtained score cannot exceed allocated points."
                )
