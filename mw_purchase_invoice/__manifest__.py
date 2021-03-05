# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase Invoice',
    'version': '1.0',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC by Bayasaa',
    'description': """
        Main managewall purchase stock""",
    'depends': [
        'purchase_stock',
        'mw_purchase',
        'mw_purchase_request',
    ],
    'summary': '',
    'data': [
        "views/res_partner_views.xml",
    ],
    'installable': True,
    'application': False,
}
