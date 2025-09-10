from odoo import http
from odoo.http import request

class Thoo8DashboardController(http.Controller):

    @http.route('/thoo8/dashboard/data', type='json', auth='user')
    def get_dashboard_data(self):
        Appointment = request.env['thoo8.appointment.request']

        # KPIs
        total = Appointment.search_count([])
        confirmed = Appointment.search_count([('state', '=', 'confirmed')])
        completed = Appointment.search_count([('state', '=', 'completed')])
        cancelled = Appointment.search_count([('state', '=', 'cancelled')])

        # Chart data
        labels = ["Confirmed", "Completed", "Cancelled"]
        values = [confirmed, completed, cancelled]

        return {
            "kpis": {
                "total": total,
                "confirmed": confirmed,
                "completed": completed,
                "cancelled": cancelled,
            },
            "chart": {
                "labels": labels,
                "values": values,
            }
        }
