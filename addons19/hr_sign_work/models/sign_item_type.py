from odoo import models, fields, api


class SignItemType(models.Model):
    _name = "sign.item.type"
    _description = "Signature Field Type"
    _order = "sequence, id"

    # =====================================================
    # BASIC
    # =====================================================

    name = fields.Char(string="Field Name", required=True)
    sequence = fields.Integer(string="Sequence", default=10)

    item_type = fields.Selection([
        ("signature", "Signature"),
        ("initial", "Initial"),
        ("text", "Text"),
        ("multiline", "Multiline Text"),
        ("checkbox", "Checkbox"),
        ("radio", "Radio"),
        ("selection", "Selection"),
        ("strikethrough", "Strikethrough"),
        ("stamp", "Stamp"),
        ("date", "Date"),
        ("name", "Name"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("company", "Company"),
        ("upload", "Upload"),
    ],
        string="Type",
        required=True,
        default="text",
    )

    # =====================================================
    # DEFAULTS USED WHEN PLACING THIS FIELD ON A PDF
    # =====================================================

    placeholder = fields.Char(string="Placeholder")
    tip = fields.Char(string="Tip")

    mandatory = fields.Boolean(string="Mandatory", default=True)
    read_only = fields.Boolean(string="Read Only", default=False)

    alignment = fields.Selection([
        ("left", "Left"),
        ("center", "Center"),
        ("right", "Right"),
    ],
        string="Alignment",
        default="left",
    )

    field_size = fields.Selection([
        ("small", "Small Text"),
        ("regular", "Regular Text"),
        ("large", "Large Text"),
    ],
        string="Field Size",
        default="regular",
    )

    default_width = fields.Float(string="Default Width (%)", default=18.0)
    default_height = fields.Float(string="Default Height (%)", default=5.0)

    # =====================================================
    # LINKED MODEL (auto-fill from a partner field, etc.)
    # =====================================================

    linked_model_id = fields.Many2one(
        "ir.model", string="Linked To", ondelete="set null",
    )
    linked_field_id = fields.Many2one(
        "ir.model.fields", string="Linked Field",
        domain="[('model_id', '=', linked_model_id)]",
        ondelete="set null",
    )

    # =====================================================
    # AUTO-FILL DEFAULTS WHEN ITEM TYPE CHANGES
    # =====================================================

    @api.onchange("item_type")
    def _onchange_item_type(self):
        partner_model = self.env.ref(
            "base.model_res_partner", raise_if_not_found=False,
        )
        defaults_map = {
            "name": ("Name", "name"),
            "email": ("Email", "email"),
            "phone": ("Phone", "phone"),
            "company": ("Company", "company_name"),
            "date": ("Date", None),
            "signature": ("Signature", None),
            "initial": ("Initial", None),
        }
        for rec in self:
            info = defaults_map.get(rec.item_type)
            if not info:
                continue
            label, partner_field = info
            if not rec.placeholder:
                rec.placeholder = label
            if partner_field and partner_model:
                rec.linked_model_id = partner_model
                rec.linked_field_id = self._get_partner_field(partner_field)

    def _get_partner_field(self, field_name):
        return self.env["ir.model.fields"].search([
            ("model", "=", "res.partner"),
            ("name", "=", field_name),
        ], limit=1)

    # =====================================================
    # TYPE SWITCHER (used by the form-view tab buttons)
    # =====================================================

    def _set_type(self, type_value):
        self.ensure_one()
        self.write({"item_type": type_value})
        return {
            "type": "ir.actions.act_window",
            "res_model": "sign.item.type",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
        }

    def set_type_signature(self):     return self._set_type("signature")
    def set_type_initial(self):       return self._set_type("initial")
    def set_type_text(self):          return self._set_type("text")
    def set_type_multiline(self):     return self._set_type("multiline")
    def set_type_checkbox(self):      return self._set_type("checkbox")
    def set_type_radio(self):         return self._set_type("radio")
    def set_type_selection(self):     return self._set_type("selection")
    def set_type_strikethrough(self): return self._set_type("strikethrough")
    def set_type_stamp(self):         return self._set_type("stamp")
    def set_type_date(self):          return self._set_type("date")
    def set_type_name(self):          return self._set_type("name")
    def set_type_email(self):         return self._set_type("email")
    def set_type_phone(self):         return self._set_type("phone")
    def set_type_company(self):       return self._set_type("company")
    def set_type_upload(self):        return self._set_type("upload")
