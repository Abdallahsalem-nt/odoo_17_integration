# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request


class Patient(http.Controller):

    @staticmethod
    def get_patient(patient):
        """
            Retrieves or creates a patient based on the provided patient.
            Args:
                patient_obj: The object of the patient.
            Returns:
                The ID of the existing or newly created patient.
            """

        country_id = False
        state_id = False
        if patient.get('country'):
            request.env.cr.execute("""
            SELECT id 
            FROM res_country 
            WHERE name = '%s' 
            OR code = '%s' ;""" % (
            patient.get('country').get('name', False), patient.get('country').get('code', False)))
            country_id = request.env.cr.fetchall()

        if patient.get('state', False):
            request.env.cr.execute("""
            SELECT id 
            FROM res_country_state 
            WHERE name = '%s' 
            OR code = '%s' ;""" % (patient.get('state').get('name', False), patient.get('country').get('code', False)))
            state_id = request.env.cr.fetchall()

        request.env.cr.execute("""
        SELECT id, name 
        FROM res_partner 
        WHERE is_public_audience = True 
        AND patient_number = '%s';""" % patient.get('patientNumber'))
        patient_id = request.env.cr.fetchall()

        if patient_id:
            patient_id = {'id': patient_id[0][0], 'name': patient_id[0][1]}
        else:
            is_company = False
            if 'type' in patient:
                if patient.get('type', False) == 'Company':
                    is_company = True
            age = ""
            if patient.get('age', False):
                age = "day: " + str(patient.get('age', False).get('day')) + " month: " + str(patient.get('age', False).get('month')) + " year: " + str(patient.get('age', False).get('year'))
            patient_data = {
                'name': patient.get('name', None),
                'display_name': patient.get('name', None),
                'gender': patient.get('gender', None),
                'card_number': patient.get('card_number', None),
                'patient_number': patient.get('patientNumber', None),
                'mobile': patient.get('phone', False),
                'patient_age': age,
                'street': patient.get('street', None),
                'city': patient.get('city', None),
                'state_id': None if not state_id else state_id[0][0],
                'country_id': None if not country_id else country_id[0][0],
                'is_public_audience': True,
                'active': True,
                'type': 'contact',
                'contact_type': 'customer',
                'is_company': is_company,
            }

            patient_data = dict((k, v) for k, v in patient_data.items() if v is not None)

            request.env.cr.execute("""INSERT INTO res_partner%s VALUES %s RETURNING id, name;""" % (
            str(tuple(patient_data.keys())).replace("'", ""), tuple(patient_data.values())))

            results = request.env.cr.fetchall()
            patient_id = {'id': results[0][0], 'name': results[0][1]}

        return patient_id
