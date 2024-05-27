# -*- coding: utf-8 -*-
import logging
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime
from .handle_response import HandleResponse
from .master_data.payer import Payer
from .master_data.service import Service
from .authenticate import validate_token
from .master_data.patient_invoice import PatientInvoice

required_data = ['reg_key', 'accessionNumber', 'services', 'updateDate']
invalid_str_data = ['reg_key', 'accessionNumber']
invalid_child_data = ['payer']


class InsertService(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/InsertService', auth='none',
                csrf=False, methods=['POST'], type='http',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='insert_service',
                invalid_child_data=invalid_child_data)
    def insert_service(self):
        # get_json_data replaced request.jsonrequest
        response = request.get_json_data()
        if not response:
            return HandleResponse.error_response(False,
                                                 response=str(response).replace("'", ""),
                                                 message='Data missing',
                                                 service_type='insert_service'
                                                 )
        try:
            try:
                bool(datetime.strptime(str(response.get('updateDate')), '%d/%m/%Y'))
            except ValueError:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="updateDate %s does not match format" % response.get(
                                                         'updateDate'),
                                                     service_type='insert_service'

                                                     )

            request.env.cr.execute("""SELECT name, patient_id, journal_id,analytic_distribution, contract_id
            FROM account_move_line WHERE reg_key = '%s' AND payer_id IS NULL""" % response.get("reg_key"))
            move_lines = request.env.cr.fetchall()
            if not move_lines:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="No previous invoices",
                                                     service_type='insert_service'
                                                     )
            payer_id = Payer.get_payer(response.get("payer", False))
            services = Service.get_product(response.get("services"), True)
            analytic = next(iter(move_lines[0][3]))
            invoices_lines_values = PatientInvoice.get_patient_invoice(response.get("reg_key"),
                                                                       response.get("accession_number"),
                                                                       services,
                                                                       datetime.strptime(response.get('updateDate'),
                                                                                         '%d/%m/%Y').date(),
                                                                       {'id': move_lines[0][1],
                                                                        'name': move_lines[0][0]},
                                                                       move_lines[0][4],
                                                                       move_lines[0][2],
                                                                       0,
                                                                       analytic,
                                                                       payer_id,
                                                                       False,
                                                                       False,
                                                                       'service',
                                                                       service_type='insert_service')

        except Exception as e:
            body = str(e).replace("'", "")
            request.cr.rollback()
            response = str(response).replace("'", "")
            user_id = request.env.user.id
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date, create_uid,code, body, service_type,reason, active) VALUES ('%s','%s','%s', '500', '%s','%s', '%s', True);" % (
                    str(datetime.now()), str(datetime.now()), user_id, body, 'insert_service', response))
            return request.make_json_response({'code': 500, 'success': False, 'message': str(e)})

        return request.make_json_response({'code': 200, 'success': True, 'total_result': invoices_lines_values})
