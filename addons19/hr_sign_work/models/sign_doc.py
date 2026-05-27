from odoo import models, fields, api


class SignDoc(models.Model):
    _name = "sign.doc"
    _description = "Sign Document"
    _order = "write_date desc"

    name = fields.Char(
        string="Document Name",
        required=True,
        default="Untitled Document",
    )

    content = fields.Html(
        string="Content",
        sanitize=False,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        readonly=True,
    )

    tag_ids = fields.Many2many("sign.tag", string="Tags")

    last_shared = fields.Datetime(string="Last Shared", readonly=True)

    shared_with_ids = fields.Many2many(
        "res.partner",
        "sign_doc_partner_rel", "doc_id", "partner_id",
        string="Shared With",
    )

    def action_share(self):
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        share_link = "%s/odoo/action-%d/%d" % (
            base_url,
            self.env.ref("hr_sign_work.action_sign_doc").id,
            self.id,
        )
        self.last_shared = fields.Datetime.now()
        return {
            "type": "ir.actions.act_window",
            "name": "Share Document",
            "res_model": "sign.doc.share.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_doc_id": self.id,
                "default_share_link": share_link,
            },
        }


class SignDocShareWizard(models.TransientModel):
    _name = "sign.doc.share.wizard"
    _description = "Share Document Wizard"

    doc_id = fields.Many2one("sign.doc", string="Document", readonly=True)
    share_link = fields.Char(string="Share Link", readonly=True)

    partner_ids = fields.Many2many(
        "res.partner",
        "sign_doc_share_wizard_partner_rel", "wizard_id", "partner_id",
        string="Share With",
    )

    note = fields.Text(
        string="Message",
        default="Please find the document link below.",
    )

    def action_done(self):
        if self.doc_id and self.partner_ids:
            for partner in self.partner_ids:
                self.doc_id.shared_with_ids = [(4, partner.id)]
            self.doc_id.last_shared = fields.Datetime.now()
        return {"type": "ir.actions.act_window_close"}
