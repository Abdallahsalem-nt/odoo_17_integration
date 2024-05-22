# -*- coding: utf-8 -*-
from odoo import http, models, _, api
from odoo.http import request


class Branch(http.Controller):

    @staticmethod
    def get_branch(branch_id, journal_id=False):
        """
            this method used to return journal (account.journal) object
        """
        name = branch_id.get('name')
        code = branch_id.get('code')
        short_code = name
        if len(name) > 5:
            short_code = name[:4] + name[-1]

        if not journal_id:
            request.env.cr.execute("""
            SELECT id 
            FROM account_journal 
            WHERE type = 'sale' 
            AND code = '%s';""" % short_code.upper())
            journal_id = request.env.cr.fetchall()
            journal_id = journal_id[0][0] if journal_id else False

        request.env.cr.execute("""
        SELECT id 
        FROM account_analytic_account 
        WHERE code = '%s';""" % str(code))
        analytic_id = request.env.cr.fetchall()
        analytic_id = analytic_id[0][0] if analytic_id else False

        if not journal_id:
            request.env.cr.execute("""
             SELECT aa.id  FROM account_account aa join account_account_type aat on aa.user_type_id = aat.id
               where aat.name='Income' LIMIT 1;""")
            account_id = request.env.cr.fetchall()[0][0]
            jl = {
                'name': name,
                'type': 'sale',
                'code': short_code.upper(),
                # 'ref': code,
                'invoice_reference_type': 'invoice',
                'invoice_reference_model': 'odoo',
                'default_account_id': account_id,
                'company_id': request.env.company.id,
                'active': True,
            }

            request.env.cr.execute("""INSERT INTO account_journal%s VALUES %s RETURNING id;""" % (
                str(tuple(jl.keys())).replace("'", ""), tuple(jl.values())))
            journal_id = request.env.cr.fetchall()
            journal_id = journal_id[0][0] if journal_id else False

        if not analytic_id:
            account_analytic_id = {
                'name': name,
                'active': True,
                'code': code
            }

            request.env.cr.execute("""INSERT INTO account_analytic_account%s VALUES %s RETURNING id;""" % (
            str(tuple(account_analytic_id.keys())).replace("'", ""), tuple(account_analytic_id.values())))

            analytic_id = request.env.cr.fetchall()
            analytic_id = analytic_id[0][0] if analytic_id else False

        branch = {'journal': journal_id, 'analytic': analytic_id}

        return branch
