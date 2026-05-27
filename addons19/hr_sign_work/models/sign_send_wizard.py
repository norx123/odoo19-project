import uuid
from odoo import models, fields, api, _


class SignSendWizard(models.TransientModel):
    _name = "sign.send.wizard"
    _description = "Send Signature Request Wizard"

    template_id = fields.Many2one(
        "sign.template", string="Template",
        required=True, readonly=True,
    )

    signer_id = fields.Many2one(
        "res.partner", string="Signer 1",
        required=True,
        default=lambda self: self.env.user.partner_id,
    )

    cc_partner_ids = fields.Many2many("res.partner", string="CC")

    subject = fields.Char(
        string="Subject",
        compute="_compute_subject", store=True, readonly=False,
    )
    message = fields.Text(string="Message")

    valid_until = fields.Date(string="Valid Until")
    reminders = fields.Boolean(string="Reminders", default=False)
    hide_certificate = fields.Boolean(
        string="Hide certificate key on pages", default=False,
    )

    @api.depends("template_id")
    def _compute_subject(self):
        for rec in self:
            rec.subject = (
                "Signature Request - %s" % (rec.template_id.name or "")
                if rec.template_id else ""
            )

    def _create_request(self, state="sent"):
        self.ensure_one()
        return self.env["sign.request"].create({
            "template_id": self.template_id.id,
            "valid_until": self.valid_until,
            "state": state,
            "signer_ids": [(0, 0, {
                "partner_id": self.signer_id.id,
                "state": state if state in ("sent", "signed") else "draft",
            })],
        })

    def action_sign_now(self):
        request = self._create_request("sent")
        return {
            "type": "ir.actions.act_url",
            "url": "/sign/document/%d" % request.id,
            "target": "self",
        }

    def action_send(self):
        request = self._create_request("sent")

        # Send a simple email notification (best-effort)
        if self.signer_id and self.signer_id.email:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            url = "%s/sign/document/%d" % (base_url, request.id)
            try:
                self.env["mail.mail"].sudo().create({
                    "subject": self.subject or _("Signature Request"),
                    "body_html": (self.message or "") +
                                 "<br/><br/>" +
                                 _("<a href='%s'>Click here to sign the document</a>") % url,
                    "email_to": self.signer_id.email,
                }).send()
            except Exception:
                pass

        return {"type": "ir.actions.act_window_close"}


class SignShareWizard(models.TransientModel):
    _name = "sign.share.wizard"
    _description = "Share Document Wizard"

    template_id = fields.Many2one(
        "sign.template", string="Template", required=True, readonly=True,
    )

    share_link = fields.Char(
        string="Share Link", compute="_compute_share_link", store=True,
    )
    valid_until = fields.Date(string="Valid Until")
    is_shared = fields.Boolean(string="Is Shared", default=True)

    @api.depends("template_id")
    def _compute_share_link(self):
        for rec in self:
            if not rec.template_id:
                rec.share_link = ""
                continue
            token = uuid.uuid4().hex
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            rec.share_link = "%s/sign/document/share/%s/%s" % (
                base_url, rec.template_id.id, token,
            )

    def action_stop_sharing(self):
        self.ensure_one()
        self.is_shared = False
        return {"type": "ir.actions.act_window_close"}

    def action_close(self):
        return {"type": "ir.actions.act_window_close"}
