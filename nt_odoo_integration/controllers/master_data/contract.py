# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request


class Contract(http.Controller):

    @staticmethod
    def get_contract(contract):
        code = contract.get('code')
        name = contract.get('name')
        if code and name:
            ###########
            request.env.cr.execute("""
            SELECT id 
            FROM ldm_contract 
            WHERE contract_code = '%s' 
            AND contract_name = '%s' ;""" % (code, name))
            contract_id = request.env.cr.fetchall()

            contract_id = contract_id[0][0] if contract_id else False
            if not contract_id:
                request.env.cr.execute(
                    """INSERT INTO ldm_contract(contract_code, contract_name) VALUES ('%s', '%s') RETURNING id;""" % (
                    code, name))
                contract_id = request.env.cr.fetchall()
                contract_id = contract_id[0][0] if contract_id else False

            return contract_id
        return False
