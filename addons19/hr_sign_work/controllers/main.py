from odoo import http
from odoo.http import request


class SignPDFController(http.Controller):

    @http.route(
        ['/sign/pdf_preview/<int:template_id>'],
        type='http',
        auth='user',
        website=False
    )
    def pdf_preview(self, template_id, **kwargs):
        template = request.env['sign.template'].sudo().browse(template_id)

        if not template.exists():
            return request.not_found()

        # agar PDF uploaded hai aur attachment nahi bana to auto create karo
        if template.document and not template.attachment_id:
            attachment = request.env['ir.attachment'].sudo().create({
                'name': template.document_name or 'document.pdf',
                'type': 'binary',
                'datas': template.document,
                'res_model': 'sign.template',
                'res_id': template.id,
                'mimetype': 'application/pdf',
            })
            template.attachment_id = attachment.id

        # agar attachment bhi nahi mila
        if not template.attachment_id:
            return request.make_response(
                """
                <html>
                    <body style="font-family: Arial; text-align:center; padding-top:100px;">
                        <h3>No PDF uploaded yet</h3>
                    </body>
                </html>
                """,
                headers=[('Content-Type', 'text/html')]
            )

        pdf_url = "/web/content/%s?download=false" % template.attachment_id.id

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PDF Preview</title>
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    background: #525659;
                    overflow: hidden;
                }}

                iframe {{
                    width: 100%;
                    height: 100vh;
                    border: none;
                    background: white;
                }}
            </style>
        </head>
        <body>
            <iframe src="{pdf_url}"></iframe>
        </body>
        </html>
        """

        return request.make_response(
            html,
            headers=[('Content-Type', 'text/html')]
        )