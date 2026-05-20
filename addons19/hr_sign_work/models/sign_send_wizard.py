from odoo import models, fields, api
import uuid


class SignSendWizard(models.TransientModel):
    _name = "sign.send.wizard"
    _description = "Send Signature Request Wizard"

    # =====================================================
    # TEMPLATE
    # =====================================================

    template_id = fields.Many2one(
        "sign.template",
        string="Template",
        required=True,
        readonly=True,
    )

    # =====================================================
    # SIGNER
    # =====================================================

    signer_id = fields.Many2one(
        "res.partner",
        string="Signer 1",
        required=True,
        default=lambda self: self.env.user.partner_id,
    )

    # =====================================================
    # EMAIL OPTIONS
    # =====================================================

    subject = fields.Char(
        string="Subject",
        compute="_compute_subject",
        store=True,
        readonly=False,
    )

    cc_partner_ids = fields.Many2many(
        "res.partner",
        string="CC",
    )

    message = fields.Text(
        string="Message",
    )

    # =====================================================
    # EXTRA OPTIONS (visible when email is selected)
    # =====================================================

    valid_until = fields.Date(
        string="Valid Until",
    )

    reminders = fields.Boolean(
        string="Reminders",
        default=False,
    )

    hide_certificate = fields.Boolean(
        string="Hide certificate key on pages",
        default=False,
    )

    # =====================================================
    # COMPUTE
    # =====================================================

    @api.depends("template_id")
    def _compute_subject(self):
        for rec in self:
            if rec.template_id:
                rec.subject = "Signature Request - %s" % (rec.template_id.name or "")
            else:
                rec.subject = ""

    # =====================================================
    # ACTIONS
    # =====================================================

    def action_sign_now(self):
        self.ensure_one()

        request = self.env["sign.request"].create({
            "template_id": self.template_id.id,
            "state": "sent",
            "signer_ids": [(0, 0, {
                "partner_id": self.signer_id.id,
                "state": "sent",
            })],
        })

        return {
            "type": "ir.actions.act_window",
            "name": "Sign Now",
            "res_model": "sign.request",
            "res_id": request.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_send(self):
        self.ensure_one()

        request = self.env["sign.request"].create({
            "template_id": self.template_id.id,
            "state": "sent",
            "signer_ids": [(0, 0, {
                "partner_id": self.signer_id.id,
                "state": "sent",
            })],
        })

        return {"type": "ir.actions.act_window_close"}


class SignShareWizard(models.TransientModel):
    _name = "sign.share.wizard"
    _description = "Share Document Wizard"

    # =====================================================
    # TEMPLATE
    # =====================================================

    template_id = fields.Many2one(
        "sign.template",
        string="Template",
        required=True,
        readonly=True,
    )

    # =====================================================
    # SHARE LINK
    # =====================================================

    share_link = fields.Char(
        string="Share Link",
        compute="_compute_share_link",
        store=True,
    )

    valid_until = fields.Date(
        string="Valid Until",
    )

    is_shared = fields.Boolean(
        string="Is Shared",
        default=True,
    )

    # =====================================================
    # COMPUTE
    # =====================================================

    @api.depends("template_id")
    def _compute_share_link(self):
        for rec in self:
            if rec.template_id:
                token = uuid.uuid4().hex
                base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                rec.share_link = "%s/sign/document/mail/%s/%s" % (
                    base_url,
                    rec.template_id.id,
                    token,
                )
            else:
                rec.share_link = ""

    # =====================================================
    # ACTIONS
    # =====================================================

    def action_stop_sharing(self):
        self.ensure_one()
        self.is_shared = False
        return {"type": "ir.actions.act_window_close"}

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}
