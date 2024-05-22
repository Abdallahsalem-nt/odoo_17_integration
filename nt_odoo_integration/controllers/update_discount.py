# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime
from .handle_response import HandleResponse
from .authenticate import validate_token
from .master_data.credit_note import CreditNote

required_data = ['reg_key', 'accessionNumber', 'updateDate']
invalid_str_data = ['reg_key', 'accessionNumber']


class UpdateDiscountVisit(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/UpdateDiscount', auth='none',
                csrf=False, methods=['POST'], type='json',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='update_discount',
                invalid_child_data=[])
    def update_discount_visit(self):
        response = request.jsonrequest
        result = []
        if not response:
            return HandleResponse.error_response(False,
                                                 response=response,
                                                 message='Data missing',
                                                 service_type='update_discount'
                                                 )
        try:
            try:
                bool(datetime.strptime(str(request.jsonrequest.get('updateDate')), '%d/%m/%Y'))
            except ValueError:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="updateDate %s does not match format" % request.jsonrequest.get(
                                                         'updateDate'),
                                                     service_type='update_discount'
                                                     )

            if type(response.get('discount')) not in (float, int):
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="Data Invalid Discount",
                                                     service_type='update_discount'
                                                     )

            request.env.cr.execute("SELECT id FROM product_product WHERE default_code = 'INT-DISC';")
            discount_product = request.env.cr.fetchall()[0][0]

            discount_line = CreditNote.search_account_move_line(response.get('reg_key'), [
                {'id': discount_product, 'patient_share': False, 'company_share': False, 'default_code': False}],
                                                                False, False, 'debit')

            if not discount_line:
                return HandleResponse.error_response(False, False, 'The Invoices dose not exist at odoo ', 400,service_type='update_discount')

            if len(discount_line) > 1:
                return HandleResponse.error_response(False, False, 'The discount has been previously updated ', 400,service_type='update_discount')
            discount_line = discount_line[0]
            price_unit = (response.get('discount') * -1)
            if discount_line['price_unit'] == price_unit:
                return HandleResponse.error_response(False, False, 'The discount has been previously updated ', 400,service_type='update_discount')

            old_move_id = request.env['account.move'].sudo().browse(discount_line['move_id'])

            if discount_line['state'] == 'draft':
                old_move_id.invoice_line_ids = [(1, discount_line['id'], {"price_unit": price_unit})]
            else:
                if discount_line['price_unit'] < price_unit:
                    move_type = 'out_invoice'
                    move = False
                    price = 'up'

                else:
                    move_type = 'out_refund'
                    move = discount_line['move_id']
                    price = 'down'

                draft_invoice = CreditNote.create_credit_note(discount_line['patient_id'],
                                                              datetime.strptime(response.get('updateDate'),
                                                                                '%d/%m/%Y').date(),
                                                              discount_line['journal_id'], move, move_type,
                                                              discount_line.get('doctor_id', False), False)
                CreditNote.insert_credit_note(draft_invoice, [discount_line], response,
                                              {'id': discount_line['patient_id']},
                                              [{'id': discount_product, 'patient_share': price_unit}], price)
                request.env['account.move'].sudo().browse(draft_invoice).action_post()
                old_move_id.reconcile_credit_note_invoices(draft_invoice)

            result.append({"code": 200, "success": True, "message": "Updated successfully"})
        except Exception as e:
            body = str(e).replace("'", "")
            response = str(response).replace("'", "")
            user_id = request.env.user.id
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date,create_uid,code, body, service_type,reason, active) VALUES ('%s','%s','%s','500', '%s','%s', '%s', True);" % (
                    str(datetime.now()),str(datetime.now()),user_id, body, 'update_discount',response))
            return {'code': 500, 'success': False, 'message': str(e)}

        return {'code': 200, 'success': True, 'total_result': result}
