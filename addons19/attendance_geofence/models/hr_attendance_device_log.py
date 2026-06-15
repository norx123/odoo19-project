# -*- coding: utf-8 -*-

from odoo import models, fields


class HrAttendanceDeviceLog(models.Model):
    """
    Stores device information captured at check-in and check-out.
    One record per attendance event (checkin / checkout).
    """
    _name        = 'hr.attendance.device.log'
    _description = 'Attendance Device Information Log'
    _order       = 'logged_at asc'

    attendance_id = fields.Many2one(
        'hr.attendance', string='Attendance', required=True,
        ondelete='cascade', index=True,
    )
    event_type = fields.Selection(
        [('checkin', 'Check-In'), ('checkout', 'Check-Out')],
        string='Event', required=True,
    )
    logged_at = fields.Datetime(string='Logged At', default=fields.Datetime.now)

    # ── Network ───────────────────────────────────────────────────────────────
    ip_address    = fields.Char(string='IP Address',       size=64)
    wifi_ssid     = fields.Char(string='WiFi SSID',        size=256)
    carrier       = fields.Char(string='Mobile Operator',  size=128)

    # ── Browser / UA ─────────────────────────────────────────────────────────
    browser       = fields.Char(string='Browser',          size=128)
    browser_ver   = fields.Char(string='Browser Version',  size=64)
    user_agent    = fields.Char(string='User Agent',       size=1024)

    # ── Device ────────────────────────────────────────────────────────────────
    device_name   = fields.Char(string='Device Name',      size=256)
    device_model  = fields.Char(string='Device Model',     size=256)
    device_type   = fields.Char(string='Device Type',      size=64)   # Phone/Tablet/Desktop
    os_name       = fields.Char(string='Operating System', size=128)
    os_version    = fields.Char(string='OS Version',       size=64)

    # ── Battery ───────────────────────────────────────────────────────────────
    battery_level    = fields.Float(string='Battery Level (%)', digits=(5, 1))
    battery_charging = fields.Boolean(string='Charging', default=False)
