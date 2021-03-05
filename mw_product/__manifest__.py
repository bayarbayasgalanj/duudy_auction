# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Product',
    'version': '1.0.1',
    'category': 'Product',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Product',
    'description': "",
    'depends': ['product','stock','mw_stock_product_report','mw_stock'],
    'data': [
        'security/mw_product_security.xml',
        'security/ir.model.access.csv',
        'views/product_view.xml',
        'views/pricelist_views.xml',
        'views/product_category_view.xml',
        'views/new_product_request_view.xml',
        'views/stock_report_view.xml'
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
