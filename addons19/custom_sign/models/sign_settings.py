from odoo import models, fields


class SignConfigSettings(models.TransientModel):
    _name = "custom.sign.config.settings"
    _description = "Sign Configuration Settings"

    sign_default_terms = fields.Boolean(
        string="Sign Default Terms & Conditions",
        default=lambda self: self._get_param("custom_sign.sign_default_terms"),
    )

    sign_manage_template_access = fields.Boolean(
        string="Manage template access",
        default=lambda self: self._get_param("custom_sign.sign_manage_template_access"),
    )

    sign_aadhaar = fields.Boolean(
        string="Sign with Aadhaar eSign",
        default=lambda self: self._get_param("custom_sign.sign_aadhaar"),
    )

    def _get_param(self, key):
        val = self.env["ir.config_parameter"].sudo().get_param(key, "False")
        return val == "True"

    def action_save(self):
        self.ensure_one()
        set_param = self.env["ir.config_parameter"].sudo().set_param
        set_param("custom_sign.sign_default_terms", str(self.sign_default_terms))
        set_param("custom_sign.sign_manage_template_access",
                  str(self.sign_manage_template_access))
        set_param("custom_sign.sign_aadhaar", str(self.sign_aadhaar))
        return {"type": "ir.actions.act_window_close"}
