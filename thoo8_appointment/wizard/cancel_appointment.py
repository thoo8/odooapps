# -*- coding: utf-8 -*-
import pytz
from babel.dates import format_datetime
from datetime import datetime
from odoo import models, fields, api, _


class CancelAppointmentWizard(models.TransientModel):
    _name = 'cancel.appointment.wizard'
    _description = 'Confirm Cancellation Appointment'

    appointment_id = fields.Many2one(
        'thoo8.appointment.request',
        string="Appointment",
        required=True
    )
    selected_date = fields.Date(string="Appointment Date")
    formatted_datetime_ar = fields.Char(string="Appointment Details")
    enable_cancel_sms = fields.Boolean(
        string="Enable SMS on Cancellation",
        default=False
    )
    cancel_reason = fields.Many2one(
        'thoo8.appointment.cancel_reason',
        string='Cancellation Reason',
        required=True
    )
    cancel_note = fields.Text(string="Cancellation Notes")
    slot_id = fields.Many2one(
        'thoo8.appointment.slot',
        string="Appointment Schedule Slot"
    )

    def _do_cancel(self, send_sms=False):
        self.ensure_one()
        appt = self.appointment_id.sudo()

        # Release the booked slot (if exists)
        if appt.slot_id:
            appt.slot_id.sudo().write({'is_booked': False})

        # حذف الأنشطة المرتبطة
        self.env['mail.activity'].search([
            ('res_model', '=', 'thoo8.appointment.request'),
            ('res_id', '=', self.appointment_id.id)
        ]).unlink()

        # Update appointment state
        appt.write({
            'state': 'cancelled',
            'cancel_reason': self.cancel_reason.id,
            'cancel_note': self.cancel_note,
            'slot_id': False,
        })

        # Cancellation logic (send SMS internally based on send_sms)
        appt._cancel_appointment(send_sms=send_sms)

    def cancel_with_sms(self):
        self._do_cancel(send_sms=True)

    def cancel_without_sms(self):
        self._do_cancel(send_sms=False)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Optionally pre-fill fields from context
        active = self.env.context.get('active_id')
        if active and 'appointment_id' in fields_list:
            res['appointment_id'] = active
        return res
