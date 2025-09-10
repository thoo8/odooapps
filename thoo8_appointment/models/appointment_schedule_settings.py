# models/appointment_schedule_settings.py

from odoo import models, fields, api, _
from datetime import timedelta, date, datetime, time

from odoo.exceptions import ValidationError, UserError


class AppointmentScheduleSettings(models.Model):
    _name = 'thoo8.appointment.schedule.settings'
    _description = 'Appointment Schedule Settings'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Schedule Name", required=True)
    appointment_duration = fields.Integer(string="Appointment Duration (minutes)", default=15)
    excluded_weekdays = fields.Many2many('thoo8.weekday', string="Excluded Weekdays")
    holiday_ids = fields.One2many('thoo8.appointment.holiday', 'settings_id', string="Official Holidays")
    start_time = fields.Float(string="Start Time", required=True, default=8.0)  # 8 AM
    end_time = fields.Float(string="End Time", required=True, default=16.0)  # 4 PM
    start_date = fields.Date(string="Schedule Start Date", required=True, default=fields.Date.context_today)
    end_date = fields.Date(string="Schedule End Date", required=True)
    slot_ids = fields.One2many('thoo8.appointment.slot', 'settings_id', string="Slots")

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        today = date.today()
        for rec in self:
            if rec.start_date and rec.start_date < today:
                raise ValidationError(_("Start date cannot be earlier than today."))
            if rec.end_date and rec.start_date and rec.end_date <= rec.start_date:
                raise ValidationError(_("End date must be greater than start date."))

    def generate_schedule(self):
        """Generate appointment slots based on settings"""
        slot_model = self.env['thoo8.appointment.slot']

        # Get booked slots
        booked_slots = slot_model.search([
            ('settings_id', '=', self.id),
            ('is_booked', '=', True)
        ])
        booked_datetimes = set(booked_slots.mapped('slot_datetime'))

        # Remove unbooked slots
        slot_model.search([
            ('settings_id', '=', self.id),
            ('is_booked', '=', False)
        ]).unlink()

        # Excluded weekdays
        excluded_days = [int(wd.code) for wd in self.excluded_weekdays]

        # Holidays
        holiday_days = set()
        for holiday in self.holiday_ids:
            current_holiday_date = holiday.start_date
            while current_holiday_date <= holiday.end_date:
                holiday_days.add(current_holiday_date)
                current_holiday_date += timedelta(days=1)

        created_count = 0
        booked_slots_count = len(booked_datetimes)

        # Generate slots
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.weekday() not in excluded_days and current_date not in holiday_days:
                current_time = self.start_time
                while current_time < self.end_time:
                    slot_datetime = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=current_time)
                    if slot_datetime not in booked_datetimes:
                        slot_model.create({
                            'slot_datetime': slot_datetime,
                            'settings_id': self.id
                        })
                        created_count += 1
                    current_time += self.appointment_duration / 60.0
            current_date += timedelta(days=1)


# models/holiday.py
class AppointmentHoliday(models.Model):
    _name = 'thoo8.appointment.holiday'
    _description = 'Official Holiday'

    name = fields.Char(string="Holiday Name", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    settings_id = fields.Many2one('thoo8.appointment.schedule.settings', string="Schedule Settings", ondelete='cascade')

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date and rec.start_date and rec.end_date < rec.start_date:
                raise ValidationError(_("End date of holiday must be equal to or later than start date."))


# models/weekday.py
class Weekday(models.Model):
    _name = 'thoo8.weekday'
    _description = 'Weekday'

    name = fields.Char(string="Day", required=True)
    code = fields.Selection([
        ('6', 'Sunday'),
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
    ], string="Day Code", required=True, unique=True)


# models/appointment_slot.py
class AppointmentSlot(models.Model):
    _name = 'thoo8.appointment.slot'
    _description = 'Appointment Slot'
    _order = 'slot_datetime asc'
    _rec_name = 'slot_datetime'

    slot_datetime = fields.Datetime(string="Slot DateTime", required=True, unique=True)
    is_booked = fields.Boolean(string="Booked", default=False)
    settings_id = fields.Many2one('thoo8.appointment.schedule.settings', string="Settings")
    date_only = fields.Date(string="Date", compute="_compute_date_time", store=True)
    time_only = fields.Char(string="Time", compute="_compute_date_time", store=True)

    @api.depends('slot_datetime')
    def _compute_date_time(self):
        for record in self:
            if record.slot_datetime:
                record.date_only = record.slot_datetime.date()
                record.time_only = record.slot_datetime.strftime('%H:%M')
            else:
                record.date_only = False
                record.time_only = False

    def unlink(self):
        for rec in self:
            if rec.is_booked:
                raise UserError(_("Cannot delete a booked slot. Cancel the booking first."))
        return super(AppointmentSlot, self).unlink()

    def write(self, vals):
        for rec in self:
            if rec.is_booked:
                restricted_fields = {'slot_datetime', 'settings_id'}
                if any(field in vals for field in restricted_fields):
                    raise UserError(_("Cannot modify the time or settings of a booked slot. Cancel the booking first."))
        return super(AppointmentSlot, self).write(vals)
