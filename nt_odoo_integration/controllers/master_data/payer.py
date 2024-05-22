# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request


class Payer(http.Controller):

    @staticmethod
    def get_payer(payer, center=False, doctor=False):
        if not payer:
            return False
        center_id = False
        doctor_id = False
        if center:
            if center.get('code', False) and center.get('name', False):
                name = center.get('name')
                code = center.get('code')

                request.env.cr.execute("""
                SELECT id, name , separated_invoices
                FROM res_partner 
                WHERE name = '%s' 
                AND center_code = '%s' 
                OR ref = '%s' ;""" % (name, code, code))
                center_id = request.env.cr.fetchall()
                if center_id:
                    center_id = {'id': center_id[0][0], 'name': center_id[0][1],
                                  'separated_invoices': center_id[0][2]}
                else:
                    center_id = {
                        'name': name,
                        'display_name': name,
                        'ref': code,
                        'contact_type': 'customer',
                        'center': True,
                        'lab2lab': True,
                        'active': True,
                        'type': 'contact',
                        'center_code': code
                    }
                    request.env.cr.execute("""INSERT INTO res_partner%s VALUES %s RETURNING id, name, separated_invoices;""" % (
                    str(tuple(center_id.keys())).replace("'", ""), tuple(center_id.values())))
                    center_id = request.env.cr.fetchall()
                    center_id = {'id': center_id[0][0], 'name': center_id[0][1], 'separated_invoices': center_id[0][2]}

        if doctor:
            if doctor.get('code', False) and doctor.get('name', False):
                name = doctor.get('name')
                code = doctor.get('code')

                request.env.cr.execute("""
                SELECT id, name , separated_invoices
                FROM res_partner 
                WHERE name = '%s' 
                AND doctor_code = '%s' 
                OR ref = '%s' ;""" % (name, code, code))
                doctor_id = request.env.cr.fetchall()
                if doctor_id:
                    doctor_id = {'id': doctor_id[0][0], 'name': doctor_id[0][1],
                                  'separated_invoices': doctor_id[0][2]}
                else:
                    doctor_id = {
                        'name': name,
                        'display_name': name,
                        'ref': code,
                        'contact_type': 'contact',
                        'doctor': True,
                        'active': True,
                        'type': 'contact',
                        'doctor_code': code
                    }
                    request.env.cr.execute("""INSERT INTO res_partner%s VALUES %s RETURNING id, name, separated_invoices;""" % (
                    str(tuple(doctor_id.keys())).replace("'", ""), tuple(doctor_id.values())))
                    doctor_id = request.env.cr.fetchall()
                    doctor_id = {'id': doctor_id[0][0], 'name': doctor_id[0][1], 'separated_invoices': doctor_id[0][2]}

        ###########
        name = payer.get('name')
        code = payer.get('code')
        request.env.cr.execute("""
        SELECT id, name , separated_invoices
        FROM res_partner 
        WHERE name = '%s' 
        OR ref = '%s' ;""" % (name, code))
        partner_id = request.env.cr.fetchall()
        if partner_id:
            partner_id = {'id': partner_id[0][0], 'name': partner_id[0][1], 'separated_invoices': partner_id[0][2]}
        else:
            partner_id = {
                'name': name,
                'display_name': name,
                'ref': code,
                'is_company': True,
                'contact_type': 'customer',
                'active': True,
                'type': 'contact',
            }

            request.env.cr.execute("""INSERT INTO res_partner%s VALUES %s RETURNING id, name, separated_invoices;""" % (
            str(tuple(partner_id.keys())).replace("'", ""), tuple(partner_id.values())))
            partner_id = request.env.cr.fetchall()

            partner_id = {'id': partner_id[0][0], 'name': partner_id[0][1], 'separated_invoices': partner_id[0][2]}
        return {'partner_id': partner_id, 'center_id': center_id, 'doctor_id': doctor_id}
