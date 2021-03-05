# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Accounting',
    'version': '1.0.1',
    'category': 'Accounting',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'website': 'www.managewall.mn',
    'summary': 'Changed by Mongolian Accounting',
    'description': "",
    'depends': ['account'],
    'data': [
#         'security/ir.model.access.csv',
        'views/widget_path.xml',
        'views/report_view.xml',
        'wizard/account_test_report_views.xml'
    ],
    "auto_install": False,
    "installable": True,
    'qweb': ['static/src/xml/custom_templates.xml'],

}
