from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class LdmContract(models.Model):
    _name = 'ldm.contract'
    _inherit = ['mail.thread.cc', 'mail.activity.mixin']
    _rec_name = 'contract_name'

    contract_code = fields.Char(string='Contract Code')
    contract_name = fields.Char('Contract Name')
    classification_name = fields.Char('Contract Classification')
    vat_number = fields.Char('Vat Registration Number')
