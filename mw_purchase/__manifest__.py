# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase',
    'version': '1.0',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC by Bayasaa',
    'description': """
        Main managewall purchase stock""",
    'depends': [
        'mw_base',
        'purchase_stock',
        'product_expiry'
    ],
    'summary': '',
    'data': [
        "security/security.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_views.xml",
        "views/purchase_order_inherit.xml",
    ],
    'installable': True,
    'application': False,
}
