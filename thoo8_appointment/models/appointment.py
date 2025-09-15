import re
from datetime import date, datetime, timedelta

import pytz
from babel.dates import format_datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
import requests

from odoo.exceptions import UserError, ValidationError


class Appointment(models.Model):
    _name = 'thoo8.appointment.request'
    _description = 'Appointment Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('check_mobile', 'check(REGEXP_LIKE(mobile, "^(05)[0-9]{8}$"))', "mobile must to be 10 digit!"),]

    def name_get(self):
        result = []
        for record in self:
            display_name = f"{record.name} - {record.beneficiary_name}" if record.beneficiary_name else record.name
            result.append((record.id, display_name))
        return result

    name = fields.Char(string="Request Number", required=True, copy=False, readonly=True, default='New', tracking=True)
    beneficiary_name = fields.Char(string="Beneficiary Name ", required=True, tracking=True)
    id_card = fields.Char(string="ID Card", required=True, tracking=True)
    mobile = fields.Char(string="Mobile", required=True, tracking=True)
    mobile_other = fields.Char(string="Mobile (Other)", tracking=True)
    service_type_id = fields.Many2one('thoo8.service.type', string="Service Type", required=True, tracking=True)
    service_note = fields.Html(related="service_type_id.note", string="Note of Appointment", readonly=True)
    otp_verified = fields.Boolean(string="OTP Verified", default=False, tracking=True)
    note = fields.Text(string="Internal Notes", tracking=True)
    appointment_date = fields.Datetime(string="Appointment Date", tracking=True)
    appointment_end = fields.Datetime(string="Appointment End", compute='_compute_appointment_end', store=False)
    formatted_datetime_ar = fields.Char(string="Detail of Appointment", compute='_compute_formatted_datetime_ar',
                                        tracking=True)
    cancel_reason = fields.Many2one('thoo8.appointment.cancel_reason', string='Reason Of Cancel', tracking=True)
    cancel_note = fields.Text(string="Cancel Note", tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    token = fields.Char(string='Security Token', readonly=True, copy=False)
    slot_id = fields.Many2one('thoo8.appointment.slot', string="Appointment Schedule Slot", tracking=True,
                              domain="[('is_booked','=',False)]")
    department = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string="Department", required=True, tracking=True)
    use_schedule = fields.Boolean(string="Use Schedule", default=False, tracking=True)
    slot_message = fields.Char(string="", store=False)
    from_portal = fields.Boolean(string="Created from Portal", default=False)
    user_id = fields.Many2one('res.users', string='Assigned To', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('thoo8.appointment.request') or '/'

        slot = self.env['thoo8.appointment.slot'].browse(vals.get('slot_id.id'))
        if slot.is_booked:
            raise UserError(_("The selected date is already booked. Please choose another date."))
        if self.slot_id:
            self.slot_id.is_booked = True

        rec = super(Appointment, self).create(vals)
        slot.is_booked = True
        send_sms = rec._send_sms_notification('create')

        return rec

    def write(self, vals):
        # عند التعديل، حجز او فك الحجز
        for rec in self:
            if rec.slot_id:
                rec.slot_id.is_booked = True
            else:
                rec.slot_id.is_booked = False

        return super(Appointment, self).write(vals)

    def unlink(self):
        # عند الحذف، فك الحجز
        for rec in self:
            if rec.slot_id:
                rec.slot_id.is_booked = False
        return super(Appointment, self).unlink()

    @api.depends('appointment_date')
    def _compute_appointment_end(self):
        for rec in self:
            rec.appointment_end = rec.appointment_date + timedelta(hours=1) if rec.appointment_date else False

    @api.onchange('service_type_id')
    def _onchange_service_type_id(self):
        for rec in self:
            rec.slot_id = False
            rec.appointment_date = False
            if rec.service_type_id and rec.use_schedule:
                service = rec.service_type_id
                male_enabled = service.enable_male_schedule
                female_enabled = service.enable_female_schedule

                # الحالة: رجال فقط
                if male_enabled and not female_enabled:
                    rec.department = 'male'
                    return {'readonly': [('department', '=', True)]}

                # الحالة: نساء فقط
                elif female_enabled and not male_enabled:
                    rec.department = 'female'
                    return {'readonly': [('department', '=', True)]}

                # الحالة: كلاهما
                elif male_enabled and female_enabled:
                    rec.department = False  # يخليه فارغ عشان المستخدم يختار
                    return {'readonly': [('department', '=', False)]}

                else:
                    raise ValidationError("This service does not have scheduled appointments for the (men's & fmale's) department..")

    @api.onchange('use_schedule', 'department', 'service_type_id')
    def _onchange_use_schedule(self):
        for rec in self:
            rec.appointment_date = False
            domain = {'slot_id': []}
            rec.slot_message = False  # إعادة الضبط

            if rec.use_schedule and rec.service_type_id and rec.department:
                service = rec.service_type_id
                slot_domain = [('is_booked', '=', False)]

                if not self.env.user.has_group('thoo8_appointment.group_thoo8_appointment_full_access'):
                    slot_domain.append(('date_only', '>=', fields.Date.today()))

                if rec.department == 'male':
                    if service.enable_male_schedule and service.schedule_male_id:
                        slot_domain.append(('settings_id', '=', service.schedule_male_id.id))
                    else:
                        rec.slot_id = False
                        rec.slot_message = _("⚠️ This service does not have scheduled appointments for the men's department.")
                        slot_domain = [('id', '=', False)]

                elif rec.department == 'female':
                    if service.enable_female_schedule and service.schedule_female_id:
                        slot_domain.append(('settings_id', '=', service.schedule_female_id.id))
                    else:
                        rec.slot_id = False
                        rec.slot_message = _("⚠️ This service does not have scheduled appointments for the women's department.")
                        slot_domain = [('id', '=', False)]

                domain['slot_id'] = slot_domain

            else:
                rec.slot_id = False
                rec.slot_message = _("⚠️ Please select a department and service.")
                domain['slot_id'] = [('id', '=', False)]

            return {'domain': domain}

    def get_settings_sms(self):
        return self.env['thoo8.appointment.settings_sms'].search([], limit=1)

    # working fine with "masegat" provider
    def template_sms_resulte(self, status, response_list):

        response = response_list or {}

        if not isinstance(response, dict):
            response = {}

        # الوصول للقيم بأمان
        code = response.get('code', '')
        message = response.get('message', '')
        sms_mobile = response.get('mobile', '')
        sms_text = response.get('message_text', '')

        self.sudo().message_post(
            body=(
                     "<b>📩 تفاصيل إرسال الرسالة النصية</b>"
                     "<ul>"
                     "<li>رمز الاستجابة: %s</li>"
                     "<li>رسالة الاستجابة: %s</li>"
                     "<li>سبب الإرسال: %s</li>"
                     "<li>رقم الجوال: %s</li>"
                     "<li>نص الرسالة:<br>%s</li>"
                     "</ul>"
                 ) % (code, message, status, sms_mobile, sms_text)
        )

    @api.constrains('id_card', 'service_type_id', 'state')
    def _check_duplicate_reservation(self):

        for record in self:
            # البحث عن حجوزات مطابقة
            duplicate_reservations = self.env['thoo8.appointment.request'].search([
                ('id', '!=', record.id),  # استبعاد السجل الحالي إذا كان تحديثًا
                ('id_card', '=', record.id_card),
                ('service_type_id', '=', record.service_type_id.id),
                ('state', 'in', ['draft', 'confirmed']),
            ])

            if duplicate_reservations:
                # إذا تم العثور على حجوزات مكررة، ارفض الحفظ
                # يمكننا عرض تفاصيل أول حجز مكرر تم العثور عليه
                existing_reservation = duplicate_reservations[0]

                # ترجمة حالة الحجز للعرض في الرسالة
                state_map = {
                    'draft': 'مسودة',
                    'confirmed': 'مؤكدة',
                    'done': 'منتهي',
                    'cancelled': 'ملغي',
                }
                existing_state_display = state_map.get(existing_reservation.state, existing_reservation.state)

                raise ValidationError(
                    f"يوجد حجز مسبق لنفس الخدمة ({existing_reservation.service_type_id.name}) "
                    f"برقم الهوية المسجل ({existing_reservation.id_card}) "
                    f"وحالته: {existing_state_display}. يرجى التحقق من الحجوزات الحالية."
                )

    @api.constrains('mobile', 'id_card')
    def _check_mobile_and_id_card(self):
        for rec in self:
            
            id_card_velidiation = self.env['ir.config_parameter'].sudo().get_param("thoo8.appointment.request.enable_id_card_verification")

            # التحقق من رقم الهوية: 10 أرقام
            if rec.id_card and id_card_velidiation:
                if not re.fullmatch(r'\d{10}', rec.id_card):
                    raise ValidationError(_("The ID number must consist of 10 digits."))

            # التحقق من رقم الجوال: 10 أرقام ويبدأ بـ 05
            if rec.mobile:
                if not re.fullmatch(r'05\d{8}', rec.mobile):
                    raise ValidationError(_("Mobile number must be 10 digits long and start with 05."))

    # استكمال الدالة وتوسيعها لتشمل باقي العمليات من خلال تمرير نوع العملية
    def _send_sms_notification(self, satus):
        settings = self.get_settings_sms()

        if not settings:
            return

        _date = self.appointment_date.strftime('%Y-%m-%d') if self.appointment_date else ''
        _time = self.appointment_date.strftime('%H:%M') if self.appointment_date else ''

        if satus == 'create' and settings.enable_create_sms:
            message = settings.create_sms_template.format(
                order_number=self.name or '',
                name=self.beneficiary_name or '',
                id_card=self.id_card or '',
                mobile=self.mobile or ''
            )
            send_sms = True

        if satus == 'confirm' and settings.enable_confirm_sms:
            message = settings.confirm_sms_template.format(
                order_number=self.name or '',
                name=self.beneficiary_name or '',
                id_card=self.id_card or '',
                mobile=self.mobile or '',
                date=_date,
                time=_time
            )
            send_sms = True

        if satus == 'confirm_portal' and settings.enable_portal_confirm_sms:
            message = settings.confirm_portal_sms_template.format(
                order_number=self.name or '',
                name=self.beneficiary_name or '',
                id_card=self.id_card or '',
                mobile=self.mobile or '',
                date=_date,
                time=_time
            )
            send_sms = True

        if satus == 'cancel' and settings.enable_cancel_sms:
            message = settings.cancel_sms_template.format(
                order_number=self.name or '',
                name=self.beneficiary_name or '',
                id_card=self.id_card or '',
                mobile=self.mobile or '',
                cancel_reason=self.cancel_reason.name or '',
                date=_date,
                time=_time
            )
            send_sms = True

        if send_sms:
            sms_send = self._send_sms(self.mobile, message)
            self.template_sms_resulte(satus, sms_send)
            return sms_send

    def _send_sms(self, phone, message):

        provider = self.env['ir.config_parameter'].sudo().get_param("thoo8_sms.default_provider_id")
        response = {}

        if provider:
            # using thoo8_sms_gateway
            response = self.env['thoo8.sms.provider'].send_sms(phone, message)

            response.update({
                'mobile': phone,
                'message_text': message
            })

            print(response)

        return response

    def action_cancelled(self):
        for rec in self:
            if self.appointment_date:
                appointment_date = rec.appointment_date
                formatted_datetime_ar = rec.formatted_datetime_ar
                selected_date = appointment_date.date()
            else:
                selected_date = ""
                formatted_datetime_ar = ""

            settings_sms = self.sudo().get_settings_sms()

            context = {
                'default_appointment_id': rec.id,
                'default_selected_date': str(selected_date),
                'default_formatted_datetime_ar': formatted_datetime_ar,
                'default_enable_cancel_sms': settings_sms.enable_cancel_sms,
                'default_slot_id': rec.slot_id.id
            }

            return {
                'type': 'ir.actions.act_window',
                'name': _('Cancel Appointment'),
                'res_model': 'cancel.appointment.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': context
            }

    def _cancel_appointment(self, send_sms=False):
        if send_sms:
            self._send_sms_notification('cancel')

    def action_confirmed(self):
        for rec in self:
            if not rec.appointment_date:
                raise UserError(_("You Not Select Appointment Date And time."))

            today = date.today()
            appointment_date = rec.appointment_date
            formatted_datetime_ar = rec.formatted_datetime_ar

            selected_date = appointment_date.date()
            show_date = selected_date < today

            settings_sms = self.get_settings_sms()

            context = {
                'default_appointment_id': rec.id,
                'default_selected_date': str(selected_date),
                'default_show_date_warning': show_date,
                'default_appointment_date': appointment_date,
                'default_user_id': rec.id,
                'default_formatted_datetime_ar': formatted_datetime_ar,
                'default_enable_confirm_sms': settings_sms.enable_confirm_sms
            }

            return {
                'type': 'ir.actions.act_window',
                'name': _('Confirm Appointment'),
                'res_model': 'confirm.appointment.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': context
            }

    def _confirm_appointment(self, send_sms=False):
        self.write({'state': 'confirmed'})
        if send_sms:
            self._send_sms_notification('confirm')

    def action_completed(self):

        # تحديث الأنشطة المرتبطة لتكون مكتملة
        activities = self.env['mail.activity'].search([
            ('res_model', '=', 'thoo8.appointment.request'),
            ('res_id', '=', self.id)
        ])
        for activity in activities:
            activity.action_done()

        self.write({'state': 'completed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.depends('appointment_date')
    def _compute_formatted_datetime_ar(self):
        arabic_months = {
            1: 'يناير', 2: 'فبراير', 3: 'مارس', 4: 'أبريل',
            5: 'مايو', 6: 'يونيو', 7: 'يوليو', 8: 'أغسطس',
            9: 'سبتمبر', 10: 'أكتوبر', 11: 'نوفمبر', 12: 'ديسمبر'
        }

        weekdays_ar = {
            0: 'الاثنين', 1: 'الثلاثاء', 2: 'الأربعاء',
            3: 'الخميس', 4: 'الجمعة', 5: 'السبت', 6: 'الأحد'
        }

        for record in self:
            if record.appointment_date:
                # تحويل التاريخ حسب المنطقة الزمنية
                tz = pytz.timezone('Asia/Riyadh')
                dt = record.appointment_date.astimezone(tz)

                day_name = weekdays_ar[dt.weekday()]
                day = dt.day
                month_name = arabic_months[dt.month]
                year = dt.year
                hour = dt.strftime('%I')  # 12-hour format
                minute = dt.strftime('%M')
                am_pm = 'صباحاً' if dt.strftime('%p') == 'AM' else 'مساءً'

                record.formatted_datetime_ar = f"{day_name} {day} {month_name} {year} - الساعة {hour}:{minute} {am_pm}"
            else:
                record.formatted_datetime_ar = ''

    @api.onchange('slot_id')
    def _onchange_slot_id(self):
        self.appointment_date = self.slot_id.slot_datetime

    # now we're not using this function, but it's working fine
    def action_send_sms_confirmation(self, template_id=None):
        """Send confirmation SMS to requester using SMS provider"""

        mobile = self.mobile
        if not mobile:
            raise UserError("رقم الجوال غير موجود.")

        # الرسالة
        if template_id:
            # لو اخترنا قالب معين
            template = self.env['thoo8.sms.template'].browse(template_id)
            if not template.exists():
                raise UserError("القالب غير موجود.")
            message = template.render_template(self.id)
        else:
            # بدون قالب → نص يدوي
            message = f"مرحباً {self.beneficiary_name}, تم حجز موعدك بتاريخ {self.appointment_date}."
            print(message)

        # استدعاء مزود الرسائل
        response = self.env['thoo8.sms.provider'].send_sms(mobile, message)
        print(response)

        return response

    def action_open_assign_wizard(self):

        for rec in self:
            if not rec.appointment_date:
                raise UserError(_("You Not Select Appointment Date And time."))

            """Open the wizard to assign appointment"""
            rec.ensure_one()
            return {
                'name': 'Assign Appointment',
                'type': 'ir.actions.act_window',
                'res_model': 'thoo8.appointment.assign.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_appointment_id': self.id,
                },
            }

    def _send_notification(self, user, title, message):
        """Send bus notification to a specific user"""
        if not user or not user.partner_id:
            return

        self.env['bus.bus']._sendone(
            user.partner_id,
            'simple_notification',
            {
                'title': title,
                'message': message,
                'sticky': False,
                'type': 'info'
            }
        )

    def activity_schedule_adding(self):

        for rec in self:

            prev_user = rec.user_id
            new_user = rec.user_id
            activity_date = rec.appointment_date.date()

            print(rec.appointment_date)
            print(activity_date)

            # حذف كل الأنشطة السابقة للموعد
            self.env['mail.activity'].search([
                ('res_model', '=', 'thoo8.appointment.request'),
                ('res_id', '=', rec.id)
            ]).unlink()

            # إشعار الموظف الجديد (bus notification)
            self._send_notification(
                new_user,
                "New Appointment Assigned",
                f"You have been assigned a new appointment: {rec.name}"
            )

            # إضافة Activity للموظف الجديد
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=new_user.id,
                note=f"You have been assigned a new appointment: {rec.name}",
                date_deadline=activity_date
            )

            # إشعار الموظف السابق إذا تم سحب الموعد منه
            if prev_user and prev_user != new_user:
                self._send_notification(
                    prev_user,
                    "Appointment Reassigned",
                    f"The appointment {rec.name} has been reassigned to another user."
                )

                # تسجيل رسالة في الـ chatter
                self.message_post(
                    body=f"Appointment reassigned from <b>{prev_user.name}</b> to <b>{new_user.name}</b>."
                )


class ServiceType(models.Model):
    _name = 'thoo8.service.type'
    _description = 'Service Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('unique_banae', 'unique(name)', 'the service name already exists.')]

    name = fields.Char(string="Service Name", required=True, tracking=True, translate=True)
    note = fields.Html(string="Note About Appointment", tracking=True, translate=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    service_gender = fields.Selection([
        ('male', "Men's Only"),
        ('female', "Female's Only"),
        ('both', 'Both')
    ], string="Target audience", default='both', required=True)
    schedule_male_id = fields.Many2one('thoo8.appointment.schedule.settings', string="Men's Department Schedule",
                                       domain="[('id', 'not in', [schedule_female_id])]",
                                       help="Choose the schedule for the Male's Department")
    schedule_female_id = fields.Many2one('thoo8.appointment.schedule.settings', string="Female's Section Schedule",
                                         domain="[('id', 'not in', [schedule_male_id])]",
                                         help="Choose the schedule for the Female's Department")
    enable_male_schedule = fields.Boolean(
        string="Activate restricting men's appointments according to the schedule (appointments will be confirmed automatically)")
    enable_female_schedule = fields.Boolean(
        string="Activate restricting Female's appointments according to the schedule (appointments will be confirmed automatically)")

    @api.onchange('enable_male_schedule')
    def _onchange_enable_male_schedule(self):
        if not self.enable_male_schedule:
            self.schedule_male_id = False

    @api.onchange('enable_female_schedule')
    def _onchange_enable_female_schedule(self):
        if not self.enable_female_schedule:
            self.schedule_female_id = False

    @api.onchange('service_gender')
    def _onchange_service_gender(self):
        if self.service_gender == 'male':
            self.enable_female_schedule = False
            self.schedule_female_id = False
        elif self.service_gender == 'female':
            self.enable_male_schedule = False
            self.schedule_male_id = False


class AppointmentCancelReason(models.Model):
    _name = 'thoo8.appointment.cancel_reason'
    _description = 'Cancel Reason Of Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('unique_banae', 'unique(name)', 'the reason name already exists..')]

    name = fields.Char(string="Reason Name", required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)


class OTPCode(models.Model):
    _name = 'thoo8.otp.code'
    _description = 'OTP Code for Appointment Verification'

    mobile = fields.Char(string='Mobile Number', required=True, tracking=True)
    code = fields.Char(string='OTP Code', required=True, tracking=True)
    is_verified = fields.Boolean(string='Verified', default=False, tracking=True)
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now, tracking=True)
