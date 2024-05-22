from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    accession_number = fields.Char('Accession Number')
    receipt_number = fields.Char('Receipt Number')
    branch_id = fields.Many2one('account.analytic.account', string='Branch')
    ldm_created_by = fields.Many2one('hr.employee')
    payment_method_journal_id = fields.Many2one('account.journal', 'Payment Method Journal')
    # ldm_payment_method = fields.Char('Payment Method')
    payment_method = fields.Char()
    patient_name = fields.Char('Patient Name')
    ldm_payment_date = fields.Char('Ldm Payment Date')
    reg_key = fields.Char('Reg Key')
    receipt_no = fields.Char('Receipt NO')
    ldm_payment_amount = fields.Monetary(currency_field='currency_id', string="LDM Payment")
    user_full_name = fields.Many2one(comodel_name="hr.employee", string="User Full Name")

    def compute_ldm_payment_amount(self):
        for rec in self.search([]):
            if rec.partner_type == "customer":
                if rec.payment_type == "inbound":
                    rec.ldm_payment_amount = rec.amount
                if rec.payment_type == "outbound":
                    rec.ldm_payment_amount = -1 * rec.amount
