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


class UpdatePriceVisit(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/UpdatePriceVisit', auth='none',
                csrf=False, methods=['POST'], type='json',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='update_price',
                invalid_child_data=[])
    def update_price_visit(self):
        response = request.jsonrequest
        result = []
        if not response:
            return HandleResponse.error_response(False,
                                                 response=response,
                                                 message='Data missing',
                                                 service_type='update_price'
                                                 )
        try:
            try:
                bool(datetime.strptime(str(request.jsonrequest.get('updateDate')), '%d/%m/%Y'))
            except ValueError:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="updateDate %s does not match format" % request.jsonrequest.get(
                                                         'updateDate'),
                                                     service_type='update_price'
                                                     )

            services = Service.get_product(response.get("services"))

            result.extend(list(filter(lambda d: 'code' in d, services)))
            services = list(filter(lambda d: 'code' not in d, services))

            services_not_inserted = list(filter(lambda d: not d['id'], services))
            services = list(filter(lambda d: d['id'], services))

            for line in services_not_inserted:
                message = "The Service dose not exist at odoo services"
                HandleResponse.success_response(line, message, response.get('reg_key'), service_type='update_price')
                result.append(
                    {"code": 400, "success": False, "default_code": line.get('default_code'), "message": message})

            if not services:
                return {'code': 200, 'success': True, 'total_result': result}

            move_line_ids = CreditNote.search_account_move_line(response.get('reg_key'), list(
                filter(lambda d: d['id'], services)), False)

            if not move_line_ids:
                return HandleResponse.error_response(False, False, 'The Invoices dose not exist at odoo ', 400,
                                                     service_type='update_price')

            draft_lines = list(filter(lambda d: d['state'] == 'draft', move_line_ids))
            if draft_lines:
                for move in list(set(map(lambda o: o['move_id'], draft_lines))):
                    request.env['account.move'].sudo().browse(move).invoice_line_ids = [
                        (1, l['id'], {"price_unit": l['company_share'] if l['payer_id'] else l['patient_share']}) for l
                        in list(
                            filter(lambda d: d['move_id'] == move, draft_lines))]

            posted_lines = list(filter(lambda d: d['state'] == 'posted', move_line_ids))
            if posted_lines:
                for move in list(set(map(lambda o: o['move_id'], posted_lines))):
                    move_id = request.env['account.move'].sudo().browse(move)
                    lines = list(filter(lambda d: d['move_id'] == move, posted_lines))
                    up_price = list(
                        filter(
                            lambda l: l['price_unit'] < (l['company_share'] if l['payer_id'] else l['patient_share']),
                            lines))
                    down_price = list(
                        filter(
                            lambda l: l['price_unit'] > (l['company_share'] if l['payer_id'] else l['patient_share']),
                            lines))
                    line_data = list(filter(lambda d: d['move_id'] == move, posted_lines))[0]

                    if up_price:
                        draft_invoice = CreditNote.create_credit_note(
                            line_data['payer_id'] if line_data['payer_id'] else line_data['patient_id'],
                            datetime.today(), line_data['journal_id'], False, 'out_invoice',
                            False if not move_id.doctor_id else move_id.doctor_id.id,
                            False if not move_id.ldm_created_by else move_id.ldm_created_by.id)
                        CreditNote.insert_credit_note(draft_invoice, up_price, response,
                                                      {'id': line_data['patient_id']}, services, 'up')
                        request.env['account.move'].sudo().browse(draft_invoice).action_post()
                        move_id.reconcile_credit_note_invoices(draft_invoice)

                    if down_price:
                        draft_invoice = CreditNote.create_credit_note(
                            line_data['payer_id'] if line_data['payer_id'] else line_data['patient_id'],
                            datetime.today(), line_data['journal_id'], move, 'out_refund',
                            False if not move_id.doctor_id else move_id.doctor_id.id,
                            False if not move_id.ldm_created_by else move_id.ldm_created_by.id)
                        CreditNote.insert_credit_note(draft_invoice, down_price, response,
                                                      {'id': line_data['patient_id']}, services, 'down')
                        request.env['account.move'].sudo().browse(draft_invoice).action_post()
                        move_id.reconcile_credit_note_invoices(draft_invoice)

            for service in list(filter(lambda d: d['id'], services)):
                result.append(HandleResponse.success_response(service, 'The service price updated successfully',
                                                              response.get('reg_key'), service_type='update_price'))

        except Exception as e:
            body = str(e).replace("'", "")
            response = str(response).replace("'", "")
            user_id = request.env.user.id
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date, create_uid,code, body,service_type ,reason, active) VALUES ('%s','%s','%s' ,'500', '%s','%s', '%s', True);" % (
                    str(datetime.now()),str(datetime.now()),user_id, body, 'update_price', response))
            return {'code': 500, 'success': False, 'message': str(e)}

        return {'code': 200, 'success': True, 'total_result': result}
