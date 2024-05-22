# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from ..handle_response import HandleResponse
from datetime import datetime


class PatientInvoice(http.Controller):

    @staticmethod
    def get_patient_invoice(reg_key, accession_number, services, registration_date, patient_id, contract_id, journal,
                            discount, analytic, payer_id, representative, employee, type='visit', service_type='insert_visit'):
        result = []
        result.extend(list(filter(lambda d: 'code' in d, services)))
        services = list(filter(lambda d: 'code' not in d, services))
        if not services:
            return result
        patient_account_move_line_id = PatientInvoice.search_account_move_line(reg_key, services, patient_id)
        if patient_account_move_line_id:
            patient_account_move_line_id = list(sum(patient_account_move_line_id, ()))
            move_lines_created = list(filter(lambda d: d['id'] in patient_account_move_line_id, services))
            exist_code = 200
            exist_success = True
            if type == 'service':
                exist_code = 400
                exist_success = False
            for line in move_lines_created:
                message = "The Service (%s) already exist" % (line.get('name', False))
                HandleResponse.success_response(line, message, reg_key, service_type=service_type)
                result.append({"code": exist_code, "success": exist_success, "default_code": line.get('default_code'),
                               "message": message})
        services = list(filter(lambda d: d['id'] not in patient_account_move_line_id, services))
        if services:
            company_exist_draft_invoice_id = False
            if sum(patient['company_share'] for patient in services) > 0:
                company_exist_draft_invoice_id = PatientInvoice.search_draft_invoice(
                    payer_id['center_id'] if payer_id['center_id'] else payer_id['partner_id'], 'draft')
                if not company_exist_draft_invoice_id:
                    company_exist_draft_invoice_id = PatientInvoice.create_draft_invoice(
                        payer_id['center_id'] if payer_id['center_id'] else payer_id['partner_id'],
                        registration_date,
                        journal, accession_number,
                        employee,
                        payer_id['doctor_id'])

            inv_lines = []
            company_inv_lines = []
            for service in services:
                if service['patient_share'] > 0:
                    inv_lines.append(PatientInvoice.get_aml_vals(
                        reg_key, accession_number, patient_id, contract_id, service, journal,
                        analytic, {'payer': payer_id['partner_id'], 'center_id': payer_id['center_id'],
                                   'doctor_id': payer_id['doctor_id']}, registration_date, representative,
                        service.get('patient_share', 0.0)))
                if service['company_share'] > 0:
                    company_inv_lines.append(PatientInvoice.get_aml_vals(
                        reg_key, accession_number, patient_id, contract_id, service, journal,
                        analytic, payer_id, registration_date, representative, service.get('company_share', 0.0)))
                message = "The Service %s has been registered successfully" % service.get(
                    'name', False)
                HandleResponse.success_response(service, message, reg_key, service_type=service_type)
                result.append(
                    {"code": 200, "success": True, "default_code": service.get('default_code'), "message": message})
            patient_exist_draft_invoice_id = PatientInvoice.search_draft_invoice(patient_id, 'draft')
            if inv_lines:
                if not patient_exist_draft_invoice_id:
                    patient_exist_draft_invoice_id = PatientInvoice.create_draft_invoice(patient_id, registration_date,
                                                                                         journal, accession_number,
                                                                                         employee,
                                                                                         payer_id['doctor_id'])
                if discount > 0:
                    print(discount)
                    request.env.cr.execute("SELECT id FROM product_product WHERE default_code = 'INT-DISC';")
                    discount_product = request.env.cr.fetchall()
                    if discount_product:
                        request.env.cr.execute("""
                        SELECT id FROM account_move_line WHERE reg_key = '%s' 
                        AND product_id = '%s' 
                        AND move_id = '%s';""" % (reg_key, discount_product[0][0], patient_exist_draft_invoice_id))
                        if not request.env.cr.fetchall():
                            inv_lines.append(PatientInvoice.get_aml_vals(
                                reg_key, accession_number, patient_id, contract_id, {'id': discount_product[0][0]},
                                journal,
                                analytic, {'payer': payer_id['partner_id'], 'center_id': payer_id['center_id'],
                                           'doctor_id': payer_id['doctor_id']}, registration_date, representative,
                                (discount * -1)))
                PatientInvoice.update_draft_invoice(patient_exist_draft_invoice_id, inv_lines)
            if company_exist_draft_invoice_id:
                PatientInvoice.update_draft_invoice(company_exist_draft_invoice_id, company_inv_lines)
        return result

    @staticmethod
    def search_account_move_line(reg_key, services, partner_id):
        sr_qu = ('product_id IN ' + str(tuple(service['id'] for service in services))) if len(services) > 1 else (
                'product_id = ' + str(tuple(service['id'] for service in services)[0]))
        request.env.cr.execute("""
                            SELECT product_id
                            FROM account_move_line
                            WHERE reg_key = '%s'
                                AND %s
                                AND patient_id = '%s';""" % (
            reg_key, sr_qu, partner_id.get('id', False)))
        am_obj = request.env.cr.fetchall()
        return am_obj if am_obj else []

    @staticmethod
    def search_draft_invoice(partner_id, state=''):
        if state:
            state = "AND state = 'draft'"
        request.env.cr.execute("""
        SELECT id 
        FROM account_move 
        WHERE partner_id = '%s'
        AND move_type = 'out_invoice'
        %s;""" % (partner_id.get('id', False), state))
        am_obj = request.env.cr.fetchall()

        return am_obj[0][0] if am_obj else False

    @staticmethod
    def create_draft_invoice(partner, registration_date, journal_id, accession_number, employee, doctor_id):
        draft_account_move = {
            'move_type': 'out_invoice',
            'state': 'draft',
            'currency_id': request.env.company.currency_id.id,
            'company_id': request.env.company.id,
            'date': str(registration_date),
            'invoice_date': str(registration_date),
            'partner_id': partner.get('id', False),
            'journal_id': journal_id,
            'accession_number': accession_number,
            'create_date': str(datetime.now()),
        }
        if doctor_id:
            if 'id' in doctor_id:
                draft_account_move['doctor_id'] = doctor_id['id']
        if employee:
            draft_account_move['user_full_name'] = employee
            draft_account_move['ldm_created_by'] = employee
        request.env.cr.execute("""INSERT INTO account_move%s VALUES %s RETURNING id;""" % (
            str(tuple(draft_account_move.keys())).replace("'", ""), tuple(draft_account_move.values())))
        return request.env.cr.fetchall()[0][0]

    @staticmethod
    def update_draft_invoice(draft_invoice_id, invoice_line_ids):
        request.env['account.move'].sudo().browse(draft_invoice_id).invoice_line_ids = invoice_line_ids

    @staticmethod
    def get_aml_vals(reg_key, accession_number, patient, contract_id, product_id, journal_id,
                     analytic_account_id, payer, registration_date, representative, value_share, ):
        dic = {
            'reg_key': reg_key,
            'accession_number': accession_number,
            'name': patient.get('name', False),
            'patient_id': patient.get('id', False),
            'contract_id': contract_id,
            'product_id': product_id.get('id'),
            'journal_id': journal_id,
            'analytic_account_id': analytic_account_id,
            'registration_date': registration_date,
            'quantity': 1,
            'price_unit': value_share,
            'representative': representative,
        }
        if payer:
            if 'center_id' in payer:
                dic['center_id'] = payer['center_id'].get('id') if payer['center_id'] else False,
            if 'doctor_id' in payer:
                dic['doctor_id'] = payer['doctor_id'].get('id') if payer['doctor_id'] else False,
            if 'partner_id' in payer:
                dic['payer_id'] = payer['partner_id'].get('id') if payer['partner_id'] else False,
                dic['service_payer_id'] = payer['partner_id'].get('id') if payer['partner_id'] else False,
            if 'payer' in payer:
                dic['service_payer_id'] = payer['payer'].get('id') if payer['payer'] else False,
        return (0, 0, dic)
