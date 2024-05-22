from odoo import api, fields, models, _


class IntegrationLog(models.Model):
    _name = 'integration.log'
    _rec_name = 'reason'
    _description = 'Integration Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    body = fields.Text(string='Body')
    reason = fields.Char(string='Reason')
    code = fields.Char(string='Code')
    request_date = fields.Datetime(string='Request Date')
    active = fields.Boolean(string='Active', default=True)
    service_type = fields.Selection([
        ('auth', 'authentication'),
        ('delete_service', ' Delete Service'),
        ('insert_payment', ' Insert Payment'),
        ('insert_service', ' Insert Service'),
        ('insert_visit', ' Insert Visit'),
        ('update_discount', ' Update Discount'),
        ('update_patient', ' Update Patient'),
        ('update_payer', ' Update Payer'),
        ('update_price', ' Update Price'),
    ])
