from odoo import models, fields, api
from odoo.exceptions import UserError


class SmsTemplateFieldWizard(models.TransientModel):
    _name = 'thoo8.sms.template.field.wizard'
    _description = 'SMS Template Field Wizard'

    model_id = fields.Many2one('ir.model', string="Model", required=True, readonly=True)
    field_id = fields.Many2one('ir.model.fields', string="Field", required=True,
                               domain="[('model_id','=',model_id)]")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        template = self.env['thoo8.sms.template'].browse(self._context.get('active_id'))
        if template:
            res['model_id'] = template.model_id.id
        return res

    def action_insert_field(self):
        """Insert selected field as variable into template body"""
        self.ensure_one()
        template = self.env['thoo8.sms.template'].browse(self._context.get('active_id'))
        if not template:
            raise UserError("No SMS Template found in context.")

        variable = "{{ object.%s }}" % self.field_id.name
        if template.body:
            template.body = template.body + " " + variable
        else:
            template.body = variable
        return {'type': 'ir.actions.act_window_close'}
