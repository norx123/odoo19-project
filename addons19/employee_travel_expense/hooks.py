# -*- coding: utf-8 -*-
"""
Post-install hook: Menu name se dhundho, XML ID pe depend mat karo.
Yeh Odoo 16/17/18/19 sabme kaam karega.
"""
import logging
_logger = logging.getLogger(__name__)


def _get_action(env, xml_id):
    try:
        return env.ref(f'employee_travel_expense.{xml_id}')
    except Exception:
        return None


def _find_expense_menus(env):
    """
    hr_expense ke menus ko name se dhundho.
    XML ID pe depend nahi karte — version-safe approach.
    """
    IrMenu = env['ir.ui.menu']

    # Pehle root "Expenses" menu dhundho (top level, no parent)
    root = IrMenu.search([
        ('parent_id', '=', False),
        ('name', 'ilike', 'Expense'),
    ], limit=1)

    if not root:
        # Try with complete_name
        root = IrMenu.search([
            ('complete_name', '=', 'Expenses'),
        ], limit=1)

    _logger.info("Travel hook: root expense menu = %s (id=%s)", root.name if root else None, root.id if root else None)

    if not root:
        return None, None, None, None

    # Children of root
    children = IrMenu.search([('parent_id', '=', root.id)])
    child_names = {c.name.lower(): c for c in children}
    _logger.info("Travel hook: expense children = %s", list(child_names.keys()))

    # My Expenses submenu
    menu_my = (
        child_names.get('my expenses') or
        child_names.get('my expense') or
        children[:1] or  # fallback: first child
        None
    )
    if hasattr(menu_my, '__iter__') and not hasattr(menu_my, 'name'):
        menu_my = menu_my[0] if menu_my else None

    # All Expenses / Manager submenu
    menu_all = (
        child_names.get('all expenses') or
        child_names.get('expenses') or
        child_names.get('manager') or
        None
    )
    if hasattr(menu_all, '__iter__') and not hasattr(menu_all, 'name'):
        menu_all = None

    # Configuration submenu
    menu_config = (
        child_names.get('configuration') or
        child_names.get('config') or
        None
    )
    if hasattr(menu_config, '__iter__') and not hasattr(menu_config, 'name'):
        menu_config = None

    return root, menu_my, menu_all, menu_config


def _create_menu(env, xml_id, name, parent, action, sequence, groups=None):
    """Create menu item and register its XML ID."""
    IrMenu = env['ir.ui.menu']
    IrModelData = env['ir.model.data']

    # Delete old record if exists (upgrade case)
    old = IrModelData.search([
        ('module', '=', 'employee_travel_expense'),
        ('name', '=', xml_id),
        ('model', '=', 'ir.ui.menu'),
    ])
    if old:
        try:
            old_menu = IrMenu.browse(old.mapped('res_id'))
            old_menu.unlink()
            old.unlink()
        except Exception:
            pass

    vals = {
        'name': name,
        'parent_id': parent.id,
        'sequence': sequence,
        'active': True,
    }
    if action:
        vals['action'] = '%s,%s' % (action._name, action.id)
    if groups:
        vals['groups_id'] = [(6, 0, groups.ids)]

    menu = IrMenu.create(vals)

    IrModelData.create({
        'name': xml_id,
        'module': 'employee_travel_expense',
        'model': 'ir.ui.menu',
        'res_id': menu.id,
        'noupdate': True,
    })
    _logger.info("Created menu '%s' under '%s'", name, parent.name)
    return menu


def post_init_hook(env):
    """Attach Travel Expense menus inside the Expenses module."""

    action_my      = _get_action(env, 'action_travel_expense_my')
    action_all     = _get_action(env, 'action_travel_expense_all')
    action_vehicle = _get_action(env, 'action_vehicle_registration')
    action_rate    = _get_action(env, 'action_mileage_rate')

    root, menu_my, menu_all, menu_config = _find_expense_menus(env)

    if not root:
        _logger.warning(
            "Expenses root menu not found. "
            "Travel Expense menus will appear in standalone 'Travel Expense' menu."
        )
        # Activate the fallback standalone root menu
        try:
            fallback = env.ref('employee_travel_expense.menu_travel_expense_root')
            fallback.write({'active': True})
            _logger.info("Standalone Travel Expense menu activated.")
        except Exception as e:
            _logger.error("Could not activate fallback menu: %s", e)
        return

    manager_group = env.ref('hr_expense.group_hr_expense_manager', raise_if_not_found=False)

    # ── My Expenses section ───────────────────────────────────────────
    if menu_my:
        _create_menu(env, 'dyn_menu_my_travel', 'My Travel Expenses',
                     menu_my, action_my, 25)
        _create_menu(env, 'dyn_menu_my_vehicles', 'My Vehicles',
                     menu_my, action_vehicle, 30)

    # ── All Expenses / Manager section ───────────────────────────────
    if menu_all:
        _create_menu(env, 'dyn_menu_all_travel', 'All Travel Expenses',
                     menu_all, action_all, 15,
                     groups=manager_group)

    # ── Configuration section ─────────────────────────────────────────
    if menu_config:
        _create_menu(env, 'dyn_menu_rate_config', 'Mileage Rate',
                     menu_config, action_rate, 15,
                     groups=manager_group)
        _create_menu(env, 'dyn_menu_vehicle_config', 'Vehicle Registration',
                     menu_config, action_vehicle, 16,
                     groups=manager_group)

    _logger.info("Travel Expense menus successfully integrated into Expenses module.")
