# -*- coding: utf-8 -*-
"""
Post-install hook: Dynamically find hr_expense menus and add our items.
This avoids hardcoded XML IDs that differ across Odoo versions.
"""
import logging
_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Find actual Expenses menu and add Travel Expense submenus."""
    
    IrUiMenu = env['ir.ui.menu']
    IrModelData = env['ir.model.data']
    
    # ── Find actions ────────────────────────────────────────────────────
    def get_action(xml_id):
        try:
            return env.ref(f'employee_travel_expense.{xml_id}')
        except Exception:
            return None

    action_my      = get_action('action_travel_expense_my')
    action_all     = get_action('action_travel_expense_all')
    action_vehicle = get_action('action_vehicle_registration')
    action_rate    = get_action('action_mileage_rate')

    # ── Find hr_expense menus (try multiple possible IDs) ────────────────
    def find_menu(*xml_ids):
        for xml_id in xml_ids:
            try:
                return env.ref(xml_id)
            except Exception:
                continue
        return None

    # Odoo 17/18/19 use different IDs - try all variants
    menu_root = find_menu(
        'hr_expense.menu_hr_expense_root',
        'hr_expense.menu_hr_expense',
    )
    menu_my = find_menu(
        'hr_expense.menu_my_expenses',
        'hr_expense.menu_hr_expense_new_expense',
        'hr_expense.menu_hr_expense_my_expenses',
    )
    menu_all = find_menu(
        'hr_expense.menu_hr_expense_all_expenses',
        'hr_expense.menu_all_expenses',
        'hr_expense.menu_hr_expense_all',
    )
    menu_config = find_menu(
        'hr_expense.menu_hr_expense_configuration',
        'hr_expense.menu_hr_expense_config',
        'hr_expense.menu_expense_configuration',
    )

    # ── If we couldn't find hr_expense menus, use our own root ──────────
    if not menu_root:
        _logger.warning("hr_expense root menu not found, using standalone Travel Expense menu")
        return  # standalone menus already created via XML

    _logger.info("hr_expense root menu found: %s (id=%s)", menu_root.name, menu_root.id)

    # ── Helper to create or update menu ─────────────────────────────────
    def ensure_menu(xml_id, name, parent, action, sequence, groups=None):
        # Check if already exists
        try:
            menu = env.ref(f'employee_travel_expense.{xml_id}')
            menu.write({'parent_id': parent.id, 'action': f'{action._name},{action.id}' if action else False})
            return menu
        except Exception:
            pass
        vals = {
            'name': name,
            'parent_id': parent.id,
            'sequence': sequence,
            'active': True,
        }
        if action:
            vals['action'] = f'{action._name},{action.id}'
        if groups:
            vals['groups_id'] = [(6, 0, groups.ids)]
        menu = IrUiMenu.create(vals)
        # Register XML ID
        IrModelData.create({
            'name': xml_id,
            'module': 'employee_travel_expense',
            'model': 'ir.ui.menu',
            'res_id': menu.id,
            'noupdate': False,
        })
        return menu

    manager_group = env.ref('hr_expense.group_hr_expense_manager', raise_if_not_found=False)
    groups = manager_group if manager_group else env['res.groups']

    # Add to "My Expenses" section
    if menu_my and action_my:
        ensure_menu('dyn_menu_my_travel', 'My Travel Expenses', menu_my, action_my, 20)
    if menu_my and action_vehicle:
        ensure_menu('dyn_menu_my_vehicles', 'My Vehicles', menu_my, action_vehicle, 30)

    # Add to "All Expenses" / Manager section
    if menu_all and action_all:
        ensure_menu('dyn_menu_all_travel', 'All Travel Expenses', menu_all, action_all, 10)

    # Add to Configuration section
    if menu_config:
        if action_rate:
            ensure_menu('dyn_menu_rate_config', 'Mileage Rate', menu_config, action_rate, 10)
        if action_vehicle:
            ensure_menu('dyn_menu_vehicle_config', 'Vehicle Registration', menu_config, action_vehicle, 20)

    _logger.info("Travel Expense menus successfully added to Expenses module.")
