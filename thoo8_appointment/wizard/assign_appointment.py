from odoo import models, fields, api

class AppointmentAssignWizard(models.TransientModel):
    _name = 'thoo8.appointment.assign.wizard'
    _description = 'Assign Appointment Wizard'

    appointment_id = fields.Many2one('thoo8.appointment.request', string="Appointment")
    user_id = fields.Many2one('res.users', string="Assign to", required=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        appointment = self.env['thoo8.appointment.request'].browse(
            self._context.get('default_appointment_id')
        )
        if appointment.user_id:
            res['user_id'] = appointment.user_id.id
        res['appointment_id'] = appointment.id
        return res

    def action_assign(self):
        """Assign appointment to selected user, notify new user and previous user if exists"""
        new_user = self.user_id
        # تحديث الإسناد
        self.appointment_id.user_id = new_user.id

        self.appointment_id.activity_schedule_adding()

        return {'type': 'ir.actions.act_window_close'}

