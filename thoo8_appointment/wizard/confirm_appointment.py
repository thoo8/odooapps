# -*- coding: utf-8 -*-
import pytz
from babel.dates import format_datetime
from datetime import datetime
from odoo import models, fields, api, _


class ConfirmAppointmentWizard(models.TransientModel):
    _name = 'confirm.appointment.wizard'
    _description = 'Confirm Appointment'

    appointment_id = fields.Many2one(
        'thoo8.appointment.request',
        string="Appointment",
        tracking=True
    )
    selected_date = fields.Date(
        string="Appointment Date",
        tracking=True
    )
    appointment_date = fields.Datetime(
        string="Appointment Date & Time",
        tracking=True
    )
    show_date_warning = fields.Boolean(
        string="Date Warning",
        default=False,
        tracking=True
    )
    formatted_datetime_ar = fields.Char(
        string="Appointment Details",
        tracking=True
    )
    enable_confirm_sms = fields.Boolean(
        string="Enable SMS on Confirmation",
        default=False
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        required=True,
        tracking=True
    )

    def confirm_with_sms(self):
        self.appointment_id._confirm_appointment(send_sms=True)

        self.appointment_id.activity_schedule_adding()

    def confirm_without_sms(self):
        self.appointment_id._confirm_appointment(send_sms=False)

        self.appointment_id.activity_schedule_adding()

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        return res
