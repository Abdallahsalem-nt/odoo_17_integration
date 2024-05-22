# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime
from .handle_response import HandleResponse
from .master_data.service import Service
from .master_data.credit_note import CreditNote
from .authenticate import validate_token

required_data = ['reg_key', 'accessionNumber', 'services', 'updateDate']
invalid_str_data = ['reg_key', 'accessionNumber']


class DeleteServiceVisit(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/DeleteServiceVisit', auth='none',
                csrf=False, methods=['POST'], type='json',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='delete_service',
                invalid_child_data=[])
    def delete_service_visit(self):
        response = request.jsonrequest
        result = []
        if not response:
            return HandleResponse.error_response(False,
                                                 response=response,
                                                 message='Data missing',
                                                 service_type='delete_service'
                                                 )
        try:
            try:
                bool(datetime.strptime(str(request.jsonrequest.get('updateDate')), '%d/%m/%Y'))
            except ValueError:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="updateDate %s does not match format" % request.jsonrequest.get(
                                                         'updateDate'),
                                                     service_type='delete_service'
                                                     )

            services = Service.get_product(response.get("services"))

            result.extend(list(filter(lambda d: 'code' in d, services)))
            services = list(filter(lambda d: 'code' not in d, services))

            services_not_inserted = list(filter(lambda d: not d['id'], services))

            for line in services_not_inserted:
                result.append(
                    HandleResponse.error_response(line, response, 'The Service dose not exist at odoo services ', 400,service_type='delete_service'))

            exist_account_move_line_ids = CreditNote.search_account_move_line(response.get('reg_key'), list(
                filter(lambda d: d['id'], services)), False)
            if not exist_account_move_line_ids:
                return HandleResponse.error_response(False, response, 'The Services Not exist at odoo', 400,service_type='delete_service')

            request.env.cr.execute(
                "SELECT id, name FROM res_partner WHERE id = '%s'" % exist_account_move_line_ids[0]['patient_id'])
            patient_id = request.env.cr.fetchall()
            patient_id = {'id': patient_id[0][0], 'name': patient_id[0][1]}

            draft_lines = list(filter(lambda d: d['state'] == 'draft', exist_account_move_line_ids))
            if draft_lines:
                for move in list(set(map(lambda o: o['move_id'], draft_lines))):
                    request.env['account.move'].sudo().browse(move).invoice_line_ids = [(2, l['id']) for l in list(
                        filter(lambda d: d['move_id'] == move, draft_lines))]

            posted_lines = list(filter(lambda d: d['state'] == 'posted', exist_account_move_line_ids))
            if posted_lines:
                for move in list(set(map(lambda o: o['move_id'], posted_lines))):
                    move_id = request.env['account.move'].sudo().browse(move)
                    draft_invoice = CreditNote.create_credit_note(patient_id['id'], datetime.strptime(
                        response.get('updateDate'),
                        '%d/%m/%Y').date(), list(
                        filter(lambda d: d['move_id'] == move, posted_lines))[0]['journal_id'], move,
                                                                  False if not move_id.doctor_id else move_id.doctor_id.id,
                                                                  False if not move_id.ldm_created_by else move_id.ldm_created_by.id)

                    CreditNote.insert_credit_note(draft_invoice,
                                                  list(filter(lambda d: d['move_id'] == move, posted_lines)),
                                                  response, patient_id, services)
                    request.env['account.move'].sudo().browse(draft_invoice).action_post()
                    move_id.reconcile_credit_note_invoices(draft_invoice)
                request.env.cr.execute("update account_move_line set is_cancelled = True WHERE id IN %s;" % list(
                    set(map(lambda o: o['id'], posted_lines))))
            for service in list(filter(lambda d: d['id'], services)):
                result.append(
                    HandleResponse.success_response(service, 'service deleted successfully', response.get('reg_key'),service_type='delete_service'))

        except Exception as e:
            body = str(e).replace("'", "")
            user_id = request.env.user.id
            response = str(response).replace("'", "")
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date,create_uid,code, body, service_type,reason, active) VALUES ('%s','%s','%s', '500', '%s','%s', '%s', True);" % (
                    str(datetime.now()), str(datetime.now()),user_id ,body,'delete_service' ,response))
            return {'code': 500, 'success': False, 'message': str(e)}

        return {'code': 200, 'success': True, 'total_result': result}
