# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase request',
    'version': '1.0',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Product request to purchase order""",
    'depends': ['purchase','branch','mw_dynamic_flow','mw_purchase_comparison','mw_product'],
    'summary': '',
    'data': [
            "security/request_security.xml",
            "security/ir.model.access.csv",
            "views/purchase_order_inherit.xml",
            "views/purchase_request_view.xml",
            "views/request_stock_view.xml",
            "report/pr_report_view.xml",
            "report/po_report_view.xml",
            "report/pr_report_excel_view.xml",
            "views/menu_item.xml",
    ],
    'installable': True,
    'application': False,
    'icon': '/mw_purchase_request/static/img/icon.png',
}
