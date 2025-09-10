from odoo import models, fields, api


class SmsLog(models.Model):
    _name = 'thoo8.sms.log'
    _description = 'SMS Log'
    _order = "create_date desc"

    provider_id = fields.Many2one("thoo8.sms.provider", string="Provider")
    to = fields.Char(string="Recipient")
    message = fields.Text(string="Message")
    status = fields.Char(string="Status")
    code = fields.Char(string="Code")
    response_text = fields.Text(string="Provider Response")
    create_date = fields.Datetime(string="Date Sent", readonly=True)
