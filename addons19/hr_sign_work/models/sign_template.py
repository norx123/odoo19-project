from odoo import models, fields, api


class SignTemplate(models.Model):
    _name = "sign.template"
    _description = "Sign Template"
    _order = "create_date desc"

    # =====================================================
    # BASIC
    # =====================================================

    name = fields.Char(string="Document Name", required=True)
    tag_ids = fields.Many2many("sign.tag", string="Tags")
    user_id = fields.Many2one(
        "res.users", string="Responsible",
        default=lambda self: self.env.user,
    )

    active = fields.Boolean(default=True)

    # =====================================================
    # FAVORITES
    # =====================================================

    favorited_ids = fields.Many2many("res.users", string="Favorited By")
    is_favorite = fields.Boolean(
        string="Favorite",
        compute="_compute_is_favorite",
        inverse="_inverse_is_favorite",
        search="_search_is_favorite",
    )

    # =====================================================
    # PDF
    # =====================================================

    document = fields.Binary(
        string="Upload PDF", attachment=True,
    )
    document_name = fields.Char(string="File Name")

    attachment_id = fields.Many2one(
        "ir.attachment",
        string="PDF Attachment",
        compute="_compute_attachment",
        store=True,
    )

    # =====================================================
    # REQUESTS
    # =====================================================

    sign_request_ids = fields.One2many(
        "sign.request", "template_id", string="Sign Requests",
    )

    sign_count = fields.Integer(
        string="Signed", compute="_compute_sign_stats",
    )
    in_progress_count = fields.Integer(
        string="In Progress", compute="_compute_sign_stats",
    )
    signee_count = fields.Integer(
        string="Signees", compute="_compute_sign_stats",
    )
    sign_request_count = fields.Integer(
        string="Documents", compute="_compute_sign_stats",
    )

    # =====================================================
    # SIGN ITEMS (placed field positions)
    # =====================================================

    sign_item_ids = fields.One2many(
        "sign.item", "template_id", string="Sign Items",
        copy=True,
    )

    sign_item_count = fields.Integer(
        string="Signature fields", compute="_compute_item_count",
    )

    # =====================================================
    # FAVORITE COMPUTE
    # =====================================================

    @api.depends("favorited_ids")
    def _compute_is_favorite(self):
        user = self.env.user
        for rec in self:
            rec.is_favorite = user in rec.favorited_ids

    def _inverse_is_favorite(self):
        user = self.env.user
        for rec in self:
            if rec.is_favorite:
                if user not in rec.favorited_ids:
                    rec.favorited_ids = [(4, user.id)]
            else:
                if user in rec.favorited_ids:
                    rec.favorited_ids = [(3, user.id)]

    def _search_is_favorite(self, operator, value):
        if operator not in ("=", "!="):
            return []
        match = (operator == "=") == bool(value)
        op = "in" if match else "not in"
        return [("favorited_ids", op, [self.env.user.id])]

    # =====================================================
    # PDF ATTACHMENT
    # =====================================================

    @api.depends("document")
    def _compute_attachment(self):
        Attachment = self.env["ir.attachment"].sudo()
        for rec in self:
            if not rec.id:
                rec.attachment_id = False
                continue
            att = Attachment.search([
                ("res_model", "=", "sign.template"),
                ("res_id", "=", rec.id),
                ("res_field", "=", "document"),
            ], limit=1)
            rec.attachment_id = att.id if att else False

    # =====================================================
    # STATS
    # =====================================================

    @api.depends("sign_request_ids.state", "sign_request_ids.signer_ids")
    def _compute_sign_stats(self):
        for rec in self:
            requests = rec.sign_request_ids
            rec.sign_count = sum(1 for r in requests if r.state == "signed")
            rec.in_progress_count = sum(1 for r in requests if r.state == "sent")
            rec.signee_count = sum(len(r.signer_ids) for r in requests)
            rec.sign_request_count = len(requests)

    @api.depends("sign_item_ids")
    def _compute_item_count(self):
        for rec in self:
            rec.sign_item_count = len(rec.sign_item_ids)

    # =====================================================
    # SAVE FIELD POSITIONS FROM JS (called via RPC)
    # =====================================================

    def save_sign_items(self, items):
        """
        Replace this template's sign items with the provided list.
        `items` is a list of dicts coming from the JS editor:
            [{type_id, placeholder, mandatory, alignment, readonly,
              page, pos_x, pos_y, width, height, responsible_role}, ...]
        """
        self.ensure_one()
        SignItem = self.env["sign.item"]

        # Wipe previous placements
        self.sign_item_ids.unlink()

        created = []
        for it in items or []:
            try:
                type_id = int(it.get("type_id"))
            except (TypeError, ValueError):
                continue
            if not type_id:
                continue

            vals = {
                "template_id": self.id,
                "type_id": type_id,
                "placeholder": it.get("placeholder") or "",
                "alignment": it.get("alignment") or "left",
                "read_only": bool(it.get("readonly")),
                "required": bool(it.get("mandatory")),
                "page": int(it.get("page") or 1),
                "pos_x": float(it.get("pos_x") or 0.0),
                "pos_y": float(it.get("pos_y") or 0.0),
                "width": float(it.get("width") or 18.0),
                "height": float(it.get("height") or 5.0),
                "responsible_role": it.get("responsible_role") or "Signer 1",
            }
            rec = SignItem.create(vals)
            created.append(rec.id)

        return {"saved": len(created), "ids": created}

    def get_sign_items(self):
        """Return placed sign items for JS to render."""
        self.ensure_one()
        out = []
        for it in self.sign_item_ids:
            out.append({
                "id": it.id,
                "type_id": it.type_id.id,
                "type_name": it.type_id.name,
                "item_type": it.item_type,
                "placeholder": it.placeholder or "",
                "alignment": it.alignment or "left",
                "readonly": it.read_only,
                "mandatory": it.required,
                "page": it.page,
                "pos_x": it.pos_x,
                "pos_y": it.pos_y,
                "width": it.width,
                "height": it.height,
                "responsible_role": it.responsible_role or "Signer 1",
            })
        return out

    # =====================================================
    # ACTIONS
    # =====================================================

    def action_send(self):
        self.ensure_one()
        wizard = self.env["sign.send.wizard"].create({"template_id": self.id})
        return {
            "type": "ir.actions.act_window",
            "name": "New Signature Request",
            "res_model": "sign.send.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
            "context": {"default_send_mode": "send"},
        }

    def action_sign_now(self):
        """Create a request signed-by-me, jump straight to sign UI."""
        self.ensure_one()
        request = self.env["sign.request"].create({
            "template_id": self.id,
            "state": "sent",
            "signer_ids": [(0, 0, {
                "partner_id": self.env.user.partner_id.id,
                "state": "sent",
            })],
        })
        # Send user to the signing page
        return {
            "type": "ir.actions.act_url",
            "url": "/sign/document/%d" % request.id,
            "target": "self",
        }

    def action_share(self):
        self.ensure_one()
        wizard = self.env["sign.share.wizard"].create({"template_id": self.id})
        return {
            "type": "ir.actions.act_window",
            "name": "Share Document",
            "res_model": "sign.share.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }


# =========================================================
# TAG
# =========================================================

class SignTag(models.Model):
    _name = "sign.tag"
    _description = "Sign Tag"
    _order = "name"

    name = fields.Char(string="Tag Name", required=True)
    color = fields.Integer(string="Color")
