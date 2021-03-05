# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class StockQuantReport(models.Model):
    _name = "stock.quant.report"
    _description = "Stock quant report mw"
    _auto = False
    
    qaunt_id = fields.Many2one('stock.quant', 'Үлдэгдэл Баримт',readonly=True)
    product_id = fields.Many2one('product.product', 'Бараа',readonly=True)
    product_tmpl_id = fields.Many2one('product.template', string='Барааны Темплати', readonly=True)
    categ_id = fields.Many2one('product.category', 'Ангилал', readonly=True)
    product_uom_id = fields.Many2one('uom.uom', 'Бараа Хэмжих', readonly=True)
    company_id = fields.Many2one('res.company', string='Компани', readonly=True)
    location_id = fields.Many2one('stock.location', 'Байрлал', readonly=True)
    lot_id = fields.Many2one('stock.production.lot', 'Цуврал дугаар', readonly=True)
    quantity = fields.Float('Үлдэгдэл', readonly=True, digits='Product Unit of Measure')
    reserved_quantity = fields.Float('Нөөцлөгдсөн', readonly=True, digits='Product Unit of Measure')
    forecast_quantity = fields.Float('Ирээдүйн Үлдэгдэл', readonly=True, digits='Product Unit of Measure')
    tracking = fields.Char(string="Tracking", readonly=True)
    barcode = fields.Char('Баркод', readonly=True)
    default_code = fields.Char('Дотоод Код', readonly=True)
    
    def _select(self):
        return """
            SELECT
                sq.id,
                sq.id as qaunt_id,
                sq.product_id,
                pp.product_tmpl_id,
                pt.uom_id as product_uom_id,
                sq.company_id,
                sq.location_id,
                sq.lot_id,
                sq.quantity,
                sq.reserved_quantity,
                sq.quantity-sq.reserved_quantity as forecast_quantity,
                pt.tracking,
                pp.barcode,
                pp.default_code,
                pt.categ_id
        """

    def _from(self):
        return """
            FROM stock_quant AS sq
            LEFT JOIN product_product pp ON (pp.id=sq.product_id)
            LEFT JOIN product_template pt ON (pp.product_tmpl_id=pt.id)
            LEFT JOIN stock_location sl ON (sl.id=sq.location_id)
        """

    def _group_by(self):
        return """
            
        """

    def _having(self):
        return """
           
        """

    def _where(self):
        return """"""

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where(), self._group_by(),self._having())
        )
