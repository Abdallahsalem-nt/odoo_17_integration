# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
import passlib.context
import random
import string
import functools


def check_validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            result = {'code': 401, 'success': False,
                      'message': "access token not found, missing access token in request header"}
            return result
        request.env.cr.execute("SELECT id FROM res_users WHERE auth_token = '%s';" % access_token)
        user_id = request.env.cr.fetchall()
        if not user_id:
            result = {'code': 401, 'success': False,
                      'message': "Authentication Failed"}
            return result
        return func(self, *args, **kwargs)
    return wrap


class SigninAuth(http.Controller):
    @http.route('/api/v2/Walk_inPatient/SignIn', auth='none', csrf=False, methods=['POST'], type='json',
                special_param='ldm')
    def sign_in(self):
        response = request.jsonrequest
        request.env.cr.execute("SELECT id FROM res_users WHERE login = '%s';" % response.get('username', False))
        user = request.env.cr.fetchall()
        if user:
            password = response.get('password', False)
            assert password
            request.env.cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user[0][0]])
            [hashed] = request.env.cr.fetchone()
            valid, replacement = passlib.context.CryptContext(['pbkdf2_sha512', 'plaintext'], deprecated=['plaintext'],
                                                              pbkdf2_sha512__rounds=600_000).verify_and_update(password,
                                                                                                               hashed)
            if valid:
                token = ''.join(random.choices((string.ascii_letters + string.digits), k=40))
                request.env.cr.execute("update res_users set auth_token = '%s' WHERE id = '%s';" % (token, user[0][0]))
                return {'code': 200, 'success': True, 'Token': token}
            else:
                return {'code': 500, 'success': False, 'Result': 'The password is incorrect'}
        else:
            return {'code': 500, 'success': False, 'Result': 'The username is incorrect'}
