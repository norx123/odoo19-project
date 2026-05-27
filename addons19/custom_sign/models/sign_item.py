from odoo import models, fields, api


class SignItem(models.Model):
    _name = "custom.sign.item"
    _description = "Sign Item (Field placed on a PDF)"
    _order = "page, pos_y, pos_x"

    # =====================================================
    # PARENT
    # =====================================================

    template_id = fields.Many2one(
        "custom.sign.template",
        string="Template",
        ondelete="cascade",
        index=True,
    )

    request_id = fields.Many2one(
        "custom.sign.request",
        string="Request",
        ondelete="cascade",
        index=True,
    )

    # =====================================================
    # TYPE - Many2one to custom.sign.item.type so we can use ALL types
    # defined in master data without enum mismatch
    # =====================================================

    type_id = fields.Many2one(
        "custom.sign.item.type",
        string="Field Type",
        required=True,
        ondelete="restrict",
    )

    item_type = fields.Selection(
        related="type_id.item_type", store=True, readonly=True,
    )

    name = fields.Char(
        string="Field Name",
        compute="_compute_name",
        store=True,
    )

    # =====================================================
    # CONFIGURATION
    # =====================================================

    placeholder = fields.Char(string="Placeholder")
    alignment = fields.Selection([
        ("left", "Left"),
        ("center", "Center"),
        ("right", "Right"),
    ], string="Alignment", default="left")

    read_only = fields.Boolean(string="Read Only", default=False)
    required = fields.Boolean(string="Required", default=True)

    # Filled value (when signer fills the field)
    value = fields.Text(string="Field Value")

    # For signature/initial/stamp fields - stores the drawn image (PNG base64)
    signature_data = fields.Binary(string="Signature Image", attachment=True)

    # =====================================================
    # PDF POSITION (percentages of page width/height)
    # =====================================================

    page = fields.Integer(string="Page", default=1)
    pos_x = fields.Float(string="Position X (%)", default=10.0)
    pos_y = fields.Float(string="Position Y (%)", default=10.0)
    width = fields.Float(string="Width (%)", default=18.0)
    height = fields.Float(string="Height (%)", default=5.0)

    # =====================================================
    # SIGNER ASSIGNMENT
    # =====================================================

    responsible_role = fields.Char(string="Responsible", default="Signer 1")

    # =====================================================
    # COMPUTES
    # =====================================================

    @api.depends("type_id", "responsible_role", "type_id.name")
    def _compute_name(self):
        for rec in self:
            type_name = rec.type_id.name or "Field"
            role = rec.responsible_role or "Signer"
            rec.name = "%s - %s" % (type_name, role)

    def copy(self, default=None):
        default = dict(default or {})
        if "name" not in default and self.name:
            default["name"] = "%s Copy" % self.name
        return super().copy(default)
