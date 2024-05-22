# -*- coding: utf-8 -*-
import logging
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime
from .handle_response import HandleResponse
from .master_data.patient import Patient
from .master_data.branch import Branch
from .master_data.payer import Payer
from .master_data.contract import Contract
from .master_data.employee import Employee
from .master_data.service import Service
from .authenticate import validate_token
from .master_data.patient_invoice import PatientInvoice

required_data = ['reg_key', 'accession_number', 'patient', 'services', 'branch_id', 'payer', 'contract', 'cash',
                 'registeration_date', 'user_full_name']
invalid_str_data = ['reg_key', 'accession_number', 'user_full_name']
invalid_child_data = ['branch_id', 'payer', 'contract']


class InsertVisit(http.Controller):
    @validate_token
    @http.route('/api/v2/Walk_inPatient/InsertVisit', auth='none',
                csrf=False, methods=['POST'], type='json',
                special_param='ldm', required_data=required_data, invalid_str_data=invalid_str_data,
                service_type='insert_visit',
                invalid_child_data=invalid_child_data)
    def insert_visit(self):
        response = request.jsonrequest
        if not response:
            return HandleResponse.error_response(False,
                                                 response=str(response).replace("'", ""),
                                                 message='Data missing',
                                                 service_type='insert_visit'
                                                 )
        try:
            if type(response.get('cash')) not in (float, int):
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="Data Invalid Cash",
                                                     service_type='insert_visit')
            if type(response.get('discount')) not in (float, int):
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="Data Invalid Discount",
                                                     service_type='insert_visit'
                                                     )

            try:
                bool(datetime.strptime(str(request.jsonrequest.get('registeration_date')), '%d/%m/%Y'))
            except ValueError:
                return HandleResponse.error_response(False,
                                                     response=str(response).replace("'", ""),
                                                     message="registeration_date %s does not match format" % request.jsonrequest.get(
                                                         'registeration_date'),
                                                     service_type='insert_visit'
                                                     )

            patient_id = Patient.get_patient(response.get("patient"))
            branch_id = Branch.get_branch(response.get("branch_id"))
            payer_id = Payer.get_payer(response.get("payer", False), response.get("center", False),
                                       response.get("doctor", False))
            contract_id = Contract.get_contract(response.get("contract"))
            employee_id = Employee.get_employee(response.get("user_full_name"))
            services = Service.get_product(response.get("services"), True)

            invoices_lines_values = PatientInvoice.get_patient_invoice(response.get("reg_key"),
                                                                       response.get("accession_number"), services,
                                                                       datetime.strptime(
                                                                           response.get('registeration_date'),
                                                                           '%d/%m/%Y').date(),
                                                                       patient_id,
                                                                       contract_id, branch_id['journal'],
                                                                       response.get("discount"),
                                                                       branch_id['analytic'],
                                                                       payer_id,
                                                                       response.get("representative"), employee_id,
                                                                       'visit',
                                                                       service_type='insert_visit'
                                                                       )

        except Exception as e:
            body = str(e).replace("'", "")
            response = str(response).replace("'", "")
            user_id = request.env.user.id
            request.cr.execute(
                "INSERT INTO integration_log(request_date,create_date,create_uid, code, body,service_type ,reason, active) VALUES ('%s','%s','%s', '500', '%s','%s' ,'%s', True);" % (
                    str(datetime.now()),str(datetime.now()),user_id, body, 'insert_visit', response))
            return {'code': 500, 'success': False, 'message': str(e)}

        return {'code': 200, 'success': True, 'total_result': invoices_lines_values}
