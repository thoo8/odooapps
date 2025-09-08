from odoo import models, fields, api, _
from odoo.exceptions import UserError


# سيتم استخدام هذا النموذج لكافة الاعدادات وفي العرض يتم عرض فقط كل اعداد على حدا مثلا الرسائل في نموذج مستقل ...الخ
class AppointmentSettingsSMS(models.Model):
    _name = 'thoo8.appointment.settings_sms'
    _description = 'SMS Appointment Settings'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Settings Title", default="SMS Settings")
    enable_create_sms = fields.Boolean(string="Enable sending SMS when an appointment request is created", default=True)
    create_sms_template = fields.Text(
        string="Creation Message",
        default="Your appointment request has been successfully received.\nOrder Number: {order_number}"
    )

    enable_confirm_sms = fields.Boolean(string="Enable confirmation SMS when scheduled by staff", default=False)
    confirm_sms_template = fields.Text(
        string="Confirmation Message",
        default="Your appointment has been confirmed.\nOrder Number: {order_number}\nDate: {date}\nTime: {time}"
    )

    enable_portal_confirm_sms = fields.Boolean(
        string="Enable confirmation SMS when the customer selects the appointment through the portal",
        default=True
    )
    confirm_portal_sms_template = fields.Text(
        string="Portal Confirmation Message",
        default="Your appointment has been confirmed.\nOrder Number: {order_number}\nDate: {date}\nTime: {time}"
    )

    enable_cancel_sms = fields.Boolean(string="Enable cancellation SMS", default=False)
    cancel_sms_template = fields.Text(
        string="Cancellation Message",
        default="Your appointment request has been cancelled.\nOrder Number: {order_number}"
    )



    @api.model
    def create(self, vals):
        if self.search_count([]) >= 1:
            raise UserError(_("More than one settings record cannot be created."))
        return super(AppointmentSettingsSMS, self).create(vals)

    @api.model
    def get_settings_sms(self):
        settings = self.search([], limit=1)
        if not settings:
            settings = self.create({})
        return settings

    def reset_defaults(self):
        self.write({
            'enable_create_sms': True,
            'enable_confirm_sms': False,
            'enable_portal_confirm_sms': True,
            'enable_cancel_sms': False,
            'create_sms_template': 'تم استلام طلب الموعد بنجاح.\nرقم الطلب: {order_number}',
            'confirm_sms_template': 'تم تأكيد موعدكم.\nرقم الطلب: {order_number}\nالتاريخ: {date}\nالساعة: {time}',
            'confirm_portal_sms_template': 'تم تأكيد موعدكم.\nرقم الطلب: {order_number}\nالتاريخ: {date}\nالساعة: {time}',
            'cancel_sms_template': 'تم إلغاء طلب موعدكم.\nلرقم الطلب: {order_number}',
        })


