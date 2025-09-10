from odoo import models, fields, api
from jinja2 import Template

class SmsTemplate(models.Model):
    _name = 'thoo8.sms.template'
    _description = 'SMS Template'
    _rec_name = "name"

    name = fields.Char("Template Name", required=True)
    model_id = fields.Many2one(
        "ir.model",
        string="Applies to",
        help="The model this template is related to (e.g. res.partner, sale.order)."
    )
    lang = fields.Selection(
        selection=lambda self: self.env['res.lang'].get_installed(),
        string="Language",
        help="Optional language for the template rendering."
    )
    body = fields.Text(
        "Message Body",
        required=True,
        help="You can use variables with Jinja2 format, e.g. {{ object.name }}"
    )
    active = fields.Boolean("Active", default=True)
    available_fields = fields.Text(
        "Available Fields",
        compute="_compute_available_fields"
    )

    @api.depends('model_id')
    def _compute_available_fields(self):
        for rec in self:
            if rec.model_id:
                model = self.env[rec.model_id.model]
                fields_list = []
                for fname, f in model._fields.items():
                    fields_list.append(f"{fname} ({f.type})")
                rec.available_fields = "\n".join(fields_list)
            else:
                rec.available_fields = ""

    def render_template(self, record=None):
        """ Render SMS body with Jinja2 template engine """
        self.ensure_one()
        context = {}
        if record:
            context["object"] = record
        try:
            template = Template(self.body or "")
            return template.render(context)
        except Exception as e:
            return f"[Template Error: {str(e)}]"
