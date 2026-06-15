# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
from math import radians, sin, cos, sqrt, atan2


def _fmt_dt(dt, tz_name='UTC'):
    """Convert UTC datetime to user timezone and format nicely."""
    if not dt:
        return ''
    try:
        import pytz
        utc = pytz.utc.localize(dt) if dt.tzinfo is None else dt
        user_tz = pytz.timezone(tz_name)
        local_dt = utc.astimezone(user_tz)
        return local_dt.strftime('%d %b %Y, %I:%M %p')
    except Exception:
        return dt.strftime('%d %b %Y, %I:%M %p')


class GeoFenceController(http.Controller):

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Use the Haversine formula to calculate the distance in meters between two GPS coordinates."""
        R = 6371000
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = (
            sin(dlat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _get_attendance_fields(self):
        """Return the list of valid field names on hr.attendance for the current Odoo version."""
        AttendanceModel = request.env['hr.attendance'].sudo()
        return list(AttendanceModel._fields.keys())

    # -------------------------------------------------------------------------
    # Locations
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/locations', type='jsonrpc', auth='user')
    def get_employee_locations(self):
        """Return the list of work locations assigned to the currently logged-in employee."""
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1
        )
        if not employee:
            return {'locations': []}

        if employee.assigned_work_location_ids:
            locs = employee.assigned_work_location_ids
        elif employee.work_location_id:
            locs = employee.work_location_id
        else:
            return {'locations': []}

        locations = []
        for loc in locs:
            locations.append({
                'id': loc.id,
                'name': loc.name,
                'geofence_enabled': loc.geofence_enabled,
                'radius': loc.geofence_radius or 100,
                'has_coordinates': bool(loc.geofence_latitude or loc.geofence_longitude),
            })
        return {'locations': locations}

    # -------------------------------------------------------------------------
    # Check-In
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/checkin', type='jsonrpc', auth='user')
    def do_checkin(self, work_location_id=None, latitude=None, longitude=None, accuracy=None, location_name=None,
                   ip_address=None, wifi_ssid=None, carrier=None,
                   browser=None, browser_ver=None, user_agent=None,
                   device_name=None, device_model=None, device_type=None,
                   os_name=None, os_version=None,
                   battery_level=None, battery_charging=None):
        """
        Create an attendance check-in record for the current employee.
        If GPS coordinates are provided, save them as the check-in location point.
        """
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1
        )
        if not employee:
            return {'success': False, 'error': 'Employee not found.'}

        # Block duplicate check-in if an open attendance record already exists
        open_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)

        if open_attendance:
            return {'success': False, 'error': 'Already checked in.'}

        vals = {
            'employee_id': employee.id,
            'check_in': fields.Datetime.now(),
        }

        if work_location_id:
            valid_fields = self._get_attendance_fields()
            if 'work_location_id' in valid_fields:
                vals['work_location_id'] = int(work_location_id)

        try:
            attendance = request.env['hr.attendance'].sudo().create(vals)
        except Exception as e:
            return {'success': False, 'error': str(e)}

        # Save GPS point (independent — don't block checkin if this fails)
        if latitude is not None and longitude is not None:
            try:
                request.env['hr.attendance.location.log'].sudo().create({
                    'attendance_id': attendance.id,
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'point_type': 'checkin',
                    'accuracy': float(accuracy) if accuracy else 0.0,
                    'location_name': location_name or '',
                    'logged_at': fields.Datetime.now(),
                })
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("GPS log save failed: %s", e)

        # Save device information (independent — always attempt)
        try:
            request.env['hr.attendance.device.log'].sudo().create({
                'attendance_id': attendance.id,
                'event_type': 'checkin',
                'logged_at': fields.Datetime.now(),
                'ip_address': ip_address or request.httprequest.remote_addr or '',
                'wifi_ssid': wifi_ssid or '',
                'carrier': carrier or '',
                'browser': browser or '',
                'browser_ver': browser_ver or '',
                'user_agent': user_agent or '',
                'device_name': device_name or '',
                'device_model': device_model or '',
                'device_type': device_type or '',
                'os_name': os_name or '',
                'os_version': os_version or '',
                'battery_level': float(battery_level) if battery_level is not None else 0.0,
                'battery_charging': bool(battery_charging),
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Device log save failed on checkin: %s", e)

        return {'success': True, 'attendance_id': attendance.id}

    # -------------------------------------------------------------------------
    # Check-Out
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/checkout', type='jsonrpc', auth='user')
    def do_checkout(self, work_location_id=None, latitude=None, longitude=None, accuracy=None, location_name=None,
                    ip_address=None, wifi_ssid=None, carrier=None,
                    browser=None, browser_ver=None, user_agent=None,
                    device_name=None, device_model=None, device_type=None,
                    os_name=None, os_version=None,
                    battery_level=None, battery_charging=None):
        """
        Close the open attendance record for the current employee.
        If GPS coordinates are provided, save them as the check-out location point.
        """
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1
        )
        if not employee:
            return {'success': False, 'error': 'Employee not found.'}

        open_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)

        if not open_attendance:
            return {'success': False, 'error': 'No open attendance record found.'}

        # Save GPS point (independent)
        if latitude is not None and longitude is not None:
            try:
                request.env['hr.attendance.location.log'].sudo().create({
                    'attendance_id': open_attendance.id,
                    'latitude': float(latitude),
                    'longitude': float(longitude),
                    'point_type': 'checkout',
                    'accuracy': float(accuracy) if accuracy else 0.0,
                    'location_name': location_name or '',
                    'logged_at': fields.Datetime.now(),
                })
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("GPS checkout log failed: %s", e)

        # Write checkout time
        try:
            open_attendance.sudo().write({'check_out': fields.Datetime.now()})
        except Exception as e:
            return {'success': False, 'error': str(e)}

        # Save device information (independent)
        try:
            request.env['hr.attendance.device.log'].sudo().create({
                'attendance_id': open_attendance.id,
                'event_type': 'checkout',
                'logged_at': fields.Datetime.now(),
                'ip_address': ip_address or request.httprequest.remote_addr or '',
                'wifi_ssid': wifi_ssid or '',
                'carrier': carrier or '',
                'browser': browser or '',
                'browser_ver': browser_ver or '',
                'user_agent': user_agent or '',
                'device_name': device_name or '',
                'device_model': device_model or '',
                'device_type': device_type or '',
                'os_name': os_name or '',
                'os_version': os_version or '',
                'battery_level': float(battery_level) if battery_level is not None else 0.0,
                'battery_charging': bool(battery_charging),
            })
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Device log save failed on checkout: %s", e)

        return {'success': True}

    # -------------------------------------------------------------------------
    # Status
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/status', type='jsonrpc', auth='user')
    def get_checkin_status(self):
        """Return whether the current employee has an open (not checked-out) attendance record."""
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1
        )
        if not employee:
            return {'checked_in': False}

        open_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)

        return {
            'checked_in': bool(open_attendance),
            'attendance_id': open_attendance.id if open_attendance else False,
        }

    # -------------------------------------------------------------------------
    # Geofence Validation
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/check', type='jsonrpc', auth='user')
    def check_geofence(self, latitude, longitude, work_location_id=None):
        """Verify whether the employee's current coordinates are within the allowed radius."""
        WorkLocation = request.env['hr.work.location'].sudo()

        if work_location_id:
            location = WorkLocation.browse(int(work_location_id))
        else:
            employee = request.env['hr.employee'].sudo().search(
                [('user_id', '=', request.env.uid)], limit=1
            )
            location = employee.work_location_id if employee else None

        if not location or not location.geofence_enabled:
            return {'allowed': True, 'reason': 'no_geofence'}

        if not location.geofence_latitude and not location.geofence_longitude:
            return {'allowed': True, 'reason': 'location_not_set'}

        distance = self._calculate_distance(
            float(latitude), float(longitude),
            location.geofence_latitude, location.geofence_longitude,
        )
        radius = location.geofence_radius or 100

        if distance > radius:
            return {
                'allowed': False,
                'distance': round(distance, 2),
                'radius': radius,
                'location_name': location.name,
            }
        return {
            'allowed': True,
            'distance': round(distance, 2),
            'radius': radius,
            'location_name': location.name,
        }

    # -------------------------------------------------------------------------
    # GPS Path Tracking
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/track', type='jsonrpc', auth='user')
    def save_track_point(self, latitude, longitude, accuracy=None):
        """
        Called periodically by the browser (every 2 minutes) after check-in.
        Saves the employee's current GPS position against the open attendance record
        to build up the movement path.
        """
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1
        )
        if not employee:
            return {'success': False}

        open_attendance = request.env['hr.attendance'].sudo().search([
            ('employee_id', '=', employee.id),
            ('check_out', '=', False),
        ], limit=1)

        if not open_attendance:
            return {'success': False, 'reason': 'not_checked_in'}

        try:
            request.env['hr.attendance.location.log'].sudo().create({
                'attendance_id': open_attendance.id,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'point_type': 'track',
                'accuracy': float(accuracy) if accuracy else 0.0,
                'logged_at': fields.Datetime.now(),
            })
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    @http.route('/attendance/geofence/path', type='jsonrpc', auth='user')
    def get_attendance_path(self, attendance_id):
        """
        Return all GPS points recorded for a given attendance record.
        Used by the map widget in the Attendance form view to draw the movement path.
        """
        attendance = request.env['hr.attendance'].sudo().browse(int(attendance_id))
        if not attendance.exists():
            return {'points': []}

        # Security: employees can only view their own records; managers can view all
        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1
        )
        is_manager = request.env.user.has_group('hr_attendance.group_hr_attendance_manager')
        if not is_manager and (not employee or attendance.employee_id.id != employee.id):
            return {'points': [], 'error': 'Access denied.'}

        logs = request.env['hr.attendance.location.log'].sudo().search(
            [('attendance_id', '=', attendance.id)],
            order='logged_at asc',
        )

        # Get user's timezone
        try:
            user_tz = request.env.user.tz or 'UTC'
        except Exception:
            user_tz = 'UTC'

        points = []
        for log in logs:
            points.append({
                'lat': log.latitude,
                'lng': log.longitude,
                'type': log.point_type,
                'time': _fmt_dt(log.logged_at, user_tz),
                'accuracy': log.accuracy,
                'location_name': log.location_name or '',
            })

        return {
            'points': points,
            'employee_name': attendance.employee_id.name,
            'check_in': _fmt_dt(attendance.check_in, user_tz),
            'check_out': _fmt_dt(attendance.check_out, user_tz) if attendance.check_out else 'Still Checked In',
        }

    # -------------------------------------------------------------------------
    # Device Information
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/device_info', type='jsonrpc', auth='user')
    def get_device_info(self, attendance_id):
        """Return device logs for a given attendance record."""
        attendance = request.env['hr.attendance'].sudo().browse(int(attendance_id))
        if not attendance.exists():
            return {'logs': []}

        employee = request.env['hr.employee'].sudo().search(
            [('user_id', '=', request.env.uid)], limit=1)
        is_manager = request.env.user.has_group('hr_attendance.group_hr_attendance_manager')
        if not is_manager and (not employee or attendance.employee_id.id != employee.id):
            return {'logs': [], 'error': 'Access denied.'}

        logs = request.env['hr.attendance.device.log'].sudo().search(
            [('attendance_id', '=', attendance.id)], order='logged_at asc')

        try:
            user_tz = request.env.user.tz or 'UTC'
        except Exception:
            user_tz = 'UTC'

        result = []
        for log in logs:
            result.append({
                'event_type':      log.event_type,
                'logged_at':       _fmt_dt(log.logged_at, user_tz),
                'ip_address':      log.ip_address or '',
                'wifi_ssid':       log.wifi_ssid or '',
                'carrier':         log.carrier or '',
                'browser':         log.browser or '',
                'browser_ver':     log.browser_ver or '',
                'user_agent':      log.user_agent or '',
                'device_name':     log.device_name or '',
                'device_model':    log.device_model or '',
                'device_type':     log.device_type or '',
                'os_name':         log.os_name or '',
                'os_version':      log.os_version or '',
                'battery_level':   log.battery_level,
                'battery_charging':log.battery_charging,
            })
        return {'logs': result}

    # -------------------------------------------------------------------------
    # Debug — verify device log table (remove in production)
    # -------------------------------------------------------------------------

    @http.route('/attendance/geofence/debug_device', type='jsonrpc', auth='user')
    def debug_device_log(self, attendance_id=None):
        """Quick check: how many device logs exist for a given attendance."""
        if attendance_id:
            logs = request.env['hr.attendance.device.log'].sudo().search_count(
                [('attendance_id', '=', int(attendance_id))]
            )
            all_logs = request.env['hr.attendance.device.log'].sudo().search(
                [('attendance_id', '=', int(attendance_id))]
            )
            return {
                'count': logs,
                'records': [{'event': l.event_type, 'browser': l.browser,
                             'os': l.os_name, 'device': l.device_name,
                             'ip': l.ip_address, 'bat': l.battery_level} for l in all_logs]
            }
        total = request.env['hr.attendance.device.log'].sudo().search_count([])
        return {'total_records': total}

