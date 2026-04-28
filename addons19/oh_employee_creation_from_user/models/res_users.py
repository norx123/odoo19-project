from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Related Employee',
        ondelete='restrict',
        auto_join=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)

        for user in users:
            # ✅ Check if employee already exists
            existing_employee = self.env['hr.employee'].sudo().search([
                ('user_id', '=', user.id),
                ('company_id', '=', user.company_id.id)
            ], limit=1)

            if not existing_employee:
                employee = self.env['hr.employee'].sudo().create({
                    'name': user.name,
                    'user_id': user.id,
                    'work_email': user.login,
                    'company_id': user.company_id.id,
                })
                user.employee_id = employee.id
            else:
                # ✅ Just link if already exists
                user.employee_id = existing_employee.id

        return users