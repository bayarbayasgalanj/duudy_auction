# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    doned_user_id = fields.Many2one('res.users', string='Батласан хэрэглэгч')
    assigned_user_id = fields.Many2one('res.users', string='Бэлэн болгсон хэрэглэгч')

    def action_done(self):
        res = super(StockPicking, self).action_done()
        self.write({'doned_user_id': self.env.user.id})
        for item in self:
            if not item.assigned_user_id:
                item.assigned_user_id = self.env.user.id
        return res

    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        self.write({'assigned_user_id': self.env.user.id})
        return res

class ProductIncomeExpenseReport(models.Model):
    _name = "product.income.expense.report"
    _description = "Product income expense report"
    _auto = False
    _order = 'product_id, picking_id'

    name = fields.Char(u'Тайлбар', readonly=True)
    date_expected = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
    picking_id = fields.Many2one('stock.picking', u'Баримт', readonly=True, help=u"Баримтын дугаар буюу хөдөлгөөн")
    stock_move_id = fields.Many2one('stock.move', u'Хөдөлгөөн', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    location_id = fields.Many2one('stock.location', u'Гарах байрлал', readonly=True)
    location_dest_id = fields.Many2one('stock.location', u'Хүрэх байрлал', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', u'Гарах агуулах', readonly=True)
    warehouse_dest_id = fields.Many2one('stock.warehouse', u'Хүрэх агуулах', readonly=True)
    partner_id = fields.Many2one('res.partner', u'Харилцагч', readonly=True)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж',readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string=u'Цуврал', readonly=True)
    default_code = fields.Char(string=u'Дотоод Код',readonly=True)
    barcode = fields.Char(string=u'Баркод',readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/Template', readonly=True)
    qty = fields.Float(u'Тоо хэмжээ', readonly=True)
    price_unit = fields.Float(u'Нэгж Өртөг', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    total_price = fields.Float(u'Өртөг Нийт', readonly=True,
        groups="mw_stock_product_report.group_stock_see_price_unit")
    state = fields.Selection([
            ('draft', 'Draft'), 
            ('confirmed', u'Бэлэн болохыг хүлээж буй'),
            ('assigned', u'Бэлэн'), 
            ('done', u'Дууссан')
        ], readonly=True, string=u'Төлөв')
    transfer_type = fields.Selection([
            ('incoming', 'Орлого'), 
            ('outgoing', u'Зарлага'),
            ('internal', u'Дотоод Хөдөлгөөн'), 
            ], readonly=True, string=u'Шилжүүлгийн Төрөл')
    doned_user_id = fields.Many2one('res.users', 'Батласан хэрэглэгч')
    assigned_user_id = fields.Many2one('res.users', string='Бэлэн болгсон хэрэглэгч')

    def _select(self):
        return """
            SELECT 
                    sml.id as id,
                    sml.move_id as stock_move_id,
                    sp.partner_id as partner_id,
                    pt.categ_id as categ_id,
                    sml.reference as name,
                    (sml.date + interval '8 hour')::date as date_expected,
                    sp.id as picking_id,
                    sml.location_id as location_id,
                    sml.location_dest_id as location_dest_id,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty,
                    sm.price_unit as price_unit,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * sm.price_unit as total_price,
                    sml.state,
                    sp.doned_user_id as doned_user_id,
                    sp.assigned_user_id as assigned_user_id,
                    sl.set_warehouse_id as warehouse_id,
                    sl2.set_warehouse_id as warehouse_dest_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _from(self):
        return """
            FROM stock_move_line as sml
        """
    def _join(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """

    def _where(self):
        return """
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table,self._select(), self._from(), self._join(), self._where())
        )

class ProductBalancePivotReport(models.Model):
    _name = "product.balance.pivot.report"
    _description = "Product balance pivot report"
    _auto = False
    _order = 'product_id'

    date_expected = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
    warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', readonly=True)
    picking_id = fields.Many2one('stock.picking', u'Баримт', readonly=True)
    stock_move_id = fields.Many2one('stock.move', u'Хөдөлгөөн', readonly=True)
    location_id = fields.Many2one('stock.location', u'Байрлал', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж',readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string=u'Цуврал', readonly=True)
    default_code = fields.Char(string=u'Дотоод Код',readonly=True)
    barcode = fields.Char(string=u'Баркод',readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/Template', readonly=True)
    qty = fields.Float(u'Тоо хэмжээ', readonly=True)
    standart_amount = fields.Float(u'Нийт өртөг/Одоогийн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    amount = fields.Float(u'Нийт өртөг/Тухайн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    dirty_profit = fields.Float(u'Бохир ашиг/Тухайн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    standart_dirty_profit = fields.Float(u'Бохир ашиг/Одоогийн/', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    amount_sale = fields.Float(u'Нийт зарах', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    state = fields.Char(readonly=True, string=u'Төлөв')
    transfer_type = fields.Selection([
            ('incoming', 'Орлого'), 
            ('outgoing', u'Зарлага'),
            ('internal', u'Дотоод Хөдөлгөөн'), 
            ], readonly=True, string=u'Шилжүүлгийн Төрөл')
    partner_id = fields.Many2one('res.partner', u'Харилцагч', readonly=True)

    def _select(self):
        return """
            SELECT 
                    sml.id as id,
                    sp.partner_id,
                    sml.picking_id,
                    sml.move_id as stock_move_id,
                    sl.set_warehouse_id as warehouse_id,
                    sml.location_dest_id as location_id, 
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as amount,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(ip.value_float)) as standart_amount,
                    (coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(sm.price_unit),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as dirty_profit,
                    (coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(ip.value_float),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as standart_dirty_profit,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * pt.list_price) as amount_sale,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty,
                    (sml.date + interval '8 hour')::date as date_expected,
                    sml.state,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _select2(self):
        return """
            SELECT 
                    sml.id*-1 as id,
                    sp.partner_id,
                    sml.picking_id,
                    sml.move_id as stock_move_id,
                    sl.set_warehouse_id as warehouse_id,
                    sml.location_id as location_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as amount,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(ip.value_float)) as standart_amount,
                    -(coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(sm.price_unit),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as dirty_profit,
                    -(coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)*coalesce(pt.list_price,0)-coalesce(ABS(ip.value_float),0)*coalesce((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end),0)) as standart_dirty_profit,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * pt.list_price) as amount_sale,
                    -(case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty,
                    (sml.date + interval '8 hour')::date as date_expected,
                    sml.state,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _from(self):
        return """
            FROM stock_move_line as sml
        """
    def _from2(self):
        return """
            FROM stock_move_line as sml
        """
    def _join(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sml.picking_id = sp.id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN ir_property as ip on (ip.res_id = 'product.product,'||sml.product_id and ip.name = 'standard_price')
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join2(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sml.picking_id = sp.id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN ir_property as ip on (ip.res_id = 'product.product,'||sml.product_id and ip.name = 'standard_price')
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _where(self):
        return """"""
    def _where2(self):
        return """"""
        
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
            )
        """ % (self._table,self._select(), self._from(), self._join(), self._where(),
        self._select2(), self._from2(), self._join2(), self._where2())
        )