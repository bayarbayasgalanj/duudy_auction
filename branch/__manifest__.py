# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################


{
    'name': 'Multiple Branch(Unit) Operation Setup for All Applications Odoo/OpenERP',
    'version': '1.0',
    'category': 'Sales',
    'author': 'BrowseInfo',
    'summary': 'Multiple Branch/Unit Operation on Sales,Purchases,Accounting/Invoicing,Voucher,Paymemt,POS, Accounting Reports for single company',
    "description": """
       Multiple Unit operation management for single company, Mutiple Branch management for single company, multiple operation for single company.
    Branch for POS, Branch for Sales, Branch for Purchase, Branch for all, Branch for Accounting, Branch for invoicing, Branch for Payment order, Branch for point of sales, Branch for voucher, Branch for All Accounting reports, Branch Accounting filter.
  Unit for POS, Unit for Sales, Unit for Purchase, Unit for all, Unit for Accounting, Unit for invoicing, Unit for Payment order, Unit for point of sales, Unit for voucher, Unit for All Accounting reports, Unit Accounting filter.
  Unit Operation for POS, Unit Operation for Sales, Unit operation for Purchase, Unit operation for all, Unit operation for Accounting, Unit Operation for invoicing, Unit operation for Payment order, Unit operation for point of sales, Unit operation for voucher, Unit operation for All Accounting reports, Unit operation Accounting filter.
  Branch Operation for POS, Branch Operation for Sales, Branch operation for Purchase, Branch operation for all, Branch operation for Accounting, Branch Operation for invoicing, Branch operation for Payment order, Branch operation for point of sales, Branch operation for voucher, Branch operation for All Accounting reports, Branch operation Accounting filter.
    """,
    'website': 'http://www.browseinfo.in',
    'depends': ['base','sale','purchase','stock', 'account', 'point_of_sale','mw_base'],
    'data': ['branch_view.xml',
            'pos_view.xml',
            'wizard/account_common_report_wizard.xml',

#             'report/analysis_report.xml',
            'report/report_financial.xml',
            'report/report_trial_bal.xml',
            'security/branch_security.xml',
            'security/ir.model.access.csv',
            'views/stock_view.xml',
             ],
    'qweb': [
#         'static/src/xml/pos.xml',
    ],
    'demo': [],
    "price": 89,
    "currency": 'EUR',
    'test': [],
    'installable': True,
    'auto_install': False,
    "images":['static/description/Banner.png'],
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
