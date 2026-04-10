from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError, UserError
from odoo.tools import float_compare


class PerformanceAppraisal(models.Model):
    _name = 'performance.appraisal'
    _description = 'Performance Appraisal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _order = 'sequence asc, appraisal_date desc'
    _order = 'appraisal_date desc'

    name = fields.Char(required=True, tracking=True, string="Appraisal Name")
    employee_id = fields.Many2one(
        'hr.employee', tracking=True, copy=False 
    )

    # sequence = fields.Integer(related='employee_id.sequence', store=True)

    date_from = fields.Date(
        string="Evaluation Start Date", required=True
    )
    date_to = fields.Date(
        string="Evaluation End Date", required=True
    )

    appraisal_date = fields.Date(
        default=fields.Date.context_today, tracking=True
    )

    performance_appraiser_ids = fields.One2many(
        'performance.appraiser',
        'performance_appraisal_id',
        string="Appraisers", copy=False 
    )

    appraiser_count = fields.Integer(
        compute='_compute_appraiser_count'
    )

    score = fields.Float(
        compute='_compute_appraisal_score',
        store=True
    )

    total_weightage = fields.Integer(
        compute='_compute_total_weightage',
        store=True
    )

    comments = fields.Text()

    state = fields.Selection(
        [('draft', 'Draft'), ('submitted', 'Submitted'), ('confirmed', 'Confirmed')],
        default='draft',
        tracking=True, copy=False
    )

    # -------------------------------------------------
    # COMPUTES
    # -------------------------------------------------

    @api.depends('performance_appraiser_ids.weightage')
    def _compute_total_weightage(self):
        for rec in self:
            rec.total_weightage = sum(
                rec.performance_appraiser_ids.mapped('weightage')
            )

    @api.depends('performance_appraiser_ids.score',
                 'performance_appraiser_ids.weightage')

        
    def _compute_appraisal_score(self):
        for appraisal in self:
            weighted_score = sum(
                appraisal.performance_appraiser_ids.mapped('score')
            )
            if not weighted_score:
                appraisal.score = 0.0
                continue

            appraisal.score = weighted_score

    def _compute_appraiser_count(self):
        for rec in self:
            rec.appraiser_count = len(rec.performance_appraiser_ids)

    
    @api.constrains('performance_appraiser_ids', 'performance_appraiser_ids.weightage')
    def _check_total_weightage(self):
        for rec in self:
            if not rec.performance_appraiser_ids:
                continue

            total = sum(rec.performance_appraiser_ids.mapped('weightage'))
            if float_compare(total, 100.0, precision_digits=2) != 0:
                raise ValidationError(
                    _("Total allocated points must be 100. Current total: %s")
                    % total
                )
    
    
    # -------------------------------------------------
    # ACTIONS
    # -------------------------------------------------

    def action_open_appraisers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Appraisers',
            'res_model': 'performance.appraiser',
            'view_mode': 'list,form',
            'domain': [('performance_appraisal_id', '=', self.id)],
            'context': {'default_performance_appraisal_id': self.id},
        }

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})

        # ---- Step 1: copy main record (respecting copy=False automatically)
        new_appraisal = super().copy(default)

        # ---- Step 2: duplicate appraisers
        for appraiser in self.performance_appraiser_ids:
            new_appraiser = appraiser.copy({
                'performance_appraisal_id': new_appraisal.id,
            })

        return new_appraisal


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    appraisal_score = fields.Float(
        compute='_compute_appraisal_score',
        store=True,
        string="Score"
    )

    performance_appraisal_ids = fields.One2many(
        'performance.appraisal',
        'employee_id'
    )

    appraisal_count = fields.Integer(
        compute='_compute_appraisal_count',
        string="Appraisals"
    )

    def _compute_appraisal_count(self):
        for employee in self:
            employee.appraisal_count = len(
                employee.performance_appraisal_ids.filtered(lambda a: a.state == 'confirmed')
            )

    @api.depends('performance_appraisal_ids.score', 'performance_appraisal_ids.state')
    def _compute_appraisal_score(self):
        for employee in self:
            confirmed = employee.performance_appraisal_ids.filtered(
                lambda a: a.state == 'confirmed' and a.score
            )
            employee.appraisal_score = (
                round(sum(confirmed.mapped('score')) / len(confirmed), 2)
                if confirmed else 0.0
            )

    def action_view_appraisals(self):
        self.ensure_one()
        return {
            'name': 'Performance Appraisals',
            'type': 'ir.actions.act_window',
            'res_model': 'performance.appraisal',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
            },
        }