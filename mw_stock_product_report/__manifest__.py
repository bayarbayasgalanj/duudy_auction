# -*- coding: utf-8 -*-
##############################################################################
#

{
    "name" : "Stock's detailed report module",
    "version" : "1.0",
    "author" : "Manahewall LLC by amaraa",
    "description": """
    Бараа материалын дэлгэрэнгүй бүртгэлийн товчоо (дансаар)
    Барааны эхний үлдэгдэл, орлого, зарлага, эцсийн үлдэгдлийг тоо хэмжээ, өртгийг дансаар бүлэглэж гаргана.
""",
    "website" : False,
    "category" : "Stock Report",
    "depends" : ['stock','date_range','mw_stock'],
    "init": [],
    "data" : [
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/product_income_expense_report_view.xml',
        'report/stock_report_detail_view.xml',
        'wizard/product_detailed_income_expense_wizard_view.xml',
        'views/menu_view.xml',        
    ],
    "demo_xml": [],
    "active": False,
    "installable": True,
}