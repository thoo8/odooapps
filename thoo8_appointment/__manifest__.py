# -*- coding: utf-8 -*-
{
    'name': 'Thoo8 Online Appointment Booking',
    'summary': "Advanced Appointment Booking & Scheduling with Portal and SMS OTP Verification",
    'description': """
Thoo8 Appointment Booking Module
================================

A comprehensive and customizable appointment booking system integrated with portal, scheduling, and SMS gateway.

Main Features:
--------------
✅ **Website Portal Booking**
- Visitors can request appointments directly from the website portal.
- Supports booking with or without predefined schedules.
- Gender-based services (Male, Female, or Both).
- Automatic filtering of available services and slots.
- Prevents duplicate bookings for the same service and ID.

✅ **Mobile & ID Verification**
- OTP verification via SMS (integrated with `thoo8_sms_gateway`).
- ID card format validation (Saudi national IDs supported).
- Optional enabling/disabling of verifications via system settings.

✅ **Scheduling & Slot Management**
- Support for services with/without time slots.
- Separate schedules for male and female departments.
- Automatic slot reservation and release on booking, cancellation, or deletion.
- Daily booking limits and system-wide suspension options.

✅ **Admin Features**
- Full appointment lifecycle: Draft → Confirmed → Completed → Cancelled.
- Wizards for confirming, cancelling, and assigning appointments.
- Assign appointments to responsible users with notifications.
- Auto-create activities/tasks on confirmation.
- Cancellation reasons with optional SMS notification.
- Configurable SMS templates and rules.

✅ **Notifications & SMS**
- OTP verification via SMS for portal users.
- Confirmation and cancellation SMS notifications.
- SMS details logged in chatter for traceability.
- Works with "Msegat" provider or any `thoo8_sms_gateway` provider.

✅ **Security & Access Rights**
- Separate security groups for appointment management.
- Validation on ID card, mobile number, and duplicate prevention.
- Token-based validation for portal success pages.

✅ **Technical Highlights**
- Custom controllers for booking flow: service selection, schedule fetching, OTP, duplicate check, submission, and success.
- Dynamic domain filtering for available slots.
- Activities (`mail.activity`) integrated for task tracking.
- Fully integrated with `mail.thread` for communication.
- Extendable architecture for services, slots, and SMS providers.

""",
    'version': '15.0.1.0.0',
    'category': 'Extra Tools',
    'author': "Saleh Ibrahim - thoo8",
    'company': 'thoo8',
    'maintainer': 'thoo8',
    'website': "http://www.thoo8.com",
    'depends': [
        'base',
        'web',
        'portal',
        'website',
        'mail',
        'thoo8_sms_gateway',
    ],
    'data': [
        'security/appointment_security.xml',
        'security/appointment_rules.xml',
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/settings_data.xml',
        'data/public_data.xml',
        'views/appointment_views.xml',
        'views/dashboard_views.xml',
        'views/appointment_settings_sms_view.xml',
        'views/appointment_schedule_settings_view.xml',
        'views/portal_errore_submit_template.xml',
        'views/portal_appointment_template.xml',
        'views/portal_appointment_success_template.xml',
        'views/res_config_settings_views.xml',
        'wizard/confirm_appointment.xml',
        'wizard/cancel_appointment.xml',
        'wizard/assign_appointment.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
        'static/description/screenshots/settings_01.jpg',
        'static/description/screenshots/settings_02.jpg',
        'static/description/screenshots/001.jpg',
        'static/description/screenshots/002.jpg',
        'static/description/screenshots/003.jpg',
        'static/description/screenshots/004.jpg',
        'static/description/screenshots/005.jpg',
        'static/description/screenshots/006.jpg',
        'static/description/screenshots/007.jpg',
        'static/description/screenshots/008.jpg',
        'static/description/screenshots/009.jpg',
        'static/description/screenshots/010.jpg',
        'static/description/screenshots/011.jpg',
        'static/description/screenshots/012.jpg',
        'static/description/screenshots/013.jpg',
        'static/description/screenshots/014.jpg',
        'static/description/screenshots/015.jpg',
        'static/description/screenshots/017.jpg',
        'static/description/screenshots/018.jpg',
        'static/description/screenshots/019.jpg',
        'static/description/screenshots/020.jpg',
    ],
    'assets': {
        'web.assets_backend': [
            'thoo8_appointment/static/src/js/sms_vars_insert.js',
            'thoo8_appointment/static/src/css/sms_vars.css',
        ],
        'web.assets_frontend': [
            'thoo8_appointment/static/src/js/portal_form.js',
            'thoo8_appointment/static/src/js/sms_vars_insert.js',
            'thoo8_appointment/static/src/css/portal_form.css',
        ]
    },
    'license': 'LGPL-3',
    'application': True,
    'installable': True,
    'auto_install': False,
}
