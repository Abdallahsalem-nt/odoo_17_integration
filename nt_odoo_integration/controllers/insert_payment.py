# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime
from .handle_response import HandleResponse
from .master_data.patient import Patient
from .master_data.branch import Branch
from .master_data.payment import Payment
from .authenticate import validate_token
from .master_data.employee import Employee

required_data = ['reg_key', 'accession_number', 'amount', 'branch_id', 'patient', 'payment_method', 'payment_type',
                 'payment_date', 'user_full_name', 'receipt_no']
invalid_child_data = ['branch_id']
invalid_str_data = ['reg_key', 'accession_number', 'user_full_name', 'payment_method', 'receipt_no']


class InsertPayment(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/Payment', auth='none',
                csrf=False, methods=['POST'], type='json',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='insert_payment',
                invalid_child_data=invalid_child_data)
    def insert_payment(self):
        response = request.get_json_data()
        if not response:
            return HandleResponse.error_response(False,
                                                 response=response,
                                                 message='Data missing',
                                                 service_type='insert_payment')
        try:
            if type(response.get('amount')) not in (float, int) or response.get('amount') <= 0:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="Data Invalid amount",
                                                     service_type='insert_payment')

            try:
                bool(datetime.strptime(str(response.get('payment_date')), '%d/%m/%Y'))
            except ValueError:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="payment_date %s does not match format" % request.jsonrequest.get(
                                                         'payment_date'),
                                                     service_type='insert_payment')

            patient_id = Patient.get_patient(response.get("patient"))
            payment_date = datetime.strptime(response.get("payment_date"), '%d/%m/%Y').date()
            employee_id = Employee.get_employee(response.get("user_full_name"))

            if response.get('payment_type') not in ['payment', 'refund']:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="Data Invalid payment_type should be payment or refund",
                                                     service_type='insert_payment')

            search_for_previous_account_payment = Payment.get_payment(patient_id, response.get("reg_key"),
                                                                      response.get("receipt_no"), payment_date)
            if search_for_previous_account_payment:
                return HandleResponse.error_response(False, {}, 'This Payment Already Exist',
                                                     service_type='insert_payment')

            payment_journal = Payment.get_payment_journal(response.get("payment_method"))
            if not payment_journal:
                message = "Send Payment Method Cash or Visa"
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message=message,
                                                     service_type='insert_payment'
                                                     )

            branch_id = Branch.get_branch(response.get("branch_id"), payment_journal)
            request.env.cr.execute(
                "SELECT id FROM account_payment_method_line WHERE name = 'Manual' AND journal_id = %s;" % branch_id.get(
                    'journal'))
            manual_id = request.env.cr.fetchall()[0][0]

            payment_type = False
            if response.get("payment_type") == 'payment':
                payment_type = 'inbound'
            elif response.get("payment_type") == 'refund':
                payment_type = 'outbound'

            payment = {
                'accession_number': response.get("accession_number"),
                'amount': int(response.get("amount")),
                'payment_type': payment_type,
                'date': payment_date,
                'reg_key': response.get("reg_key"),
                'receipt_no': response.get("receipt_no"),
                'ldm_payment_date': payment_date,
                'ldm_payment_amount': int(response.get("amount")),
                'partner_id': patient_id.get('id'),
                'payment_method': response.get("payment_method").lower(),
                # @todo: equal to payment_method_line_id in v 17
                'payment_method_line_id': manual_id,
                'journal_id': branch_id.get('journal'),
                'branch_id': branch_id.get('analytic'),
                'payment_method_journal_id': payment_journal,
                'user_full_name': employee_id,
            }

            payment_id = request.env['account.payment'].sudo().create(payment)
            payment_id.action_post()

        except Exception as e:
            body = str(e).replace("'", "")
            response = str(response).replace("'", "")
            user_id = request.env.user.id
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date,create_uid ,code, body, service_type, reason, active) VALUES ('%s','%s','%s', '500', '%s','%s' ,'%s', True);" % (
                    str(datetime.now()), str(datetime.now()), user_id, body, 'insert_payment', response))
            return {'code': 500, 'success': False, 'message': str(e)}

        user_id = request.env.user.id
        request.cr.execute(
            "INSERT INTO integration_log(request_date,create_date ,create_uid,code, body,service_type,reason, active) VALUES ('%s','%s','%s', '200', '%s','%s', '%s', True);" % (
                str(datetime.now()), str(datetime.now()), user_id, str(response).replace("'", ""), 'insert_payment',
                "The Payment has been created successfully"))
        return request.make_json_response(
            {'code': 200, 'success': True, 'message': "The Payment has been created successfully"}, status=200)
