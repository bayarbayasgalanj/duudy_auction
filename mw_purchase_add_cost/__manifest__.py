# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Purchase Order Add Cost',
    'version': '1.0.1',
    'category': 'Purchase order',
    'sequence': 20,
    'author': 'Bayasaa Managewall LLC',
    'summary': 'Changed by Mongolian Purchase order',
    'description': "",
    'depends': [
        'mw_purchase',
    ],
    'data': [
        'security/mw_purchase_security.xml',
        'security/ir.model.access.csv',
        'views/purchase_order_view.xml',
        'views/purchase_order_expenses_views.xml',
        'views/product_views.xml',
        'views/purchase_order_line_import_view.xml',
        'report/po_expenses_report.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
