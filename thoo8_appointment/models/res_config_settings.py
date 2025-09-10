from odoo import models, fields, api, _, SUPERUSER_ID


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stop_all_bookings = fields.Boolean(
        string="Stop Receiving Appointment Bookings",
        config_parameter='thoo8.appointment.request.stop_all_bookings',
        help="If enabled, no new appointment bookings will be accepted."
    )
    stop_when_reached = fields.Boolean(
        string="Stop Accepting Appointments When Maximum Reached",
        config_parameter='thoo8.appointment.request.stop_when_reached',
        help="If enabled, bookings will stop once the allowed number is reached."
    )
    max_daily_bookings = fields.Integer(
        string="Maximum Daily Bookings",
        config_parameter='thoo8.appointment.request.max_daily_bookings',
        default=50,
        help="The allowed number of daily bookings through the portal."
    )
    enable_mobile_verification = fields.Boolean(
        string="Enable Mobile Verification",
        config_parameter='thoo8.appointment.request.enable_mobile_verification',
        help="If enabled, customers must verify their mobile number before booking an appointment."
    )
    enable_id_card_verification = fields.Boolean(
        string="Enable ID Card Verification",
        config_parameter='thoo8.appointment.request.enable_id_card_verification',
        help="If enabled, the system will enforce ID card verification during the appointment booking."
    )

    def set_default_config(cr, registry):
        env = api.Environment(cr, SUPERUSER_ID, {})
        params = env['ir.config_parameter'].sudo()

        if not params.get_param('thoo8.appointment.request.enable_id_card_verification'):
            params.set_param('thoo8.appointment.request.enable_id_card_verification', True)

    @api.onchange('enable_mobile_verification')
    def _check_sms_gateway_dependency(self):
        """ Ensure SMS Gateway module is installed and a provider is selected """
        if self.enable_mobile_verification:
            # تحقق من وجود الموديول
            module = self.env['ir.module.module'].search([('name', '=', 'thoo8_sms_gateway')], limit=1)
            if not module or module.state != 'installed':
                self.enable_mobile_verification = False
                return {
                    'warning': {
                        'title': _("Dependency Error"),
                        'message': _(
                            "You must install and activate the 'THOO8 SMS Gateway' module before enabling mobile verification."),
                    }
                }

            # تحقق من اختيار مزود SMS
            provider_id = self.env['ir.config_parameter'].sudo().get_param("thoo8_sms.default_provider_id")
            if not provider_id:
                self.enable_mobile_verification = False
                return {
                    'warning': {
                        'title': _("Missing SMS Provider"),
                        'message': _(
                            "Please select a default SMS Provider in the SMS Gateway settings before enabling mobile verification."),
                    }
                }
