# -*- coding: utf-8 -*-
import logging
from odoo import http, models, _, api
from odoo.http import request, Response

import json
from odoo.exceptions import AccessDenied
import functools
import datetime as DT

_logger = logging.getLogger(__name__)

date_format = '%m/%d/%Y'
success_message = 'The Service  ( {} : {} )  with send key ( {} )  created successfully '
error_message = 'The Service  ( {} : {} )  with send key ( {} ) already exist '
product_error_message = 'The Service dose not exist at odoo services '
change_center_message = 'Center has been changed successfully'
reference_message = 'Reversal of: %(move_name)s'
headers = [
    ('Content-Type', 'application/json'),
]
required_services_data = ['default_code', 'name', 'patient_share', 'company_share']


def validate_params(required_data=None, invalid_str_data=None, invalid_child_data=None):
    def decorator(func):
        @functools.wraps(func)
        def wrap(self, *args, **kwargs):
            response = request.jsonrequest
            # ******************** Check Data ********************
            required_data = request.endpoint.routing.get('required_data', False)
            invalid_str_data = request.endpoint.routing.get('invalid_str_data', False)
            invalid_child_data = request.endpoint.routing.get('invalid_child_data', False)
            service_type = request.endpoint.routing.get('service_type', False)
            user_id = request.env.user.id
            # ********** Missing Data **********
            if required_data:
                dif = list(set(required_data) - set(list(request.jsonrequest.keys())))
                dif.extend(
                    [i + ': code' for i in invalid_child_data if
                     set(['code']) - set(list(request.jsonrequest.get(i).keys()))])
                dif.extend(
                    [i + ': name' for i in invalid_child_data if
                     set(['name']) - set(list(request.jsonrequest.get(i).keys()))])
                if dif:
                    message = "Data missing " + str(dif).replace("'", "")
                    request.cr.execute(
                        "INSERT INTO integration_log(request_date, create_date,create_uid,code, body,service_type, reason, active) VALUES ('%s','%s','%s', '400', '%s','%s', '%s', True);" % (
                            str(DT.datetime.now()), str(DT.datetime.now()), user_id,
                            str(request.jsonrequest).replace("'", ""), service_type, message))
                    return {
                        'code': 400,
                        'success': False,
                        'message': message
                    }

            # ********** Invalid Data **********
            if invalid_str_data:
                invalid_data = [i for i in invalid_str_data if
                                type(request.jsonrequest.get(i)) != str or len(request.jsonrequest.get(i)) < 1]
                invalid_data.extend(i + ': code' for i in invalid_child_data if
                                    (type(request.jsonrequest.get(i)['code']) != str or len(
                                        request.jsonrequest.get(i)['code']) < 1))
                invalid_data.extend(i + ': name' for i in invalid_child_data if
                                    (type(request.jsonrequest.get(i)['name']) != str or len(
                                        request.jsonrequest.get(i)['name']) < 1))

                if invalid_data:
                    message = "Data Invalid " + str(invalid_data).replace("'", "")
                    request.cr.execute(
                        "INSERT INTO integration_log(request_date,create_date,create_uid, code, body, reason, active) VALUES ('%s','%s', '400', '%s','%s', '%s', True);" % (
                            str(DT.datetime.now()), str(DT.datetime.now()), user_id,
                            str(request.jsonrequest).replace("'", ""), service_type, message))
                    return {
                        'code': 400,
                        'success': False,
                        'message': message
                    }

            if 'patient' in request.jsonrequest:
                patient = request.jsonrequest.get('patient')
                if list(set(['patientNumber']) - set(list(patient.keys()))):
                    message = "Data missing patient [patientNumber]"
                    request.cr.execute(
                        "INSERT INTO integration_log(request_date,create_date,create_uid, code, body, reason, active) VALUES ('%s',%s',%s', '400', '%s','%s', '%s', True);" % (
                            str(DT.datetime.now()), str(DT.datetime.now()), user_id,
                            str(request.jsonrequest).replace("'", ""), service_type, message))
                    return {
                        'code': 400,
                        'success': False,
                        'message': message
                    }
                if list(set(['name']) - set(list(patient.keys()))):
                    message = "Data missing patient [name]"
                    request.cr.execute(
                        "INSERT INTO integration_log(request_date, create_date,create_uid,code, body, reason, active) VALUES ('%s',%s',%s', '400', '%s', '%s','%s', True);" % (
                            str(DT.datetime.now()), str(DT.datetime.now()), user_id,
                            str(request.jsonrequest).replace("'", ""), service_type, message))
                    return {
                        'code': 400,
                        'success': False,
                        'message': message
                    }

                if type(patient['patientNumber']) != str or len(patient['patientNumber']) < 1:
                    message = "Data Invalid patient [patientNumber]"
                    request.cr.execute(
                        "INSERT INTO integration_log(request_date,create_date,create_uid, code, body, reason, active) VALUES ('%s','%s','%s', '400', '%s', '%s','%s', True);" % (
                            str(DT.datetime.now()), str(DT.datetime.now()), user_id,
                            str(request.jsonrequest).replace("'", ""), service_type, message))
                    return {
                        'code': 400,
                        'success': False,
                        'message': message
                    }

                if type(patient['name']) != str or len(patient['name']) < 1:
                    message = "Data Invalid patient [name]"
                    request.cr.execute(
                        "INSERT INTO integration_log(request_date,create_date,create_uid, code, body, reason, active) VALUES ('%s','%s','%s', '400', '%s', '%s','%s', True);" % (
                            str(DT.datetime.now()), str(DT.datetime.now()), user_id,
                            str(request.jsonrequest).replace("'", ""), service_type, message))
                    return {
                        'code': 400,
                        'success': False,
                        'message': message
                    }

        return func(self, *args, **kwargs)

        return wrap

    return decorator


def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            result = {'code': 401, 'success': False,
                      'message': "access token not found, missing access token in request header"}
            return request.make_json_response(result, status=200)
        user_id = request.env["res.users.apikeys"]._check_credentials(scope="rpc", key=access_token)
        if not user_id:
            result = {'code': 401, 'success': False,
                      'message': "Authentication Failed"}
            return request.make_json_response(result, status=200)
        request.env.cr.execute(f'''
                            SELECT create_date
                            FROM res_users_apikeys WHERE index= '{access_token[:8]}' LIMIT 1;
                        ''')
        results = request.env.cr.fetchall()
        if results:
            result = results[0][0]
            today = DT.date.today()
            if today > result.date():
                token_expiration_check = (today - result.date()).days
                if token_expiration_check > 7:
                    result = {'code': 401, 'success': False,
                              'message': "Session Expired"}
                    return result
        # update request session user new method update_env in v17
        # request.session.uid = user_id
        # cant change user direct any more use this fun
        request.update_env(user=user_id)
        return func(self, *args, **kwargs)

    return wrap


class TokenAuthenticate(http.Controller):

    @http.route('/Token/Authenticate', methods=["POST"], type="http", csrf=False, auth="none")
    def get_token(self, *args, **kwargs):
        """
        notes:
        fun  handle auth rout return purse json object :
       1- make sure route type :http note json
       2- wrap rpayload make_json_response()
        :param args:
        :param kwargs:
        :return: {
                    code:'respnse code'
                    success : sucess status,
                    payload : payload

                    }
        """
        try:
            byte_string = request.httprequest.data
            data = json.loads(byte_string.decode('utf-8'))
            username = data['username']
            password = data['password']
            db = data['db']
            user_id = request.session.authenticate(db, username, password)
        except AccessDenied as e:
            result = {'code': 401, 'success': False, 'message': str(e)}
            return result
        except Exception as e:
            result = {'code': 400, 'success': False, 'message': str(e)}
            return result
        env = request.env(user=request.env.user.sudo().browse(user_id))
        token = env['res.users.apikeys'].sudo()._generate('rpc', username)
        request.env.cr.execute(f'''
                                SELECT api_key.id
                                FROM res_users_apikeys api_key 
                                WHERE user_id = {user_id} and index != '{token[:8]}';
                                ''')
        query_results = request.env.cr.fetchall()
        if query_results:
            query_results = [item[0] for item in query_results]
            for query_result in query_results:
                request.env.cr.execute(f'''
                                        DELETE 
                                        FROM res_users_apikeys api_key 
                                        WHERE api_key.id = '{query_result}';
                                            ''')
        payload = {
            'user_id': user_id,
            'token': token

        }
        result = {'code': 200, 'success': True, 'message': payload}
        return request.make_json_response(result, status=200)
