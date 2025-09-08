{
    'name': 'Thoo8 Appointment Booking',
    'summary': "Custom Appointment Booking via Odoo Portal",
    'description': "Allows users to request appointments through the portal with mobile OTP verification",

    'category': 'thoo8',
    'version': '15.0.1.0.0',
    'author': "thoo8 - Saleh Ibrahim",
    'maintainer': 'Saleh Ibrahim',
    'website': "http://www.thoo8.com",
    'license': 'LGPL-3',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'portal', 'website', 'mail'],

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
    'images': ['static/description/icon.png'],
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
    'application': True,
    'installable': True,
    'auto_install': False,
}

