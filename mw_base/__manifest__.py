# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Base',
    'version': '12.0.1',
    'category': 'Base',
    'sequence': 20,
    'author': 'Darmaa Managewall LLC',
    'summary': 'Changed by Mongolian Base',
    'description': "",
    'depends': ['base','stock','account','purchase','hr','mail'],
    'data': [
        'security/mw_base_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_inherit_view.xml',
        'views/res_users_view.xml',
        'views/abstract_exsel_report_view.xml',
        'views/res_company_inherit_view.xml',
    ],
    'qweb': [
        'static/src/xml/date_picker.xml',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
    # 'auto_install': False,
}
