from odoo import api, fields, models, _
from odoo.tools import float_compare
from odoo.exceptions import AccessError, ValidationError, UserError

class PerformanceAppraiser(models.Model):
    _name = 'performance.appraiser'
    _description = 'Performance Appraiser'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    performance_appraisal_id = fields.Many2one(
        'performance.appraisal',
        ondelete='cascade',
        copy=False 
    )
    name = fields.Many2one(
        'hr.employee',
        related='performance_appraisal_id.employee_id',
        store=True,
        readonly=True,
        string="Appraisee",
        copy=False 
    )
    appraiser_id = fields.Many2one(
        'hr.employee',
        string="Allowed Appraisers",
        required=True
    )

    weightage = fields.Integer(
        default=1, max=100, min=1, tracking=True, string="Allocated Points (Σ=100)",
        help="The allocated points for this evaluation topic. Must be between 1 and 100. The total weightage across all topics should ideally sum up to 100."
    )

    # weightage = fields.Selection([(1, 1), (2, 2), (3, 3), (4, 4), (5, 5)], string="Priority", tracking=True, default=3)

    score = fields.Float(
        compute='_compute_appraiser_score',
        store=True,
        copy=False 
    )

    performance_appraiser_line_ids = fields.One2many(
        'performance.appraiser.line',
        'performance_appraiser_id',
        copy=False 
    )

    state = fields.Selection(
        related='performance_appraisal_id.state',
        store=True,
        tracking=True,
        copy=False
    )

    total_weightage = fields.Integer(
        compute='_compute_total_weightage',
        store=True
    )

    

    # -------------------------------------------------
    # COMPUTES
    # -------------------------------------------------
    @api.depends('performance_appraiser_line_ids.weightage')
    def _compute_total_weightage(self):
        for rec in self:
            rec.total_weightage = sum(
                rec.performance_appraiser_line_ids.mapped('weightage')
            )

    
    @api.constrains('performance_appraiser_line_ids', 'performance_appraiser_line_ids.weightage')
    def _check_total_weightage(self):
        for rec in self:
            if not rec.performance_appraiser_line_ids:
                continue

            total = sum(rec.performance_appraiser_line_ids.mapped('weightage'))
            if float_compare(total, 100.0, precision_digits=2) != 0:
                raise ValidationError(
                    _("Total allocated points must be 100. Current total: %s")
                    % total
                )

    @api.constrains('weightage')
    def _check_weightage_range(self):
        for rec in self:
            if rec.weightage < 1:
                raise ValidationError(
                    "Allocated point must be a positive number."
                )

    @api.depends('performance_appraiser_line_ids.score',
                 'performance_appraiser_line_ids.weightage', 'weightage')

    
    def _compute_appraiser_score(self):
        for rec in self:
            lines = rec.performance_appraiser_line_ids
            weighted_score = sum(l.score for l in lines)
            if not weighted_score:
                rec.score = 0.0
                continue

            rec.score = weighted_score * rec.weightage / 100

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})

        # ---- Step 1: copy main record (respecting copy=False automatically)
        new_appraisal = super().copy(default)

        # ---- Step 2: duplicate appraisers
        for appraiser in self.performance_appraiser_line_ids:
            new_appraiser = appraiser.copy({
                'performance_appraiser_id': new_appraisal.id,
            })
            
        return new_appraisal