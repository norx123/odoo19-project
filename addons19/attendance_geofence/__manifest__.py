# -*- coding: utf-8 -*-
{
    'name': 'Attendance Geofence + Path Tracker',
    'version': '19.0.2.0.0',
    'category': 'Human Resources/Attendance',
    'summary': 'Geofence check-in restriction with GPS movement path tracking',
    'description': """
Attendance Geofence + Path Tracker
====================================
Features:
---------
* Latitude, Longitude and Radius configurable directly on Work Location
* GPS-based attendance validation (geofence)
* Employee can only punch in inside the allowed radius
* Clear warning message when outside radius

GPS Path Tracking (New):
* Employee GPS path is automatically recorded after check-in
* A location point is saved every 2 minutes in the background
* Check-out point is also saved
* View the full movement path on a map inside the Attendance form (date-wise)
* Interactive map on OpenStreetMap — Check-In (green), Movement (purple), Check-Out (red)
* Works with hr_attendance
    """,
    'author': 'Norx ERP',
    'website': 'https://norxerp.com',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'hr_attendance',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_work_location_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'attendance_geofence/static/src/js/attendance_geofence.js',
            'attendance_geofence/static/src/js/geofence_map_widget.js',
            'attendance_geofence/static/src/js/attendance_path_map.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
