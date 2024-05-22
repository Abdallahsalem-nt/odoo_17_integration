# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request


class Payment(http.Controller):

    @staticmethod
    def get_payment(patient_id, reg_key, receipt_no, payment_date):
        request.env.cr.execute("""
        SELECT id 
        FROM account_payment 
        WHERE partner_id = '%s'
        AND reg_key = '%s'
        AND receipt_no = '%s'
        AND ldm_payment_date = '%s';""" % (patient_id.get('id'), reg_key, receipt_no, payment_date))
        payment_id = request.env.cr.fetchall()
        return payment_id[0][0] if payment_id else False

    @staticmethod
    def get_payment_journal(payment_method):
        if payment_method == 'Cash':
            payment_type = 'cash'
        elif payment_method == 'Visa':
            payment_type = 'bank'
        else:
            return False
        request.env.cr.execute("""
        SELECT id 
        FROM account_journal
        WHERE code = '%s';""" % ('D' + payment_method.upper()))
        journal_id = request.env.cr.fetchall()
        if not journal_id:
            request.cr.execute(
                "INSERT INTO account_journal(name, type, code, invoice_reference_type, invoice_reference_model, company_id, active) VALUES('%s', '%s', '%s', 'invoice', 'odoo', 1, True) RETURNING id;" % (
                    payment_type, payment_method, 'D' + payment_method.upper()))
            journal_id = request.env.cr.fetchall()
        return journal_id[0][0]

    @staticmethod
    def insert_payment(payment):
        request.env.cr.execute("""INSERT INTO account_payment%s VALUES %s RETURNING id;""" % (
            str(tuple(payment.keys())).replace("'", ""), tuple(payment.values())))
        payment_id = request.env.cr.fetchall()
        return payment_id
