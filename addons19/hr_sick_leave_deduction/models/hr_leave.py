from odoo import models, fields, api


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    no_of_leave_deduct = fields.Selection(
        [(str(i), str(i)) for i in range(1, 11)],
        string="No of Leave Deduct",
        default='1'
    )

    show_leave_deduct = fields.Boolean(
        compute="_compute_show_leave_deduct"
    )

    @api.depends('holiday_status_id')
    def _compute_show_leave_deduct(self):
        for rec in self:
            rec.show_leave_deduct = False

            if rec.holiday_status_id:
                leave_name = rec.holiday_status_id.name

                if leave_name in ['Medical Leave/Sick Leave', 'Medical Leave', 'Sick Leave']:
                    rec.show_leave_deduct = True

    @api.onchange('request_unit_half')
    def _onchange_request_unit_half(self):
        for rec in self:
            if rec.request_unit_half:
                rec.no_of_leave_deduct = '1'

    def action_validate(self):
        res = super().action_validate()

        for leave in self:

            deduct = int(leave.no_of_leave_deduct or 1)

            if deduct > 1:

                allocation = self.env['hr.leave.allocation'].search([
                    ('employee_id', '=', leave.employee_id.id),
                    ('holiday_status_id', '=', leave.holiday_status_id.id),
                    ('state', '=', 'validate')
                ], limit=1)

                if allocation:
                    allocation.number_of_days -= (deduct - 1)

        return res
