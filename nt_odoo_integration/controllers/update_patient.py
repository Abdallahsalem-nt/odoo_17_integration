# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from .handle_response import HandleResponse
from .master_data.patient import Patient
from .master_data.credit_note import CreditNote
from .authenticate import validate_token
from datetime import datetime

required_data = ['reg_key', 'accessionNumber', 'patient']
invalid_str_data = ['reg_key', 'accessionNumber']


class UpdatePatientVisit(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/UpdatePatientVisit', auth='none',
                csrf=False, methods=['POST'], type='json',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='update_patient',
                invalid_child_data=[])
    def update_patient_visit(self):
        response = request.jsonrequest
        if not response:
            return HandleResponse.error_response(False,
                                                 response=response,
                                                 message='Data missing',
                                                 service_type='update_patient'
                                                 )
        try:
            new_patient_id = Patient.get_patient(response.get("patient"))
            request.env['res.partner'].sudo().browse(new_patient_id.get('id')).write({'name': response.get("patient").get('name')})
            request.env.cr.execute("SELECT id FROM account_move_line WHERE patient_id = '%s'" % new_patient_id.get('id'))
            exist_move_lines = request.env.cr.fetchall()
            if exist_move_lines:
                request.env.cr.execute("update account_move_line set name = '%s' WHERE id IN %s;" % (
                    response.get("patient").get('name'), str(tuple(line[0] for line in exist_move_lines))))

            # exist_account_move_line_ids = CreditNote.search_account_move_line(response.get('reg_key'), False, False,
            #                                                                   False)
            # if not exist_account_move_line_ids:
            #     return HandleResponse.error_response(False, False, 'The Invoices dose not exist at odoo ', 400)
            #
            # draft_lines = list(filter(lambda d: d['state'] == 'draft', exist_account_move_line_ids))
            # if draft_lines:
            #     for move in list(set(map(lambda o: o['move_id'], draft_lines))):
            #         move_id = request.env['account.move'].sudo().browse(move)
            #         if not list(filter(lambda d: d['move_id'] == move, draft_lines))[0]['payer_id']:
            #             move_id.partner_id = new_patient_id.get('id')
            #         move_id.invoice_line_ids = [(1, m.id, {'partner_id': new_patient_id.get('id')}) for m in
            #                                     move_id.invoice_line_ids]
            #
            # posted_lines = list(filter(lambda d: d['state'] == 'posted', exist_account_move_line_ids))
            # if posted_lines:
            #     for move in list(set(map(lambda o: o['move_id'], posted_lines))):
            #         move_id = request.env['account.move'].sudo(2).browse(move)
            #         move_id.invoice_line_ids = [(1, m.id, {'partner_id': new_patient_id.get('id')}) for m in
            #                                     move_id.invoice_line_ids]
            #         if not list(filter(lambda d: d['move_id'] == move, posted_lines))[0]['payer_id']:
            #             move_id.copy({'partner_id': new_patient_id.get('id')})
            #             move_id._reverse_moves(cancel=True)
            #             request.env.cr.execute("update account_move_line set is_cancelled = True WHERE id IN %s;" % str(
            #                 tuple(line.id for line in move_id.invoice_line_ids)))

            request.env.cr.execute(
                "INSERT INTO integration_log(request_date,create_date, code, body, service_type,reason, active) VALUES ('%s','%s', '200', '%s','%s', '%s', True);" % (
                    str(datetime.now()),str(datetime.now()), str(response).replace("'", ""), 'update_patient',"Patient Updated successfully"))

        except Exception as e:
            body = str(e).replace("'", "")
            response = str(response).replace("'", "")
            user_id = request.env.user.id
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date,create_uid,code, body, service_type,reason, active) VALUES ('%s','%s','%s' ,'500', '%s','%s', '%s', True);" % (
                    str(datetime.now()), str(datetime.now()),user_id, body,'update_patient',response))
            return {'code': 500, 'success': False, 'message': str(e)}

        return {"code": 200, "success": True,
                "total_result": [{"code": 200, "success": True, "message": "Patient Updated successfully"}]}
