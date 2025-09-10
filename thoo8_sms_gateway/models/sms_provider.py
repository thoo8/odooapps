from odoo import models, fields, api, _
from odoo.exceptions import UserError, _logger
import json, requests
from odoo import api, SUPERUSER_ID


class SmsProviderField(models.Model):
    _name = "thoo8.sms.provider.field"
    _description = "Provider Field"

    provider_id = fields.Many2one("thoo8.sms.provider", string="Provider", required=True)
    field_name = fields.Char("Field Name", required=True, help="Name used in Python")
    api_key_name = fields.Char("API Variable Name", required=True, help="Actual variable name required by the provider")
    value = fields.Char("Default Value", help="Value to send for this variable")


class SmsProvider(models.Model):
    _name = "thoo8.sms.provider"
    _description = "SMS Provider"

    name = fields.Char("Provider Name", required=True)
    api_url = fields.Char("API URL", required=True)
    active = fields.Boolean(default=True)
    provider_fields = fields.One2many("thoo8.sms.provider.field", "provider_id", string="Provider Fields")
    sucess_code = fields.Text("Sucess Code", required=True, help="add , bettwen the numbers if it more than one number")

    recipient_number_field = fields.Char(
        required=True,
        string="Recipient Number Variable",
        help="The actual variable name to send the recipient number to the API (e.g., numbers, to)"
    )
    message_field = fields.Char(
        required=True,
        string="Message Variable",
        help="The actual variable name to send the message text to the API (e.g., msg, message)"
    )
    extra_params = fields.Text("Extra Parameters (JSON)", help="Add additional dynamic variables in JSON format")
    test_number = fields.Char("Test Number", help="Phone number in international format, e.g., 9665XXXXXXX")
    success_code = fields.Char(
        required=True,
        string="Success Code",
        help="Add comma between numbers if there are multiple codes, e.g., 1,200,M0000"
    )
    success_code_var = fields.Char(
        required=True,
        string="Code Variable",
        help="The variable name in the response that holds the code, e.g., code"
    )

    def action_open_test_wizard(self):
        self.ensure_one()
        return {
            "name": _("Test SMS"),
            "type": "ir.actions.act_window",
            "res_model": "thoo8.sms.test.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_provider_id": self.id,
            }
        }

    def _log_sms(self, phone, provider, message, status="pending", code=None, response=None):
        """Fire-and-forget SMS logging (Isolated from the current process)."""
        provider.ensure_one()

        # open new cursor
        with provider.pool.cursor() as new_cr:
            try:
                env2 = api.Environment(new_cr, SUPERUSER_ID, {})
                env2['thoo8.sms.log'].create({
                    'provider_id': provider.id,
                    'to': phone,
                    'message': message,
                    'status': status,
                    'code': code,
                    'response_text': response or "",
                })
                new_cr.commit()  # يثبت فقط سجل الـ log
            except Exception as e:
                new_cr.rollback()
                _logger.error("Failed to save SMS log: %s", e)

    def send_sms(self, phone, message, provider=None, test_mode=False):
        """Send SMS via provider, fallback to default provider if not provided"""

        # إذا ما تم تمرير provider → استخدم المزود الافتراضي من الإعدادات
        if not provider:
            provider = self.env['ir.config_parameter'].sudo().get_param("thoo8_sms.default_provider_id")
            if not provider:
                raise UserError("لم يتم تحديد مزود الرسائل الافتراضي")
            provider = self.env['thoo8.sms.provider'].browse(int(provider))

        payload = {}

        # إضافة الحقول الديناميكية من provider_fields
        for f in provider.provider_fields:
            payload[f.api_key_name] = f.value

        # إضافة أي متغيرات إضافية من extra_params (JSON)
        if hasattr(provider, 'extra_params') and provider.extra_params:
            try:
                extra = json.loads(provider.extra_params)
                payload.update(extra)
            except Exception:
                raise UserError("Invalid JSON in Extra Parameters")

        # أرقام المستلمين حسب متغيرات المزود
        if provider.recipient_number_field:
            payload[provider.recipient_number_field] = phone
        else:
            payload['numbers'] = phone

        # نص الرسالة حسب متغيرات المزود
        if provider.message_field:
            payload[provider.message_field] = message
        else:
            payload['msg'] = message

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(provider.api_url, data=json.dumps(payload), headers=headers, timeout=15)
            try:
                response_json = response.json()
            except Exception:
                response_json = {"error": response.text}

            # --- التحقق من كود النجاح ---
            success_status = "Failed"
            if provider.success_code_var and provider.success_code:
                success_codes = [s.strip() for s in provider.success_code.split(",")]
                resp_code = str(response_json.get(provider.success_code_var, ""))
                if resp_code in success_codes:
                    success_status = "Success"
            print(provider)
            print(provider.id)

            # تسجيل النتيجة
            self._log_sms(
                phone,
                provider,
                message,
                status=success_status,
                code=response.status_code,
                response=json.dumps(response_json)
            )

            return response_json

        except requests.exceptions.RequestException as e:
            self._log_sms(phone, provider, message, status='Failed', response=str(e))
            raise UserError(f"Failed to send SMS: {str(e)}")