from odoo import models, fields, api

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
