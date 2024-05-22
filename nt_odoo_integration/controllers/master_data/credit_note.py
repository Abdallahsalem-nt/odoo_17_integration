# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime


class CreditNote(http.Controller):

    @staticmethod
    def insert_credit_note(move_id, lines, response, patient, services, update=False):
        cnl = []
        for line in lines:
            service = list(filter(lambda d: d['id'] == line['product_id'], services))[0]
            price = service['company_share'] if line['payer_id'] else service['patient_share']
            if update == 'up':
                price = price - line['price_unit']
            elif update == 'down':
                price = line['price_unit'] - price
            cnl.append(CreditNote.get_cnl_vals(line, response, patient, price))
        credit_note = request.env['account.move'].sudo().browse(move_id)
        if credit_note.reversed_entry_id:
            credit_note.sudo().write({
                "partner_id": credit_note.reversed_entry_id.partner_id.id,
                "invoice_line_ids": cnl,
                "ref": 'Reversal of: ' + credit_note.reversed_entry_id.name
            })
        else:
            credit_note.sudo().write({
                "invoice_line_ids": cnl
            })

    @staticmethod
    def create_credit_note(partner, registration_date, journal_id, move_id, type='out_refund', doctor=False,
                           employee=False):
        draft_account_move = {
            'move_type': type,
            'state': 'draft',
            'currency_id': request.env.company.currency_id.id,
            'company_id': request.env.company.id,
            'date': str(registration_date),
            'invoice_date': str(registration_date),
            'partner_id': partner,
            'journal_id': journal_id,
            'create_date': str(datetime.now()),
        }
        if doctor:
            draft_account_move['doctor_id'] = doctor
        if employee:
            draft_account_move['ldm_created_by'] = employee
        if move_id:
            draft_account_move['reversed_entry_id'] = move_id
        request.env.cr.execute("""INSERT INTO account_move%s VALUES %s RETURNING id;""" % (
            str(tuple(draft_account_move.keys())).replace("'", ""), tuple(draft_account_move.values())))
        return request.env.cr.fetchall()[0][0]

    @staticmethod
    def get_cnl_vals(line, response, patient, price):
        return (
            0, 0,
            {
                'reg_key': response.get('reg_key'),
                'accession_number': response.get('accessionNumber'),
                'patient_id': patient.get('id', False),
                'product_id': line['product_id'],
                'journal_id': line['journal_id'],
                'quantity': 1,
                'price_unit': price,
                'contract_id': line['contract_id'],
                'analytic_account_id': line['analytic_account_id'],
                'representative': line['representative'],
                'center_id': line['center_id'],
                'doctor_id': line['doctor_id'],
                'service_payer_id': line['service_payer_id'],
                'name': line['name'],
                'registration_date': datetime.strptime(response.get('updateDate'), '%d/%m/%Y').date(),
            }
        )

    @staticmethod
    def search_account_move_line(reg_key, services, partner_id, partner='patient_id', type='credit'):
        cr_lines = []
        partner_qr = ''
        if partner_id:
            partner_qr = 'AND l.' + partner + ' = ' + str(partner_id.get('id', False))
        type_qr = ''
        if type == 'credit':
            type_qr = "AND l.credit > 0 AND m.move_type = 'out_invoice'"
        service_qr = ''
        if services:
            service_qr = 'AND l.product_id ' + (('IN ' + str(tuple(service['id'] for service in services))) if len(
                services) > 1 else ('= ' + str(tuple(service['id'] for service in services)[0])))
        request.env.cr.execute("""
                            SELECT l.product_id, l.parent_state, l.id, l.move_id, l.journal_id, l.payer_id, l.price_unit, l.patient_id, l.contract_id, l.analytic_account_id, l.representative, l.center_id, l.doctor_id, l.service_payer_id, l.name
                            FROM account_move_line l
                            join account_move m on l.move_id = m.id
                            WHERE reg_key = '%s'
                                AND l.is_cancelled = False
                                %s
                                %s
                                %s;""" % (
            reg_key, type_qr, service_qr, partner_qr))
        cr_obj = request.env.cr.fetchall()
        for cr in cr_obj:
            if services:
                service = list(filter(lambda d: d['id'] == cr[0], services))[0]
                cr_lines.append(
                    {'product_id': cr[0], 'state': cr[1], 'id': cr[2], 'move_id': cr[3], 'journal_id': cr[4],
                     'payer_id': cr[5], 'price_unit': cr[6], 'patient_share': service['patient_share'],
                     'company_share': service['company_share'], 'default_code': service['default_code'],
                     'patient_id': cr[7], 'contract_id': cr[8], 'analytic_account_id': cr[9], 'representative': cr[10],
                     'center_id': cr[11], 'doctor_id': cr[12], 'service_payer_id': cr[13], 'name': cr[14]})
            else:
                cr_lines.append(
                    {'product_id': cr[0], 'state': cr[1], 'id': cr[2], 'move_id': cr[3], 'journal_id': cr[4],
                     'payer_id': cr[5], 'price_unit': cr[6], 'patient_id': cr[7]})
        return cr_lines
