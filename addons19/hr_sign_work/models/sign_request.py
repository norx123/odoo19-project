import base64
import io
import logging
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SignRequest(models.Model):
    _name = "sign.request"
    _description = "Sign Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    # =====================================================
    # IDENTITY
    # =====================================================

    template_id = fields.Many2one(
        "sign.template", string="Template",
        required=True, ondelete="cascade",
    )

    name = fields.Char(
        string="Document Name",
        related="template_id.name",
        store=True, readonly=False,
    )

    document = fields.Binary(
        string="PDF Document",
        related="template_id.document",
        readonly=True,
    )

    document_name = fields.Char(
        string="File Name",
        related="template_id.document_name",
        readonly=True,
    )

    # =====================================================
    # PEOPLE
    # =====================================================

    sent_by = fields.Many2one(
        "res.users", string="Sent By",
        default=lambda self: self.env.user,
    )

    signer_ids = fields.One2many(
        "sign.request.signer", "request_id", string="Signers",
    )

    signer_partner_ids = fields.Many2many(
        "res.partner", string="Signer Partners",
        compute="_compute_signer_partner_ids", store=False,
    )

    tag_ids = fields.Many2many("sign.tag", string="Tags")

    # =====================================================
    # FIELDS (placed positions copied from template at creation,
    # then filled in by signers)
    # =====================================================

    sign_item_ids = fields.One2many(
        "sign.item", "request_id", string="Sign Items",
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
    ], string="Status", default="draft", tracking=True)

    date = fields.Date(string="Date", default=fields.Date.today)
    valid_until = fields.Date(string="Valid Until")

    signed_pdf = fields.Binary(
        string="Signed PDF", attachment=True, readonly=True,
    )
    signed_pdf_name = fields.Char(string="Signed PDF Name")

    # =====================================================
    # COMPUTES
    # =====================================================

    @api.depends("signer_ids.partner_id")
    def _compute_signer_partner_ids(self):
        for rec in self:
            rec.signer_partner_ids = rec.signer_ids.mapped("partner_id")

    def _update_signer_state(self, state_value):
        for rec in self:
            for signer in rec.signer_ids:
                signer.state = state_value
                signer.signing_date = (
                    fields.Date.today() if state_value == "signed" else False
                )

    # =====================================================
    # CREATE: copy field positions from the template and
    # auto-add the current user as signer if none provided
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for rec in records:
            # Default signer
            if not rec.signer_ids:
                self.env["sign.request.signer"].create({
                    "request_id": rec.id,
                    "partner_id": self.env.user.partner_id.id,
                    "state": "draft",
                })

            # Copy template's placed fields into this request
            if rec.template_id and not rec.sign_item_ids:
                for tpl_item in rec.template_id.sign_item_ids:
                    self.env["sign.item"].create({
                        "request_id": rec.id,
                        "type_id": tpl_item.type_id.id,
                        "placeholder": tpl_item.placeholder,
                        "alignment": tpl_item.alignment,
                        "read_only": tpl_item.read_only,
                        "required": tpl_item.required,
                        "page": tpl_item.page,
                        "pos_x": tpl_item.pos_x,
                        "pos_y": tpl_item.pos_y,
                        "width": tpl_item.width,
                        "height": tpl_item.height,
                        "responsible_role": tpl_item.responsible_role,
                    })

        return records

    # =====================================================
    # JSON / RPC HELPERS USED BY THE SIGNING UI
    # =====================================================

    def get_sign_data(self):
        """Return everything the signer UI needs to render."""
        self.ensure_one()
        items = []
        for it in self.sign_item_ids:
            items.append({
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
                "value": it.value or "",
                "has_signature": bool(it.signature_data),
            })
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "pdf_url": (
                "/web/content/%d?download=false" % self.template_id.attachment_id.id
                if self.template_id.attachment_id else ""
            ),
            "items": items,
        }

    def sign_submit(self, filled_items):
        """
        Called from the signer UI when the user clicks Sign.
        `filled_items` = [
            {id, value, signature_data (data:image/png;base64 or empty)}
        ]
        """
        self.ensure_one()

        if self.state not in ("sent", "draft"):
            raise UserError(_("This document is not open for signing."))

        # Validate & save filled values
        items_by_id = {it.id: it for it in self.sign_item_ids}
        for filled in filled_items or []:
            item = items_by_id.get(int(filled.get("id") or 0))
            if not item:
                continue

            vals = {}
            val = filled.get("value")
            if val is not None:
                vals["value"] = val

            sig_data = filled.get("signature_data") or ""
            if sig_data:
                # Strip the data-URL prefix if present
                if "," in sig_data:
                    sig_data = sig_data.split(",", 1)[1]
                vals["signature_data"] = sig_data

            if vals:
                item.write(vals)

        # Check mandatory fields are filled
        missing = []
        for it in self.sign_item_ids:
            if not it.required:
                continue
            if it.item_type in ("signature", "initial", "stamp"):
                if not it.signature_data:
                    missing.append(it.name)
            elif it.item_type == "checkbox":
                # Checkbox is allowed to be unchecked unless mandatory
                if (it.value or "").lower() not in ("1", "true", "on", "yes"):
                    missing.append(it.name)
            else:
                if not (it.value or "").strip():
                    missing.append(it.name)

        if missing:
            raise UserError(
                _("Please fill the required fields: %s") % ", ".join(missing)
            )

        # Generate the signed PDF
        signed_pdf_bytes = self._generate_signed_pdf()
        if signed_pdf_bytes:
            base_name = self.document_name or (self.name or "document") + ".pdf"
            if not base_name.lower().endswith(".pdf"):
                base_name += ".pdf"
            signed_name = base_name.rsplit(".pdf", 1)[0] + "_signed.pdf"

            self.write({
                "signed_pdf": base64.b64encode(signed_pdf_bytes),
                "signed_pdf_name": signed_name,
                "state": "signed",
            })
        else:
            self.state = "signed"

        self._update_signer_state("signed")
        return {"ok": True, "request_id": self.id}

    # =====================================================
    # PDF STAMPING - merges field values onto the original PDF
    # =====================================================

    def _generate_signed_pdf(self):
        """
        Read original PDF, overlay each filled field at its (pos_x, pos_y)
        on its page, and return the merged PDF as bytes.
        """
        self.ensure_one()

        if not self.template_id.document:
            return None

        try:
            from PyPDF2 import PdfReader, PdfWriter
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.utils import ImageReader
        except ImportError:
            _logger.warning(
                "PyPDF2 or reportlab not installed; cannot stamp signed PDF."
            )
            return None

        pdf_bytes = base64.b64decode(self.template_id.document)
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()

        # Group items by page (1-indexed)
        items_by_page = {}
        for it in self.sign_item_ids:
            items_by_page.setdefault(it.page or 1, []).append(it)

        for page_idx, page in enumerate(reader.pages, start=1):
            page_items = items_by_page.get(page_idx, [])

            if not page_items:
                writer.add_page(page)
                continue

            # Page geometry
            mediabox = page.mediabox
            try:
                page_w = float(mediabox.width)
                page_h = float(mediabox.height)
            except AttributeError:
                # very old PyPDF2
                page_w = float(mediabox[2] - mediabox[0])
                page_h = float(mediabox[3] - mediabox[1])

            # Build overlay PDF
            overlay_buf = io.BytesIO()
            c = rl_canvas.Canvas(overlay_buf, pagesize=(page_w, page_h))

            for it in page_items:
                self._draw_item_on_canvas(c, it, page_w, page_h)

            c.save()
            overlay_buf.seek(0)

            overlay_reader = PdfReader(overlay_buf)
            overlay_page = overlay_reader.pages[0]
            page.merge_page(overlay_page)
            writer.add_page(page)

        out_buf = io.BytesIO()
        writer.write(out_buf)
        return out_buf.getvalue()

    def _draw_item_on_canvas(self, c, it, page_w, page_h):
        """Draw one sign item onto the reportlab canvas (which is PDF
        coordinates: origin bottom-left)."""
        from reportlab.lib.utils import ImageReader

        # Convert percent-based positions into PDF points.
        # In the editor, pos_x/pos_y are % of the page width/height from
        # the top-left. PDF uses bottom-left origin, so flip Y.
        x = (it.pos_x / 100.0) * page_w
        w = (it.width / 100.0) * page_w
        h = (it.height / 100.0) * page_h
        y_top = (it.pos_y / 100.0) * page_h
        y = page_h - y_top - h  # bottom-left of the box in PDF coords

        item_type = it.item_type

        try:
            if item_type in ("signature", "initial", "stamp") and it.signature_data:
                try:
                    img_bytes = base64.b64decode(it.signature_data)
                    img = ImageReader(io.BytesIO(img_bytes))
                    c.drawImage(
                        img, x, y, width=w, height=h,
                        mask="auto", preserveAspectRatio=True,
                    )
                except Exception as e:
                    _logger.warning("Could not draw signature image: %s", e)

            elif item_type == "checkbox":
                checked = (it.value or "").lower() in ("1", "true", "on", "yes")
                # box outline
                c.setLineWidth(1)
                box_size = min(w, h)
                bx = x
                by = y + (h - box_size) / 2.0
                c.rect(bx, by, box_size, box_size, stroke=1, fill=0)
                if checked:
                    c.setLineWidth(2)
                    c.line(bx + 2, by + box_size - 2, bx + box_size - 2, by + 2)
                    c.line(bx + 2, by + 2, bx + box_size - 2, by + box_size - 2)

            elif item_type == "strikethrough":
                c.setLineWidth(1.5)
                mid_y = y + h / 2.0
                c.line(x, mid_y, x + w, mid_y)

            else:
                # Text-like fields
                text_value = self._format_item_value(it)
                if not text_value:
                    continue

                font_size = max(8, min(14, int(h * 0.55)))
                c.setFont("Helvetica", font_size)

                if it.alignment == "center":
                    c.drawCentredString(x + w / 2.0, y + h / 2.0 - font_size / 3.0, text_value)
                elif it.alignment == "right":
                    c.drawRightString(x + w, y + h / 2.0 - font_size / 3.0, text_value)
                else:
                    c.drawString(x + 2, y + h / 2.0 - font_size / 3.0, text_value)

        except Exception as e:
            _logger.warning("Failed to render sign item %s: %s", it.id, e)

    def _format_item_value(self, it):
        val = (it.value or "").strip()
        if val:
            return val
        if it.item_type == "date":
            return date.today().strftime("%Y-%m-%d")
        return ""

    # =====================================================
    # ACTIONS
    # =====================================================

    def action_send(self):
        for rec in self:
            rec.state = "sent"
            rec._update_signer_state("sent")
        return True

    def action_open_sign(self):
        """Open the signing UI in the same tab."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": "/sign/document/%d" % self.id,
            "target": "self",
        }

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"
            rec._update_signer_state("draft")
        return True

    def action_resend(self):
        for rec in self:
            rec.state = "sent"
            rec._update_signer_state("sent")
        return True

    def action_download(self):
        """Download signed PDF if available, else the original."""
        self.ensure_one()

        if self.signed_pdf or self.template_id.document:
            return {
                "type": "ir.actions.act_url",
                "url": "/sign/download/%d" % self.id,
                "target": "self",
            }

        raise UserError(_("No document available to download."))


# =========================================================
# SIGNER
# =========================================================

class SignRequestSigner(models.Model):
    _name = "sign.request.signer"
    _description = "Sign Request Signer"
    _order = "id asc"

    request_id = fields.Many2one(
        "sign.request", string="Request",
        required=True, ondelete="cascade",
    )

    partner_id = fields.Many2one(
        "res.partner", string="Signer", required=True,
    )

    state = fields.Selection([
        ("draft", "Waiting"),
        ("sent", "Sent"),
        ("signed", "Signed"),
        ("refused", "Refused"),
    ], string="Status", default="draft")

    signing_date = fields.Date(string="Signing Date")
