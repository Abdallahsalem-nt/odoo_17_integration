# -*- coding: utf-8 -*-
{
    'name': "Odoo Integration With LDM",
    'author': "National Technology",
    'website': "https://nt-me.com/",
    'category': 'Odoo LDM Financial  ',
    'version': '0.1',

    'depends': ['base', 'mail', 'account','sale'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'demo/demo.xml',
        'views/integration_log_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/ldm_contract_views.xml',
        'views/payment.xml',
        'data/account_move_crons.xml'
    ],
    'license': 'LGPL-3',
}
