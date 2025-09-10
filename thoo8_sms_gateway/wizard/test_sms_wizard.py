from odoo import models, fields, api, _
from odoo.exceptions import UserError, _logger
from jinja2 import Environment, BaseLoader

import json


class SmsTestWizard(models.TransientModel):
    _name = "thoo8.sms.test.wizard"
    _description = "SMS Test Wizard"

    provider_id = fields.Many2one("thoo8.sms.provider", string="Provider", required=True)
    template_id = fields.Many2one("thoo8.sms.template", string="SMS Template", required=True)
    template_model = fields.Many2one("ir.model", string="Template Module", compute="_compute_template_model")
    test_number = fields.Char("Test Number", required=True,
                              default=lambda self: self.env.user.partner_id.phone or self.env.user.partner_id.mobile or '')

    @api.depends('template_id')
    def _compute_template_model(self):
        for rec in self:
            rec.template_model = rec.template_id.model_id.id if rec.template_id else False

    def action_send_test_sms(self):
        self.ensure_one()

        # جلب أول سجل من الموديل المرتبط بالقالب
        record = None
        if self.template_id.model_id:
            record = self.env[self.template_id.model_id.model].search([], limit=1)

        # إنشاء بيئة Jinja2 مع context إضافي
        env = Environment(loader=BaseLoader())
        context = {
            "object": record,
            "user": self.env.user,
            "company": self.env.company,
        }

        try:
            template = env.from_string(self.template_id.body or "")
            message = template.render(context)
        except Exception as e:
            _logger.error("خطأ في توليد الرسالة من القالب: %s", str(e))
            raise UserError(_("خطأ في توليد الرسالة من القالب:\n%s") % str(e))

        if not message.strip():
            raise UserError(_("الناتج من القالب فارغ."))

        # التحقق أن المزود عنده method send_sms
        if not hasattr(self.provider_id, "send_sms"):
            raise UserError(_("مزود الرسائل المحدد لا يدعم إرسال SMS."))

        # إرسال الرسالة عبر المزود
        response = self.provider_id.send_sms(self.test_number, message, self.provider_id)
        _logger.info("SMS Test sent to %s via %s. Response: %s",
                     self.test_number, self.provider_id.name, response)

        # تنسيق الرد بشكل JSON مرتب
        try:
            formatted = json.dumps(response, indent=2, ensure_ascii=False)
        except Exception:
            formatted = str(response)

        # احصل على قيمة الكود من الرد
        response_code = response.get(self.provider_id.success_code_var)
        print(response_code)
        # تحويل حقل success_code لمصفوفة أرقام
        codes = [x.strip() for x in (self.provider_id.success_code or "").split(",")]

        # تحقق
        result_code = None
        if response_code in codes:
            result_code = "بنجاح ✅"
        else:
            result_code = "وفشل التسليم ❌"

        raise UserError(f" تم إرسال الرسالة التجريبية. {result_code} .\nرد المزود:\n{formatted}")
