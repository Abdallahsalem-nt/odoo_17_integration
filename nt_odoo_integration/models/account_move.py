from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

from odoo.tools import float_compare, float_is_zero, date_utils, email_split, email_re, html_escape, is_html_empty

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ldm_created_by = fields.Many2one('hr.employee')
    is_company2 = fields.Boolean(string='Is a Company', default=False,
                                 help="Check if the contact is a company, otherwise it is a person")
    company_type2 = fields.Selection(string='Company Type',
                                     selection=[('person', 'Individual'), ('company', 'Company')])
    center_code = fields.Char()
    accession_number = fields.Char()
    user_full_name = fields.Many2one(comodel_name="hr.employee", string="User Full Name")
    doctor_id = fields.Many2one('res.partner')
    age = fields.Char(string="Age", related='partner_id.patient_age')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], related='partner_id.gender')
    phone = fields.Char(string="Mobile", related='partner_id.phone')
    code = fields.Char(string="Code", related='partner_id.ref')

    @api.onchange('partner_id')
    def onchange_is_company(self):
        for rec in self:
            rec.is_company2 = rec.partner_id.is_company
            rec.company_type2 = rec.partner_id.company_type

    @api.model
    def corn_post_ldm_invoices(self):
        invoices = self.search([('state', '=', 'draft'),
                                ('move_type', '=', 'out_invoice')])
        for invoice in invoices:
            invoice.action_post()

    @api.model
    def walkin_patient_ldm_post_invoices(self):
        invoices = self.search([
            ('partner_id.is_public_audience', '=', True),
            ('state', '=', 'draft'),
            ('move_type', '=', 'out_invoice'),
        ]).filtered(lambda x: len(x.invoice_line_ids) > 0)
        for invoice in invoices:
            if invoice.is_invoice(include_receipts=True) and float_compare(invoice.amount_total, 0.0,
                                                                           precision_rounding=invoice.currency_id.rounding) < 0:
                _logger.error("cannot validate an invoice with a negative total amount ({})".format(invoice.id))
            else:
                _logger.info('before post payer')
                invoice.action_post()
                _logger.info('before post payer')

            self.env.cr.commit()

    @api.model
    def payer_ldm_post_invoices(self):
        invoices = self.search([
            ('partner_id.is_public_audience', '=', False),
            ('state', '=', 'draft'),
            ('move_type', '=', 'out_invoice'),
        ]).filtered(lambda x: len(x.invoice_line_ids) > 0)

        for invoice in invoices:
            if invoice.is_invoice(include_receipts=True) and float_compare(invoice.amount_total, 0.0,
                                                                           precision_rounding=invoice.currency_id.rounding) < 0:
                _logger.error("cannot validate an invoice with a negative total amount ({})".format(invoice.id))
            else:
                _logger.info('before post payer')
                invoice.action_post()
                _logger.info('before post payer')
            self.env.cr.commit()

    def reconcile_credit_note_invoices(self, ml):
        test_line = []
        for move in self:
            if move.state != 'posted' \
                    or move.payment_state not in ('not_paid', 'partial') \
                    or not move.is_invoice(include_receipts=True):
                continue

            pay_term_lines = move.line_ids \
                .filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            domain = [
                ('account_id', 'in', pay_term_lines.account_id.ids),
                ('parent_state', '=', 'posted'),
                ('move_id.move_type', '=', 'out_refund'),
                ('move_id', '=', ml),
                ('partner_id', '=', move.commercial_partner_id.id),
                ('reconciled', '=', False),
                '|', ('amount_residual', '!=', 0.0), ('amount_residual_currency', '!=', 0.0),
            ]

            if move.is_inbound():
                domain.append(('balance', '<', 0.0))
            else:
                domain.append(('balance', '>', 0.0))

            lines = self.env['account.move.line'].search(domain).sorted(
                key=lambda line: (line.date_maturity or line.date, line.currency_id))
            if lines:
                lines += move.line_ids.filtered(
                    lambda line: line.account_id == lines[
                        0].account_id and not line.reconciled)
            if lines not in test_line:
                test_line.append(lines)
        test = set(test_line)
        for l in test:
            l.reconciled = False
            l.reconcile()

    def corn_post_patient_invoices(self):
        self.search(
            [('state', '=', 'draft'), ('move_type', '=', 'out_invoice'), ('partner_id.is_public_audience', '=', True),
             ('move_type', '=', 'out_invoice')]).action_post()

    def corn_post_payer_invoices(self):
        self.search(
            [('state', '=', 'draft'), ('move_type', '=', 'out_invoice'), ('partner_id.is_public_audience', '=', False),
             ('move_type', '=', 'out_invoice')]).action_post()
