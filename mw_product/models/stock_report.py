# -*- coding: utf-8 -*-
from odoo import api, models, fields

class StockQuantReport(models.Model):
    _inherit = "stock.quant.report"
    
    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    product_code = fields.Char(string='Код' ,readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч', readonly=True)

    def _select(self):
        select_str = super(StockQuantReport, self)._select()
        select_str += """
            ,pt.production_partner_id
            ,pt.product_code
            ,pt.supplier_partner_id
        """
        return select_str
