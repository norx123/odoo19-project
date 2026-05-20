from odoo import models, fields, api


class SignItem(models.Model):
    _name = "sign.item"
    _description = "Sign Item (Field on PDF)"
    _order = "id asc"


    # =====================================================
    # TEMPLATE LINK
    # =====================================================

    template_id = fields.Many2one(
        "sign.template",
        string="Template",
        required=True,
        ondelete="cascade"
    )


    # =====================================================
    # FIELD TYPE
    # =====================================================

    type_id = fields.Selection([
        ("signature", "Signature"),
        ("initial", "Initials"),
        ("name", "Name"),
        ("email", "Email"),
        ("phone", "Phone"),
        ("company", "Company"),
        ("text", "Text"),
        ("multiline", "Multiline"),
        ("checkbox", "Checkbox"),
        ("radio", "Radio"),
        ("selection", "Selection"),
        ("date", "Date"),
        ("strikethrough", "Strikethrough"),
        ("stamp", "Stamp"),
    ],
        string="Field Type",
        required=True,
        default="signature"
    )

    name = fields.Char(
        string="Field Name",
        compute="_compute_name",
        store=True
    )


    # =====================================================
    # FIELD CONFIGURATION
    # =====================================================

    placeholder = fields.Char(
        string="Placeholder"
    )

    alignment = fields.Selection([
        ("left", "Left"),
        ("center", "Center"),
        ("right", "Right"),
    ],
        string="Alignment",
        default="left"
    )

    read_only = fields.Boolean(
        string="Read Only",
        default=False
    )

    value = fields.Text(
        string="Field Value"
    )


    # =====================================================
    # PDF POSITION
    # =====================================================

    page = fields.Integer(
        string="Page",
        default=1
    )

    pos_x = fields.Float(
        string="Position X (%)",
        default=10.0
    )

    pos_y = fields.Float(
        string="Position Y (%)",
        default=10.0
    )

    width = fields.Float(
        string="Width (%)",
        default=18.0
    )

    height = fields.Float(
        string="Height (%)",
        default=5.0
    )


    # =====================================================
    # RESPONSIBLE SIGNER
    # =====================================================

    responsible = fields.Char(
        string="Responsible",
        default="Signer 1"
    )

    required = fields.Boolean(
        string="Required",
        default=True
    )


    # =====================================================
    # AUTO FIELD NAME
    # =====================================================

    @api.depends("type_id", "responsible")
    def _compute_name(self):
        for rec in self:
            field_type = dict(
                self._fields["type_id"].selection
            ).get(rec.type_id, "Field")

            responsible = rec.responsible or "Signer"

            rec.name = f"{field_type} - {responsible}"


    # =====================================================
    # COPY SAFE DEFAULTS
    # =====================================================

    def copy(self, default=None):
        default = dict(default or {})

        if "name" not in default:
            default["name"] = f"{self.name} Copy"

        return super().copy(default)