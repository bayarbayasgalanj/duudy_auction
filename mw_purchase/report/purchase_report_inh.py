# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class PurchaseReport(models.Model):
    _inherit = "purchase.report"

    untaxed_total_currency = fields.Float('Татваргүй Дүн Валют', readonly=True)
    price_total_currency = fields.Float('Нийт Дүн Валют', readonly=True)
    price_average_currency = fields.Float('Дундаж Үнэ Валют', readonly=True, group_operator="avg")
    
    def _select(self):
        res = super(PurchaseReport, self)._select()
        res+="""
        ,sum(l.price_total)::decimal(16,2) as price_total_currency,
        (sum(l.product_qty * l.price_unit)/NULLIF(sum(l.product_qty/line_uom.factor*product_uom.factor),0.0))::decimal(16,2) as price_average_currency,
        sum(l.price_subtotal)::decimal(16,2) as untaxed_total_currency
        """
        return res