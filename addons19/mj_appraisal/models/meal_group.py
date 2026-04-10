from odoo import models, fields

class MealGroup(models.Model):
    _name = 'meal.group'
    _description = 'Meal Group'

    name = fields.Char("Name", required=True)