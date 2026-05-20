from odoo import models, fields, api


class SignTemplate(models.Model):
    _name = "sign.template"
    _description = "Sign Template"
    _order = "create_date desc"


    # =====================================================
    # BASIC INFO
    # =====================================================

    name = fields.Char(
        string="Document Name",
        required=True
    )

    tag_ids = fields.Many2many(
        "sign.tag",
        string="Tags"
    )

    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        default=lambda self: self.env.user
    )


    # =====================================================
    # FAVORITES
    # =====================================================

    favorited_ids = fields.Many2many(
        "res.users",
        string="Favorited By"
    )

    is_favorite = fields.Boolean(
        string="Favorite",
        compute="_compute_is_favorite",
        inverse="_inverse_is_favorite"
    )


    # =====================================================
    # PDF DOCUMENT
    # =====================================================

    document = fields.Binary(
        string="Upload PDF",
        attachment=True
    )

    document_name = fields.Char(
        string="File Name"
    )

    attachment_id = fields.Many2one(
        "ir.attachment",
        string="PDF Attachment",
        compute="_compute_attachment",
        store=True,
    )


    # =====================================================
    # SIGN REQUESTS
    # =====================================================

    sign_request_ids = fields.One2many(
        "sign.request",
        "template_id",
        string="Sign Requests"
    )

    sign_count = fields.Integer(
        string="Signed",
        compute="_compute_sign_stats"
    )

    in_progress_count = fields.Integer(
        string="In Progress",
        compute="_compute_sign_stats"
    )

    signee_count = fields.Integer(
        string="Signees",
        compute="_compute_sign_stats"
    )

    sign_request_count = fields.Integer(
        string="Documents",
        compute="_compute_sign_stats"
    )


    # =====================================================
    # SIGN ITEMS (PLACED FIELDS)
    # =====================================================

    sign_item_ids = fields.One2many(
        "sign.item",
        "template_id",
        string="Sign Items"
    )

    sign_item_count = fields.Integer(
        string="Signature fields",
        compute="_compute_item_count"
    )


    # =====================================================
    # FAVORITE COMPUTE
    # =====================================================

    @api.depends("favorited_ids")
    def _compute_is_favorite(self):
        for rec in self:
            rec.is_favorite = self.env.user in rec.favorited_ids


    def _inverse_is_favorite(self):
        for rec in self:
            if rec.is_favorite:
                if self.env.user not in rec.favorited_ids:
                    rec.favorited_ids = [(4, self.env.user.id)]
            else:
                if self.env.user in rec.favorited_ids:
                    rec.favorited_ids = [(3, self.env.user.id)]


    # =====================================================
    # PDF ATTACHMENT
    # =====================================================

    @api.depends("document")
    def _compute_attachment(self):
        for rec in self:
            if not rec.id:
                rec.attachment_id = False
                continue

            attachment = self.env["ir.attachment"].sudo().search([
                ("res_model", "=", "sign.template"),
                ("res_id", "=", rec.id),
                ("res_field", "=", "document"),
            ], limit=1)

            rec.attachment_id = attachment.id if attachment else False


    # =====================================================
    # SIGN STATS
    # =====================================================

    @api.depends("sign_request_ids.state", "sign_request_ids.signer_ids")
    def _compute_sign_stats(self):
        for rec in self:
            rec.sign_count = sum(
                1 for r in rec.sign_request_ids
                if r.state == "signed"
            )

            rec.in_progress_count = sum(
                1 for r in rec.sign_request_ids
                if r.state == "sent"
            )

            rec.signee_count = sum(
                len(r.signer_ids) for r in rec.sign_request_ids
            )

            rec.sign_request_count = len(rec.sign_request_ids)

    @api.depends("sign_item_ids")
    def _compute_item_count(self):
        for rec in self:
            rec.sign_item_count = len(rec.sign_item_ids)


    # =====================================================
    # ACTIONS
    # =====================================================

    def action_send(self):
        self.ensure_one()

        wizard = self.env["sign.send.wizard"].create({
            "template_id": self.id,
        })

        return {
            "type": "ir.actions.act_window",
            "name": "New Signature Request",
            "res_model": "sign.send.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }


    def action_sign_now(self):
        self.ensure_one()

        wizard = self.env["sign.send.wizard"].create({
            "template_id": self.id,
        })

        return {
            "type": "ir.actions.act_window",
            "name": "New Signature Request",
            "res_model": "sign.send.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }


    def action_share(self):
        self.ensure_one()

        wizard = self.env["sign.share.wizard"].create({
            "template_id": self.id,
        })

        return {
            "type": "ir.actions.act_window",
            "name": "Share Document",
            "res_model": "sign.share.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }


# =========================================================
# TAG MODEL
# =========================================================

class SignTag(models.Model):
    _name = "sign.tag"
    _description = "Sign Tag"

    name = fields.Char(
        string="Tag Name",
        required=True
    )

    color = fields.Integer(
        string="Color"
    )