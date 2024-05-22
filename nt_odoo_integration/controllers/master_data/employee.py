# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request


class Employee(http.Controller):

    @staticmethod
    def get_employee(employee):
        request.env.cr.execute("SELECT id FROM hr_employee WHERE name = '%s';" % employee)
        employee_id = request.env.cr.fetchall()
        if not employee_id:
            request.env.cr.execute(
                "INSERT INTO hr_employee(name, resource_id, company_id, employee_type, active) VALUES ('%s', 1, '%s', 'employee', True) RETURNING id;" % (employee, request.env.company.id))
            employee_id = request.env.cr.fetchall()
        return employee_id[0][0]
