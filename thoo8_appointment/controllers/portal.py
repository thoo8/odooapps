from odoo import http, api, _
from odoo.http import request
from datetime import date
from datetime import datetime, timedelta
import random
import requests
import logging
import re
import secrets

_logger = logging.getLogger(__name__)


class AppointmentPortal(http.Controller):

    @http.route(['/thoo8/appointment'], type='http', auth='public', website=True)
    def portal_appointment(self, **kwargs):
        # جلب الإعدادات
        ICP = request.env['ir.config_parameter'].sudo()

        mobile_verification = ICP.get_param('thoo8.appointment.request.enable_mobile_verification') == 'True'
        id_card_verification = ICP.get_param('thoo8.appointment.request.enable_id_card_verification') == 'True'
        stop_all = ICP.get_param('thoo8.appointment.request.stop_all_bookings') == 'True'
        stop_when_reached = ICP.get_param('thoo8.appointment.request.stop_when_reached') == 'True'
        max_daily = int(ICP.get_param('thoo8.appointment.request.max_daily_bookings') or 0)

        error_message = None

        # إيقاف عام
        if stop_all:
            error_message = _("Sorry, appointment bookings are temporarily suspended.")

        # التحقق من الحد الأقصى اليومي
        elif stop_when_reached:
            today_count = request.env['thoo8.appointment.request'].sudo().search_count([
                ('create_date', '>=', date.today().strftime('%Y-%m-%d 00:00:00')),
                ('create_date', '<=', date.today().strftime('%Y-%m-%d 23:59:59')),
            ])
            if today_count >= max_daily:
                error_message = _("Sorry, the maximum number of bookings for today has been reached.")

        #جلب الخدمات المتاحة بعد فلترة المنتهية
        service_types_all = request.env['thoo8.service.type'].sudo().search([])
        service_types = []
        today = date.today()

        for service in service_types_all:
            include_service = False

            # رجال
            if service.service_gender in ['male', 'both']:
                if service.enable_male_schedule and service.schedule_male_id:
                    male_slots = service.schedule_male_id.slot_ids.filtered(
                        lambda s: not s.is_booked and s.date_only >= today
                    )
                    if male_slots:
                        include_service = True
                else:
                    include_service = True  # لم يتم تقييد الجدولة => اجلب الخدمة

            # نساء
            if service.service_gender in ['female', 'both']:
                if service.enable_female_schedule and service.schedule_female_id:
                    female_slots = service.schedule_female_id.slot_ids.filtered(
                        lambda s: not s.is_booked and s.date_only >= today
                    )
                    if female_slots:
                        include_service = True
                else:
                    include_service = True  # لم يتم تقييد الجدولة => اجلب الخدمة

            if include_service:
                service_types.append(service)

        if not service_types:
            error_message = _("Sorry, there are no available appointments at the moment.")

        return request.render('thoo8_appointment.portal_appointment_template', {
            'mobile_verification': mobile_verification,
            'id_card_verification': id_card_verification,
            'service_types': service_types,
            'error_message': error_message,
        })

    @http.route('/get_service_schedule', type='json', auth='public', methods=['POST'])
    def get_service_schedule(self, service_type_id, **kwargs):
        service = request.env['thoo8.service.type'].sudo().browse(int(service_type_id))

        # افتراضياً: نعيد التواريخ المتاحة والأوقات حسب الخدمة
        available_dates = []
        times = {}

        for schedule in service.schedule_ids:
            for date_info in schedule.get_available_dates():  # افترض هذه دالة تحسب الأيام المتاحة
                date_str = date_info['date']
                available_dates.append({'date': date_str, 'display': date_info['display']})
                times[date_str] = [{'id': t.id, 'display': t.name} for t in schedule.get_available_times(date_str)]

        return {
            'dates': available_dates,
            'times': times,
            'note': service.note,
            'gender': service.gender,
            'schedule_male_id': service.schedule_male_id.id if service.schedule_male_id else None,
            'schedule_female_id': service.schedule_female_id.id if service.schedule_female_id else None,
        }

    @http.route('/get_service_note', type='json', auth='public', website=True)
    def get_service_note(self, service_type_id):
        service = request.env['thoo8.service.type'].sudo().browse(int(service_type_id))
        if service.exists():
            return {
                'note': service.note or '',
                'gender': service.service_gender or 'both',
                'enable_male_schedule': service.enable_male_schedule,
                'enable_female_schedule': service.enable_female_schedule,
                'schedule_male_id': service.schedule_male_id.id if service.schedule_male_id else False,
                'schedule_female_id': service.schedule_female_id.id if service.schedule_female_id else False,
            }
        return {'note': ''}

    @http.route('/get_available_dates', type='json', auth='public', website=True)
    def get_available_dates(self, schedule_id):
        try:
            schedule_id = int(schedule_id)
            today = date.today()
            # جلب كل المواعيد غير المحجوزة من اليوم فصاعداً
            slots = request.env['thoo8.appointment.slot'].sudo().search([
                ('settings_id', '=', schedule_id),
                ('date_only', '>=', today),
                ('is_booked', '=', False)
            ], order='date_only asc')

            # اجمع كل التواريخ الفريدة
            dates_set = sorted(list(set([slot.date_only for slot in slots])))
            dates = [{'date': d.strftime('%Y-%m-%d'), 'display': d.strftime('%d/%m/%Y')} for d in dates_set]

            return {'dates': dates}
        except Exception as e:
            return {'dates': []}

    @http.route('/get_available_times', type='json', auth='public', website=True)
    def get_available_times(self, schedule_id, date):

        try:
            if not schedule_id or not date:
                return {'times': []}

            date_obj = datetime.strptime(date, "%Y-%m-%d").date()

            # البحث عن كل الـ Slots لهذا الجدول في هذا التاريخ، غير المحجوزة
            available_slots = request.env['thoo8.appointment.slot'].sudo().search([
                ('settings_id', '=', int(schedule_id)),
                ('date_only', '=', date_obj),
                ('is_booked', '=', False)
            ], order="slot_datetime asc")

            # تجهيز الأوقات في شكل list of dicts
            times = [{'id': slot.id, 'time': slot.time_only} for slot in available_slots]

            return {'times': times}

        except Exception as e:
            return {'times': [], 'error': str(e)}

    @http.route(['/thoo8/appointment/submit'], type='http', auth='public', website=True, csrf=True)
    def submit_appointment(self, **post):

        ICP = request.env['ir.config_parameter'].sudo()

        mobile_verification = ICP.get_param('thoo8.appointment.request.enable_mobile_verification') == 'True'
        id_card_verification = ICP.get_param('thoo8.appointment.request.enable_id_card_verification') == 'True'
        stop_all = ICP.get_param('thoo8.appointment.request.stop_all_bookings') == 'True'
        stop_when_reached = ICP.get_param('thoo8.appointment.request.stop_when_reached') == 'True'
        max_daily = int(ICP.get_param('thoo8.appointment.request.max_daily_bookings') or 0)

        # 1- منع الحجوزات بالكامل
        if stop_all:
            return request.render('thoo8_appointment.portal_appointment_template', {
                'error_message': _("Sorry, booking is currently suspended.")
            })

        # 2- التحقق من الحد اليومي
        if stop_when_reached and max_daily > 0:
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            today_count = request.env['thoo8.appointment.request'].sudo().search_count([
                ('create_date', '>=', today),
                ('create_date', '<', tomorrow)
            ])
            if today_count >= max_daily:
                return request.render('thoo8_appointment.portal_appointment_template', {
                    'error_message': _("Sorry, the maximum number of bookings for today has been reached.")
                })
        # الحقول المطلوبة
        required_fields = ['beneficiary_name', 'id_card', 'mobile', 'service_type']

        # إذا كان التحقق مفعل، أضف otp للقائمة
        if mobile_verification:
            required_fields.append('otp')

        # تحقق من الحقول المفقودة
        missing = [field for field in required_fields if not request.params.get(field)]

        if missing:
            return request.render("thoo8_appointment.portal_errore_submit_template", {
                'error_message': 'Missing fields: ' + ', '.join(missing)
            })

        # من هنا تبدأ المعالجة الفعلية، مثال فقط
        beneficiary_name = post.get("beneficiary_name")
        id_card = post.get("id_card")
        mobile = post.get("mobile")
        mobile_other = post.get("mobile_other")
        service_type = post.get("service_type")
        gender = post.get("gender")
        otp_code = post.get("otp")
        appointment_time = post.get("appointment_time")
        appointment_date = post.get("appointment_date")
        schedule_id = post.get("schedule_id")
        token = secrets.token_urlsafe(16)

        # تحقق رقم الجوال
        if not mobile or not re.match(r'^05\d{8}$', mobile):
            return request.render('thoo8_appointment.portal_errore_submit_template', {
                'error_message': _("Invalid mobile number. It must start with 05 and contain 10 digits."),
            })

        # تحقق رقم الهوية
        if not id_card:
            error_msg = _("ID Card number is required.")
        elif id_card_verification and not re.match(r'^[12]\d{9}$', id_card):
            error_msg = _("Invalid ID Card number. It must start with 1 or 2 and contain 10 digits.")
        else:
            error_msg = None

        if error_msg:
            return request.render('thoo8_appointment.portal_errore_submit_template', {
                'error_message': error_msg,
            })



        # تحقق من التكرار
        existing_appointment = request.env['thoo8.appointment.request'].sudo().search([
            ('id_card', '=', id_card),
            ('service_type_id', '=', int(service_type)),
            ('state', 'in', ['draft', 'confirmed'])
        ], limit=1)
        print(existing_appointment.id_card)
        if existing_appointment:
            return request.render('thoo8_appointment.portal_errore_submit_template', {
                'error_message': _("There is an existing request linked to the entered ID number. You will be notified once your appointment becomes available."),
            })

        # التحقق من الرمز والجوال
        session_code = request.session.get("otp_code")
        session_mobile = request.session.get("otp_mobile")

        if mobile_verification:
            if not session_code or not session_mobile or otp_code != session_code or mobile != session_mobile:
                error = _("The verification code is incorrect or does not match the mobile number.")
                return request.render('thoo8_appointment.portal_errore_submit_template', {
                    'error_message': error,
                    'values': request.params
                })

        slot_appointment_date = False
        slot = False
        use_schedule = False

        if appointment_time:
            slot = request.env['thoo8.appointment.slot'].sudo().search([('id', '=', int(appointment_time))], limit=1)
            if slot:
                use_schedule = True
                slot_appointment_date = slot.slot_datetime

        # تخزين الموعد
        appointment = request.env['thoo8.appointment.request'].sudo().create({
            'beneficiary_name': beneficiary_name,
            'id_card': id_card,
            'mobile': mobile,
            'mobile_other': mobile_other,
            'department': gender,
            'service_type_id': int(service_type),
            'appointment_date': slot_appointment_date,
            'use_schedule': use_schedule,
            'slot_id': int(appointment_time) if appointment_time else False,
            'from_portal': True,
            'token': token
        })

        # ⚡ إرسال SMS بعد نجاح التخزين
        settings = request.env['thoo8.appointment.settings_sms'].sudo().get_settings_sms()
        if appointment and settings and settings.enable_portal_confirm_sms and slot:
            send_sms = appointment._send_sms_notification('confirm_portal')
            appointment.template_sms_resulte('confirm', send_sms)

        request.session.pop('otp_code', None)
        request.session.pop('otp_mobile', None)

        return request.redirect(f'/thoo8/appointment/success?appointment_id={appointment.id}&token={appointment.token}')

    @http.route(['/thoo8/appointment/send_otp'], type='json', auth='public', methods=['POST'], website=True)
    def send_otp(self, mobile=None, **kwargs):

        if not mobile:
            return {'success': False, 'message': f'Mobile number required {mobile}'}

        otp = str(random.randint(1000, 9999))

        request.session["otp_%s" % mobile] = otp
        request.session['otp_code'] = otp
        request.session['otp_mobile'] = mobile

        self.send_sms_via_msegat(mobile, f"رمز التحقق لطلب موعد هو: {otp}")

        return {'success': True, 'code': otp, 'message': 'OTP sent successfully'}

    def send_sms_via_msegat(self, mobile, message):
        provider = request.env['ir.config_parameter'].sudo().get_param("thoo8_sms.default_provider_id")
        print(provider)
        if provider:

            # using thoo8_sms_gateway
            response = request.env['thoo8.sms.provider'].sudo().send_sms(mobile, message)

        print(response)

    @http.route('/check_duplicate_id', type='json', auth='public', website=True)
    def check_duplicate_id(self, id_card, service_type):
        record = request.env['thoo8.appointment.request'].sudo().search([
            ('id_card', '=', id_card),
            ('service_type_id', '=', int(service_type)),
            ('state', 'in', ['draft', 'confirmed'])
        ], limit=1)

        if record:
            return {
                'exists': True,
                'name': record.beneficiary_name,
                'beneficiary_name': record.beneficiary_name,
                'mobile': record.mobile,
            }
        else:
            return {
                'exists': False,
                'id_card': id_card,
                'service_type_id': service_type
            }

    @http.route('/thoo8/appointment/success', type='http', auth='public', website=True)
    def appointment_success(self, **kw):
        appointment_id = kw.get('appointment_id')
        token = kw.get('token')
        appointment = request.env['thoo8.appointment.request'].sudo().browse(
            int(appointment_id)) if appointment_id else None

        print(appointment)
        print(appointment.token)
        print(token)

        # التحقق من التوكن
        if not appointment or appointment.token != token:
            return request.not_found()

        if appointment.slot_id:
            appointment.write({'state': 'confirmed'})

        return request.render('thoo8_appointment.portal_appointment_success_template', {
            'appointment': appointment,
        })

    @http.route('/validate_otp_session', type='json', auth='public')
    def validate_otp_session(self, otp_code=None, mobile=None):
        session_code = request.session.get('otp_code') or ''
        session_mobile = request.session.get('otp_mobile') or ''

        is_valid = bool(session_code and session_mobile and otp_code == session_code and mobile == session_mobile)
        return {'valid': is_valid}
