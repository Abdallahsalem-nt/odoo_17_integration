from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    accession_number = fields.Char('Accession Number')
    contract_id = fields.Many2one('ldm.contract', string='Contract')
    center_id = fields.Many2one('res.partner')
    doctor_id = fields.Many2one('res.partner')
    payer_id = fields.Many2one('res.partner')
    service_payer_id = fields.Many2one('res.partner', string='Payer')
    registration_date = fields.Date('Registration Date')
    patient_id = fields.Many2one("res.partner", string="Patient")
    reg_key = fields.Char('Reg Key')
    representative = fields.Char('Representative')
    is_cancelled = fields.Boolean(default=False)
