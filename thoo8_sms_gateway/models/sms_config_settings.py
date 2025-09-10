from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_default_provider_id = fields.Many2one(
        'thoo8.sms.provider',
        string="Default SMS Provider",
        config_parameter="thoo8_sms.default_provider_id"
    )
    sms_auto_send = fields.Boolean(
        string="Enable Auto Send",
        config_parameter="thoo8_sms.auto_send"
    )
    sms_fallback_message = fields.Char(
        string="Fallback Message",
        config_parameter="thoo8_sms.fallback_message",
        help="رسالة افتراضية تُستخدم إذا فشل إرسال الرسالة."
    )
