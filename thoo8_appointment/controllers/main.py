
from odoo import http, _
from odoo.http import request
import json


class AppointmentController(http.Controller):

    @http.route('/api/appointment', auth='public', type='json', methods=['POST'], csrf=False)
    def create_appointment(self, **post):
        try:
            data = post if isinstance(post, dict) else json.loads(post)
            appointment = request.env['thoo8.appointment.request'].sudo().create({
                'beneficiary_name': data.get('beneficiary_name'),
                'id_card': data.get('id_card'),
                'mobile': data.get('mobile'),
                'mobile_other': data.get('mobile_other'),
                'appointment_date': data.get('appointment_date'),
                'service_type_id': data.get('service_type_id')
            })
            return {
                'success': True,
                'message': 'Appointment created successfully.',
                'appointment_id': appointment.id
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
