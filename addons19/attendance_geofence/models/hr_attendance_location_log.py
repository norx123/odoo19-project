# -*- coding: utf-8 -*-

from odoo import models, fields


class HrAttendanceLocationLog(models.Model):
    """
    Stores GPS breadcrumb points recorded between an employee's check-in and
    check-out. Connecting all points in chronological order forms the
    employee's movement path for that attendance session.
    """
    _name = 'hr.attendance.location.log'
    _description = 'Attendance GPS Location Log'
    _order = 'logged_at asc'

    attendance_id = fields.Many2one(
        comodel_name='hr.attendance',
        string='Attendance Record',
        required=True,
        ondelete='cascade',
        index=True,
    )

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        related='attendance_id.employee_id',
        store=True,
        index=True,
    )

    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        required=True,
    )

    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        required=True,
    )

    logged_at = fields.Datetime(
        string='Logged At',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )

    point_type = fields.Selection(
        selection=[
            ('checkin', 'Check-In'),
            ('track', 'Movement'),
            ('checkout', 'Check-Out'),
        ],
        string='Point Type',
        default='track',
        required=True,
    )

    accuracy = fields.Float(
        string='Accuracy (meters)',
        digits=(8, 2),
        help='GPS accuracy radius in meters reported by the device.',
    )
