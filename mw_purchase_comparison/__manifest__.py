# -*- coding: utf-8 -*-

{
    'name': 'MW Purchase Comparison',
    'version': '1.0',
    'sequence': 31,
    'category': 'Purchase',
    'website': 'http://manangewall.mn',
    'author': 'Managewall LLC',
    'description': """
        Purchase comparison to purchase order""",
    'depends': ['purchase','branch','mw_dynamic_flow'],
    'summary': '',
    'data': [
            # "security/comparison_security.xml",
            "security/ir.model.access.csv",
            "views/purchase_comparison_view.xml",
            "views/purchase_order_inherit.xml",
            
    ],
    'installable': True,
    'application': False,
    # 'icon': '/mw_purchase_comparison/static/img/icon.png',
}
