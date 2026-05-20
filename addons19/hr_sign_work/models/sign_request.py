from odoo import models, fields, api


class SignRequest(models.Model):
    _name = "sign.request"
    _description = "Sign Request"
    _order = "create_date desc"


    # =====================================================
    # BASIC INFO
    # =====================================================

    template_id = fields.Many2one(
        "sign.template",
        string="Template",
        required=True,
        ondelete="cascade"
    )

    name = fields.Char(
        string="Document Name",
        related="template_id.name",
        store=True,
        readonly=False
    )

    document = fields.Binary(
        string="PDF Document",
        related="template_id.document",
        readonly=True
    )

    document_name = fields.Char(
        string="Document Name",
        related="template_id.document_name",
        readonly=True
    )


    # =====================================================
    # USERS
    # =====================================================

    sent_by = fields.Many2one(
        "res.users",
        string="Sent By",
        default=lambda self: self.env.user
    )

    signer_ids = fields.One2many(
        "sign.request.signer",
        "request_id",
        string="Signers"
    )

    signer_partner_ids = fields.Many2many(
        "res.partner",
        string="Signers",
        compute="_compute_signer_partner_ids",
        store=False,
    )

    tag_ids = fields.Many2many(
        "sign.tag",
        string="Tags",
    )


    # =====================================================
    # STATUS
    # =====================================================

    state = fields.Selection([
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("signed", "Signed"),
        ("refused", "Refused"),
        ("cancel", "Cancelled"),
    ],
        string="Status",
        default="draft",
        tracking=True
    )


    # =====================================================
    # DATES
    # =====================================================

    date = fields.Date(
        string="Date",
        default=fields.Date.today
    )


    # =====================================================
    # COMPUTE
    # =====================================================

    @api.depends("signer_ids.partner_id")
    def _compute_signer_partner_ids(self):
        for rec in self:
            rec.signer_partner_ids = rec.signer_ids.mapped("partner_id")

    def _update_signer_state(self, state_value):
        for rec in self:
            for signer in rec.signer_ids:
                signer.state = state_value

                if state_value == "signed":
                    signer.signing_date = fields.Date.today()
                else:
                    signer.signing_date = False


    # =====================================================
    # ACTIONS
    # =====================================================

    def action_send(self):
        for rec in self:
            rec.state = "sent"
            rec._update_signer_state("sent")

        return True


    def action_sign(self):
        for rec in self:
            rec.state = "signed"
            rec._update_signer_state("signed")

        return True


    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"
            rec._update_signer_state("draft")

        return True


    def action_download(self):
        self.ensure_one()

        if not self.template_id.attachment_id:
            return False

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % (
                self.template_id.attachment_id.id
            ),
            "target": "self",
        }

    def action_resend(self):
        for rec in self:
            rec.state = "sent"
            rec._update_signer_state("sent")
        return True


    # =====================================================
    # DEFAULT SIGNER AUTO CREATE
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            if not rec.signer_ids:
                self.env["sign.request.signer"].create({
                    "request_id": rec.id,
                    "partner_id": self.env.user.partner_id.id,
                    "state": "draft",
                })

        return records


# =====================================================
# SIGN REQUEST SIGNER
# =====================================================

class SignRequestSigner(models.Model):
    _name = "sign.request.signer"
    _description = "Sign Request Signer"
    _order = "id asc"


    request_id = fields.Many2one(
        "sign.request",
        string="Request",
        required=True,
        ondelete="cascade"
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Signer",
        required=True
    )

    state = fields.Selection([
        ("draft", "Waiting"),
        ("sent", "Sent"),
        ("signed", "Signed"),
        ("refused", "Refused"),
    ],
        string="Status",
        default="draft"
    )

    signing_date = fields.Date(
        string="Signing Date"
    )