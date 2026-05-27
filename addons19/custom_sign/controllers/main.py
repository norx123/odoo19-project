import base64
import json

from odoo import http
from odoo.http import request


class SignWorkController(http.Controller):

    # ---------------------------------------------------------
    # PDF PREVIEW (used by the editor iframe fallback)
    # ---------------------------------------------------------

    @http.route(
        ["/sign/pdf_preview/<int:template_id>"],
        type="http", auth="user", website=False,
    )
    def pdf_preview(self, template_id, **kwargs):
        template = request.env["custom.sign.template"].sudo().browse(template_id)

        if not template.exists():
            return request.not_found()

        # Auto-create attachment if PDF was uploaded but attachment missing
        if template.document and not template.attachment_id:
            attachment = request.env["ir.attachment"].sudo().create({
                "name": template.document_name or "document.pdf",
                "type": "binary",
                "datas": template.document,
                "res_model": "custom.sign.template",
                "res_id": template.id,
                "mimetype": "application/pdf",
            })
            template.attachment_id = attachment.id

        if not template.attachment_id:
            return request.make_response(
                "<html><body style='font-family:Arial;"
                "text-align:center;padding-top:100px;'>"
                "<h3>No PDF uploaded yet</h3></body></html>",
                headers=[("Content-Type", "text/html")],
            )

        pdf_url = "/web/content/%s?download=false" % template.attachment_id.id

        html = (
            "<!DOCTYPE html><html><head><title>PDF Preview</title>"
            "<style>html,body{margin:0;padding:0;width:100%;height:100%;"
            "background:#525659;overflow:hidden}"
            "iframe{width:100%;height:100vh;border:none;background:#fff}"
            "</style></head><body>"
            "<iframe src='%s'></iframe>"
            "</body></html>" % pdf_url
        )
        return request.make_response(
            html, headers=[("Content-Type", "text/html")],
        )

    # ---------------------------------------------------------
    # SIGNING PAGE - this is where the signer actually signs
    # ---------------------------------------------------------

    @http.route(
        ["/sign/document/<int:request_id>"],
        type="http", auth="user", website=False,
    )
    def sign_document(self, request_id, **kwargs):
        sign_req = request.env["custom.sign.request"].sudo().browse(request_id)

        if not sign_req.exists():
            return request.not_found()

        # Ensure attachment exists for the PDF
        template = sign_req.template_id
        if template.document and not template.attachment_id:
            attachment = request.env["ir.attachment"].sudo().create({
                "name": template.document_name or "document.pdf",
                "type": "binary",
                "datas": template.document,
                "res_model": "custom.sign.template",
                "res_id": template.id,
                "mimetype": "application/pdf",
            })
            template.attachment_id = attachment.id

        pdf_url = (
            "/web/content/%d?download=false" % template.attachment_id.id
            if template.attachment_id else ""
        )

        already_signed = sign_req.state == "signed"

        # Render a standalone signing page (no Odoo chrome)
        html = SIGN_PAGE_TEMPLATE.format(
            request_id=sign_req.id,
            doc_name=(sign_req.name or "Document").replace("<", "&lt;"),
            pdf_url=pdf_url,
            already_signed=str(already_signed).lower(),
            download_url="/sign/download/%d" % sign_req.id,
        )

        return request.make_response(
            html, headers=[("Content-Type", "text/html; charset=utf-8")],
        )

    # ---------------------------------------------------------
    # DOWNLOAD SIGNED PDF
    # ---------------------------------------------------------

    @http.route(
        ["/sign/download/<int:request_id>"],
        type="http", auth="user",
    )
    def download_signed_pdf(self, request_id, **kwargs):
        sign_req = request.env["custom.sign.request"].sudo().browse(request_id)
        if not sign_req.exists():
            return request.not_found()

        if sign_req.signed_pdf:
            data = base64.b64decode(sign_req.signed_pdf)
            filename = sign_req.signed_pdf_name or "signed.pdf"
        elif sign_req.template_id.document:
            data = base64.b64decode(sign_req.template_id.document)
            filename = sign_req.document_name or "document.pdf"
        else:
            return request.not_found()

        return request.make_response(
            data,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Disposition",
                 "attachment; filename=\"%s\"" % filename),
            ],
        )

    # ---------------------------------------------------------
    # JSON: load sign data for the signing UI
    # ---------------------------------------------------------

    @http.route(
        ["/sign/data/<int:request_id>"],
        type="json", auth="user",
    )
    def sign_data(self, request_id, **kwargs):
        sign_req = request.env["custom.sign.request"].sudo().browse(request_id)
        if not sign_req.exists():
            return {"error": "not_found"}
        return sign_req.get_sign_data()

    # ---------------------------------------------------------
    # JSON: submit signed values + signature images
    # ---------------------------------------------------------

    @http.route(
        ["/sign/submit/<int:request_id>"],
        type="json", auth="user",
    )
    def sign_submit(self, request_id, items=None, **kwargs):
        sign_req = request.env["custom.sign.request"].sudo().browse(request_id)
        if not sign_req.exists():
            return {"error": "not_found"}
        return sign_req.sign_submit(items or [])


# =============================================================
# SIGNER PAGE TEMPLATE (kept short; JS does the heavy lifting)
# =============================================================

SIGN_PAGE_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <title>Sign - {doc_name}</title>
    <link rel="stylesheet" href="/web/static/lib/fontawesome/css/font-awesome.css"/>
    <style>
        body {{ margin:0; font-family: 'Segoe UI', Arial, sans-serif; background: #525659; }}
        #sign_topbar {{
            position: sticky; top:0; z-index:1000;
            background: #fff; padding: 10px 20px;
            border-bottom: 1px solid #ddd;
            display:flex; align-items:center; justify-content:space-between;
        }}
        #sign_topbar h2 {{ margin:0; font-size:16px; color:#333; }}
        #sign_topbar .btns button {{
            border:none; padding:8px 16px; border-radius:4px;
            font-weight:500; cursor:pointer; margin-left:8px;
        }}
        .btn-sign-primary {{ background:#875A7B; color:#fff; }}
        .btn-sign-primary:hover {{ background:#6e4866; }}
        .btn-sign-secondary {{ background:#e9ecef; color:#333; }}
        #sign_pdf_container {{
            padding: 20px; display:flex; flex-direction:column;
            align-items:center; min-height:calc(100vh - 60px);
        }}
        .sign_pdf_page {{
            position:relative; margin:10px auto; background:#fff;
            box-shadow:0 2px 12px rgba(0,0,0,0.3);
        }}
        .sign_field_placed {{
            position:absolute; background: rgba(255, 235, 153, 0.6);
            border: 2px dashed #d4a017; box-sizing:border-box;
            display:flex; align-items:center; justify-content:center;
            font-size:12px; color:#333; cursor:pointer;
            font-weight:500; text-align:center; overflow:hidden;
            border-radius:3px;
        }}
        .sign_field_placed.filled {{
            background: rgba(135, 211, 124, 0.35);
            border: 2px solid #2e8b57;
        }}
        .sign_field_placed:hover {{ background: rgba(255, 235, 153, 0.9); }}
        .sign_field_placed img {{ max-width:100%; max-height:100%; }}
        .sign_field_placed input, .sign_field_placed textarea {{
            border: none; background: transparent;
            width:100%; height:100%; padding:2px 4px;
            font-size: inherit; box-sizing: border-box;
            font-family: inherit;
        }}
        .sign_field_placed input:focus, .sign_field_placed textarea:focus {{
            outline: none; background: rgba(255,255,255,0.6);
        }}

        /* Signature modal */
        #sig_modal_backdrop {{
            display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5);
            z-index:2000; align-items:center; justify-content:center;
        }}
        #sig_modal {{
            background:#fff; padding:24px; border-radius:8px;
            min-width:480px; max-width:90vw;
            box-shadow:0 10px 40px rgba(0,0,0,0.3);
        }}
        #sig_modal h3 {{ margin: 0 0 12px; font-size:18px; }}
        #sig_canvas {{
            border:1px solid #ccc; background:#fafafa; cursor:crosshair;
            width:100%; touch-action:none; border-radius:4px;
        }}
        #sig_modal .sig_actions {{
            margin-top:16px; display:flex; gap:8px; justify-content:flex-end;
        }}
        #sig_modal button {{
            padding:8px 16px; border:none; border-radius:4px;
            cursor:pointer; font-weight:500;
        }}
        #sig_modal .btn-clear {{ background:#6c757d; color:#fff; }}
        #sig_modal .btn-cancel {{ background:#e9ecef; color:#333; }}
        #sig_modal .btn-confirm {{ background:#875A7B; color:#fff; }}

        /* Toast */
        #sign_toast {{
            position:fixed; top:80px; left:50%; transform:translateX(-50%);
            background:#dc3545; color:#fff; padding:10px 20px;
            border-radius:4px; z-index:3000; display:none;
            box-shadow:0 4px 12px rgba(0,0,0,0.2);
        }}
        #sign_toast.success {{ background:#28a745; }}
    </style>
</head>
<body>
    <div id="sign_topbar">
        <h2><i class="fa fa-file-text-o"></i> {doc_name}</h2>
        <div class="btns">
            <button class="btn-sign-secondary" onclick="window.history.back()">
                <i class="fa fa-arrow-left"></i> Back
            </button>
            <button id="btn_download" class="btn-sign-secondary"
                onclick="window.location.href='{download_url}'">
                <i class="fa fa-download"></i> Download
            </button>
            <button id="btn_sign" class="btn-sign-primary">
                <i class="fa fa-check"></i> Sign & Submit
            </button>
        </div>
    </div>

    <div id="sign_pdf_container"></div>

    <div id="sig_modal_backdrop">
        <div id="sig_modal">
            <h3>Draw your signature</h3>
            <canvas id="sig_canvas" width="600" height="200"></canvas>
            <div class="sig_actions">
                <button class="btn-clear" onclick="window._signerClearCanvas()">Clear</button>
                <button class="btn-cancel" onclick="window._signerCloseSigModal()">Cancel</button>
                <button class="btn-confirm" onclick="window._signerConfirmSig()">Adopt &amp; Sign</button>
            </div>
        </div>
    </div>

    <div id="sign_toast"></div>

    <script>
        window.SIGN_REQUEST_ID = {request_id};
        window.SIGN_PDF_URL = "{pdf_url}";
        window.SIGN_ALREADY_SIGNED = {already_signed};
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script src="/custom_sign/static/src/js/sign_signer_page.js"></script>
</body>
</html>
"""
