# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class FvVisit(models.Model):
    _name = 'fv.visit'
    _description = 'Field Visit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, visit_time desc'

    name         = fields.Char('Reference', readonly=True, copy=False, default='New')
    employee_id  = fields.Many2one('hr.employee', 'Employee', required=True,
                                    default=lambda s: s.env['hr.employee'].search([('user_id','=',s.env.uid)], limit=1),
                                    tracking=True, index=True)
    dept_id      = fields.Many2one(related='employee_id.department_id', store=True, readonly=True, string='Department')
    manager_id   = fields.Many2one(related='employee_id.parent_id', store=True, readonly=True, string='Reporting Manager')

    visit_date   = fields.Date('Visit Date', required=True, default=fields.Date.today, tracking=True, index=True)
    visit_time   = fields.Float('Start Time', help='24h e.g. 10.5 = 10:30 AM')
    end_time     = fields.Float('End Time')

    # Purpose — what kind of visit
    visit_type   = fields.Selection([
        ('client_meeting', 'Client Meeting'),
        ('project_site',   'Project Site Visit'),
        ('shop_purchase',  'Shop / Purchase'),
        ('delivery',       'Delivery'),
        ('office_visit',   'Office / Branch Visit'),
        ('survey',         'Survey / Inspection'),
        ('other',          'Other'),
    ], string='Visit Type', required=True, default='client_meeting', tracking=True)

    # Where — employee types directly
    place_name   = fields.Char('Place Name', required=True,
                                help='e.g. ABC Hardware Shop, XYZ Client Office, Site-3 Varanasi')
    address      = fields.Text('Address', help='Full address of the location')
    city         = fields.Char('City')
    contact_name = fields.Char('Contact Person')
    contact_phone= fields.Char('Contact Phone')

    # What — description
    title        = fields.Char('Visit Title / Subject')
    purpose      = fields.Text('Purpose / Description',
                                help='What needs to be done, what to buy, whom to meet...')
    priority     = fields.Selection([('0','Normal'),('1','Important'),('2','Urgent')], default='0')

    # Assigned by manager
    assigned_by  = fields.Many2one('res.users', string='Assigned By',
                                    default=lambda s: s.env.user, readonly=True)
    is_self_added= fields.Boolean('Self Added', default=False,
                                   help='Employee added this visit themselves')

    # Status flow
    status = fields.Selection([
        ('planned',     'Planned'),
        ('in_progress', 'In Progress'),
        ('completed',   'Completed'),
        ('cancelled',   'Cancelled'),
    ], default='planned', tracking=True)

    # Check In
    check_in     = fields.Datetime('Check In Time', readonly=True)
    in_lat       = fields.Float('In Latitude',  readonly=True)
    in_lng       = fields.Float('In Longitude', readonly=True)
    in_map_url   = fields.Char('In Map URL')
    in_photo     = fields.Image('Check In Photo', max_width=1920, max_height=1080, readonly=True)
    in_device    = fields.Char('Device (In)', readonly=True)

    # Check Out
    check_out    = fields.Datetime('Check Out Time', readonly=True)
    out_lat      = fields.Float('Out Latitude',  readonly=True)
    out_lng      = fields.Float('Out Longitude', readonly=True)
    out_map_url  = fields.Char('Out Map URL')
    out_photo    = fields.Image('Check Out Photo', max_width=1920, max_height=1080, readonly=True)
    out_device   = fields.Char('Device (Out)', readonly=True)

    # Result
    duration     = fields.Float('Duration (hrs)', compute='_compute_duration', store=True)
    duration_str = fields.Char('Duration',        compute='_compute_duration', store=True)
    outcome      = fields.Text('Outcome / Result')

    @api.depends('check_in','check_out')
    def _compute_duration(self):
        for r in self:
            if r.check_in and r.check_out:
                secs = (r.check_out - r.check_in).total_seconds()
                h, m = int(secs // 3600), int((secs % 3600) // 60)
                r.duration     = round(secs / 3600, 2)
                r.duration_str = f'{h}h {m}m' if h else f'{m}m'
            else:
                r.duration, r.duration_str = 0.0, '-'

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env['ir.sequence']
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = seq.next_by_code('fv.visit') or '/'
        return super().create(vals_list)

    def action_cancel(self):
        self.write({'status': 'cancelled'})

    def action_reopen(self):
        self.write({'status': 'planned'})

    @api.model
    def cron_mark_missed(self):
        self.search([
            ('visit_date', '<', date.today()),
            ('status', '=', 'planned'),
        ]).write({'status': 'cancelled'})

    # ── RPC Methods for JS Dashboard ─────────────────────────
    @api.model
    def fv_get_my_visits(self, visit_date=None):
        """Get visits for current user — today or specific date"""
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if not emp:
            return {'ok': False, 'msg': 'No employee linked to your account. Ask admin: Employees > [Your Name] > HR Settings > Related User.'}

        if not visit_date:
            visit_date = date.today()
        elif isinstance(visit_date, str):
            visit_date = date.fromisoformat(visit_date)

        visits = self.search([
            ('employee_id', '=', emp.id),
            ('visit_date',  '=', visit_date),
            ('status', 'not in', ['cancelled']),
        ], order='visit_time asc, id asc')

        result = []
        for v in visits:
            vtype_label = dict(self._fields['visit_type'].selection).get(v.visit_type, '')
            result.append({
                'id':          v.id,
                'title':       v.title or v.place_name,
                'place':       v.place_name,
                'address':     v.address or '',
                'city':        v.city or '',
                'contact':     v.contact_name or '',
                'phone':       v.contact_phone or '',
                'vtype':       v.visit_type,
                'vtype_label': vtype_label,
                'purpose':     v.purpose or '',
                'priority':    v.priority,
                'start_time':  v.visit_time or 0,
                'end_time':    v.end_time or 0,
                'status':      v.status,
                'check_in':    fields.Datetime.context_timestamp(v, v.check_in).strftime('%I:%M %p')   if v.check_in  else '',
                'check_out':   fields.Datetime.context_timestamp(v, v.check_out).strftime('%I:%M %p') if v.check_out else '',
                'duration':    v.duration_str or '-',
                'in_map':      v.in_map_url  or '',
                'out_map':     v.out_map_url or '',
                'outcome':     v.outcome or '',
            })
        return {
            'ok':       True,
            'visits':   result,
            'emp_name': emp.name,
            'date':     str(visit_date),
        }

    @api.model
    def fv_add_visit(self, place_name, address, city, visit_type, title,
                      purpose, priority, visit_date, visit_time, end_time,
                      contact_name='', contact_phone=''):
        """Employee adds a new visit from dashboard"""
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if not emp:
            return {'ok': False, 'msg': 'No employee linked to your account.'}
        v = self.create({
            'employee_id':  emp.id,
            'place_name':   place_name,
            'address':      address,
            'city':         city,
            'visit_type':   visit_type,
            'title':        title,
            'purpose':      purpose,
            'priority':     priority,
            'visit_date':   visit_date,
            'visit_time':   float(visit_time or 0),
            'end_time':     float(end_time or 0),
            'contact_name': contact_name,
            'contact_phone':contact_phone,
            'is_self_added':True,
            'assigned_by':  self.env.user.id,
        })
        return {'ok': True, 'id': v.id, 'name': v.name}

    @api.model
    def fv_check_in(self, visit_id, lat, lng, photo, device=''):
        v = self.browse(int(visit_id))
        if not v.exists():
            return {'ok': False, 'msg': 'Visit not found'}
        if v.check_in:
            return {'ok': False, 'msg': 'Already checked in'}
        lat_f = float(lat or 0)
        lng_f = float(lng or 0)
        map_url = f'https://www.google.com/maps?q={lat_f:.6f},{lng_f:.6f}' if lat_f else ''
        v.write({
            'check_in':   datetime.now(),
            'in_lat':     lat_f,
            'in_lng':     lng_f,
            'in_photo':   photo or False,
            'in_device':  str(device or ''),
            'in_map_url': map_url,
            'status':     'in_progress',
        })
        local_in = fields.Datetime.context_timestamp(v, v.check_in)
        return {'ok': True, 'check_in': local_in.strftime('%I:%M %p'), 'map': map_url}

    @api.model
    def fv_check_out(self, visit_id, lat, lng, photo, outcome='', device=''):
        v = self.browse(int(visit_id))
        if not v.exists():
            return {'ok': False, 'msg': 'Visit not found'}
        if not v.check_in:
            return {'ok': False, 'msg': 'Please Check In first'}
        if v.check_out:
            return {'ok': False, 'msg': 'Already checked out'}
        lat_f = float(lat or 0)
        lng_f = float(lng or 0)
        map_url = f'https://www.google.com/maps?q={lat_f:.6f},{lng_f:.6f}' if lat_f else ''
        v.write({
            'check_out':   datetime.now(),
            'out_lat':     lat_f,
            'out_lng':     lng_f,
            'out_photo':   photo or False,
            'outcome':     str(outcome or ''),
            'out_device':  str(device or ''),
            'out_map_url': map_url,
            'status':      'completed',
        })
        v._compute_duration()
        local_out = fields.Datetime.context_timestamp(v, v.check_out)
        return {'ok': True, 'check_out': local_out.strftime('%I:%M %p'),
                'duration': v.duration_str or '-', 'map': map_url}
