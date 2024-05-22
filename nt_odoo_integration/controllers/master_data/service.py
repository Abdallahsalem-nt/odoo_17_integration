# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request
from datetime import datetime
import json

required_data = ['default_code', 'name', 'patient_share', 'company_share']


class Service(http.Controller):

    @staticmethod
    def get_product(products, insert=False):
        request.env.cr.execute("""
                SELECT id
                FROM uom_uom
                WHERE name->>'en_US' LIKE 'Units' ;""")
        product_uom_id = request.env.cr.fetchall()

        products_list = []
        for product in products:

            dif = list(set(required_data) - set(list(product.keys())))
            if dif:
                message = "Data missing services " + str(dif).replace("'", "")
                request.cr.execute(
                    "INSERT INTO integration_log(request_date, code, body, reason, active) VALUES ('%s', '400', '%s', '%s', True);" % (
                        str(datetime.now()), str(request.jsonrequest).replace("'", ""), message))
                products_list.append({
                    'code': 400,
                    'success': False,
                    "default_code": product.get('default_code'),
                    'message': message
                })

            elif type(product['default_code']) != str or len(product['default_code']) < 1:
                message = "Data Invalid services [default_code]"
                request.cr.execute(
                    "INSERT INTO integration_log(request_date, code, body, reason, active) VALUES ('%s', '400', '%s', '%s', True);" % (
                        str(datetime.now()), str(request.jsonrequest).replace("'", ""), message))
                products_list.append({
                    'code': 400,
                    'success': False,
                    "default_code": product.get('default_code'),
                    'message': message
                })

            elif type(product['name']) != str or len(product['name']) < 1:
                message = "Data Invalid services [name]"
                request.cr.execute(
                    "INSERT INTO integration_log(request_date, code, body, reason, active) VALUES ('%s', '400', '%s', '%s', True);" % (
                        str(datetime.now()), str(request.jsonrequest).replace("'", ""), message))
                products_list.append({
                    'code': 400,
                    'success': False,
                    "default_code": product.get('default_code'),
                    'message': message
                })

            elif type(product.get('patient_share')) not in (float, int) or type(product.get('company_share')) not in (
                    float, int):
                message = "Data Invalid services patient_share or company_share"
                request.cr.execute(
                    "INSERT INTO integration_log(request_date, code, body, reason, active) VALUES ('%s', '400', '%s', '%s', True);" % (
                        str(datetime.now()), str(request.jsonrequest).replace("'", ""), message))
                products_list.append({
                    'code': 400,
                    'success': False,
                    "default_code": product.get('default_code'),
                    'message': message
                })

            else:
                code = product.get('default_code')
                name = product.get('name')
                if code and name:

                    request.env.cr.execute("""
                    SELECT id,default_code,product_tmpl_id
                    FROM product_product
                    WHERE default_code = '%s';""" % code)
                    product_product = request.env.cr.fetchall()

                    if product_product:
                        product_product = product_product[0]
                        request.env.cr.execute("""
                        SELECT name
                        FROM product_template
                        WHERE id = %s;""" % product_product[2])
                        product_temp = request.env.cr.fetchall()[0]

                        products_list.append({
                                                 "id": product_product[0],
                                                 "name": product_temp[0],
                                                 "default_code": product_product[1],
                                                 "patient_share": product.get('patient_share', 0.0),
                                                 "company_share": product.get('company_share', 0.0),
                                             } if product_product else False)

                    elif insert:
                        product_temp = {
                            'name': json.dumps({'en_US': product.get('name')}),
                            'default_code': product.get('default_code'),
                            'detailed_type': 'service',
                            'sale_line_warn': 'no-message',
                            'purchase_line_warn': 'no-message',
                            'categ_id': 1,
                            'sale_ok': True,
                            'active': True,
                            'uom_id': product_uom_id[0][0] if product_uom_id else False,
                            'uom_po_id': product_uom_id[0][0] if product_uom_id else False,
                        }

                        request.env.cr.execute("""INSERT INTO product_template%s VALUES %s RETURNING id, name;""" % (
                            str(tuple(product_temp.keys())).replace("'", ""), tuple(product_temp.values())))

                        product_temp = request.env.cr.fetchall()[0]
                        product_id = {
                            'product_tmpl_id': product_temp[0],
                            'active': True,
                            'default_code': product.get('default_code')
                        }

                        request.env.cr.execute(
                            """INSERT INTO product_product%s VALUES %s RETURNING id, default_code;""" % (
                                str(tuple(product_id.keys())).replace("'", ""), tuple(product_id.values())))
                        product_product = request.env.cr.fetchall()[0]

                        products_list.append({
                            "id": product_product[0],
                            "name": product_temp[1],
                            "default_code": product_product[1],
                            "patient_share": product.get('patient_share', 0.0),
                            "company_share": product.get('company_share', 0.0),
                        })

                    else:
                        products_list.append(
                            {"id": False, "name": product.get('name'), "default_code": product.get('default_code')})

        return products_list
