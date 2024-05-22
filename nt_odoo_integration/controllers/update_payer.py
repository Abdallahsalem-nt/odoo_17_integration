# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime
from .handle_response import HandleResponse
from .master_data.payer import Payer
from .master_data.service import Service
from .master_data.credit_note import CreditNote
from .master_data.patient_invoice import PatientInvoice
from .update_price import UpdatePriceVisit
from .authenticate import validate_token
from .master_data.contract import Contract

required_data = ['reg_key', 'accessionNumber', 'services', 'contract', 'updateDate']
invalid_str_data = ['reg_key', 'accessionNumber']
invalid_child_data = ['payer', 'contract', 'old_payer']


class UpdatePayerVisit(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/UpdatePayerVisit', auth='none',
                csrf=False, methods=['POST'], type='json',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='update_payer',
                invalid_child_data=invalid_child_data)
    def update_payer_visit(self):
        response = request.jsonrequest
        result = []
        if not response:
            return HandleResponse.error_response(False,
                                                 response=response,
                                                 message='Data missing',
                                                 service_type='update_payer'
                                                 )
        try:
            try:
                bool(datetime.strptime(str(request.jsonrequest.get('updateDate')), '%d/%m/%Y'))
            except ValueError:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="updateDate %s does not match format" % request.jsonrequest.get(
                                                         'updateDate'),
                                                     service_type='update_payer'
                                                     )
            payer_id = Payer.get_payer(response.get("old_payer"))
            new_payer_id = Payer.get_payer(response.get("payer"))
            services = Service.get_product(response.get("services"))
            contract_id = Contract.get_contract(response.get("contract"))

            result.extend(list(filter(lambda d: 'code' in d, services)))
            services = list(filter(lambda d: 'code' not in d, services))

            services_not_inserted = list(filter(lambda d: not d['id'], services))
            for line in services_not_inserted:
                result.append(
                    HandleResponse.error_response(line, False, 'The Service dose not exist at odoo services ', 400,
                                                  service_type='update_payer'))

            duplicated_new_payer_invoice = CreditNote.search_account_move_line(response.get('reg_key'), list(
                filter(lambda d: d['id'], services)),
                                                                               new_payer_id.get('partner_id', False),
                                                                               'service_payer_id')
            if duplicated_new_payer_invoice:
                return HandleResponse.error_response(False, response, "This update has already been done", 400,
                                                     service_type='update_payer')

            exist_account_move_line_ids = CreditNote.search_account_move_line(response.get('reg_key'), list(
                filter(lambda d: d['id'], services)), payer_id.get('partner_id', False), 'service_payer_id')
            if not exist_account_move_line_ids:
                return HandleResponse.error_response(False, response, "No Data To Update", 400,
                                                     service_type='update_payer')

            for service in exist_account_move_line_ids:
                move_id = request.env['account.move'].sudo().browse(service['move_id'])
                old_move_line = move_id.invoice_line_ids.filtered(lambda l: l.id == service['id'])
                if service['payer_id']:
                    draft_payer_invoice = PatientInvoice.search_draft_invoice(new_payer_id.get('partner_id', False),
                                                                              'draft')
                    if not draft_payer_invoice:
                        draft_payer_invoice = PatientInvoice.create_draft_invoice(new_payer_id.get('partner_id', False),
                                                                                  datetime.strptime(
                                                                                      response.get('updateDate'),
                                                                                      '%d/%m/%Y').date(),
                                                                                  service['journal_id'],
                                                                                  response.get("accessionNumber"),
                                                                                  False if not move_id.ldm_created_by else move_id.ldm_created_by.id,
                                                                                  False if not move_id.doctor_id else {
                                                                                      'id': move_id.doctor_id.id})
                    move_line_data = {
                        'reg_key': response.get('reg_key'),
                        'accession_number': response.get('accessionNumber'),
                        'name': old_move_line.patient_id.name if old_move_line.patient_id else False,
                        'patient_id': old_move_line.patient_id.id if old_move_line.patient_id else False,
                        'product_id': service.get('product_id'),
                        'journal_id': old_move_line.journal_id,
                        'quantity': 1,
                        'price_unit': service['company_share'],
                        'contract_id': contract_id,
                        'analytic_account_id': old_move_line.analytic_account_id,
                        'registration_date': datetime.strptime(response.get('updateDate'), '%d/%m/%Y').date(),
                        'representative': old_move_line.representative,
                        'center_id': old_move_line.center_id,
                        'doctor_id': old_move_line.doctor_id,
                        'payer_id': new_payer_id.get('partner_id', False).get('id'),
                        'service_payer_id': new_payer_id.get('partner_id', False).get('id'),
                    }
                    request.env['account.move'].sudo().browse(draft_payer_invoice).invoice_line_ids = [
                        (0, 0, move_line_data)]

                    if service['state'] == 'draft':
                        move_id.invoice_line_ids = [(2, old_move_line.id)]

                    else:
                        draft_invoice = CreditNote.create_credit_note(payer_id.get('partner_id', False).get('id'),
                                                                      datetime.strptime(response.get('updateDate'),
                                                                                        '%d/%m/%Y').date(),
                                                                      move_id.journal_id.id, move_id.id, 'out_refund',
                                                                      False if not move_id.doctor_id else move_id.doctor_id.id,
                                                                      False if not move_id.ldm_created_by else move_id.ldm_created_by.id)
                        credit_note = request.env['account.move'].sudo().browse(draft_invoice)
                        move_line_data['price_unit'] = old_move_line.price_unit
                        credit_note.invoice_line_ids = [(0, 0, move_line_data)]
                        credit_note.action_post()
                        move_id.reconcile_credit_note_invoices(draft_invoice)
                        request.env.cr.execute(
                            "update account_move_line set is_cancelled = True WHERE id = %s;" % str(old_move_line.id))

                    result.append(
                        HandleResponse.success_response(service, 'The Payer Updated successfully',
                                                        response.get('reg_key'), service_type='update_payer'))

                else:
                    move_id.invoice_line_ids = [
                        (1, old_move_line.id, {"service_payer_id": new_payer_id.get('partner_id', False).get('id'),
                                               "contract_id": contract_id})]

        except Exception as e:
            body = str(e).replace("'", "")
            response = str(response).replace("'", "")
            user_id = request.env.user.id
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date,create_uid ,code, body, service_type,reason, active) VALUES ('%s','%s','%s', '500', '%s','%s', '%s', True);" % (
                    str(datetime.now()), str(datetime.now()),user_id, body, 'update_payer', response))
            return {'code': 500, 'success': False, 'message': str(e)}

        UpdatePriceVisit.update_price_visit(http)
        return {'code': 200, 'success': True, 'total_result': result}
