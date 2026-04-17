from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BonusCalculator(models.Model):
    _name = 'bonus.calculator'
    _description = 'Bonus Calculator'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)

    basic_da = fields.Float(string="Basic + DA", required=True)
    bonus_percentage = fields.Float(string="Bonus Percentage (%)", required=True)
    minimum_wage = fields.Float(string="Minimum Wage")

    eligible = fields.Boolean(string="Eligible", compute="_compute_bonus", store=True)
    bonus_amount = fields.Float(string="Bonus Amount", compute="_compute_bonus", store=True)

    @api.depends('basic_da', 'bonus_percentage')
    def _compute_bonus(self):
        for rec in self:
            rec.eligible = False
            rec.bonus_amount = 0

            if rec.basic_da <= 21000:
                rec.eligible = True

                # Apply ceiling rule
                salary_for_bonus = rec.basic_da
                if rec.basic_da > 7000:
                    salary_for_bonus = 7000

                rec.bonus_amount = (salary_for_bonus * rec.bonus_percentage) / 100
            else:
                rec.eligible = False
                rec.bonus_amount = 0

    @api.constrains('bonus_percentage')
    def _check_percentage(self):
        for rec in self:
            if rec.bonus_percentage < 8.33 or rec.bonus_percentage > 20:
                raise ValidationError("Bonus % must be between 8.33 and 20")