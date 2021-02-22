# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class StockReportDetail(models.Model):
    _name = "stock.report.detail"
    _description = "Stock Report Detailt"
    _auto = False
    _order = 'product_id'

    picking_id = fields.Many2one('stock.picking', u'Баримт', readonly=True)
    stock_move_id = fields.Many2one('stock.move', u'Хөдөлгөөн', readonly=True)
    partner_id = fields.Many2one('res.partner', u'Харилцагч', readonly=True)
    location_id = fields.Many2one('stock.location', u'Байрлал', readonly=True)
    location_dest_id = fields.Many2one('stock.location', u'Хүрэх Байрлал', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', readonly=True)
    date_expected = fields.Date(u'Огноо', readonly=True)
    date_balance = fields.Date(u'Үлдэгдлийн Огноо', readonly=True)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/Template', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж',readonly=True)
    default_code = fields.Char(string=u'Дотоод Код',readonly=True)
    barcode = fields.Char(string=u'Баркод',readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string=u'Цуврал',readonly=True)
    description = fields.Char(u'Тайлбар', readonly=True)
    qty_first = fields.Float(u'Эхний Үлдэгдэл', readonly=True)
    price_unit_first = fields.Float(u'Нэгж Өртөг Эхний', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    total_price_first = fields.Float(u'Өртөг Эхний Үлдэгдэл ', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_last = fields.Float(u'Эцсийн Үлдэгдэл', readonly=True)
    total_price_last = fields.Float(u'Өртөг Эцсийн Үлдэгдэл ', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_income = fields.Float(u'Орлого', readonly=True)
    price_unit_income = fields.Float(u'Нэгж Өртөг Орлого', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    total_price_income = fields.Float(u'Өртөг Орлого', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_expense = fields.Float(u'Зарлага', readonly=True)
    price_unit_expense = fields.Float(u'Нэгж Өртөг Зарлага', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    price_unit = fields.Float(u'Нэгж Өртөг', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    total_price_expense = fields.Float(u'Өртөг Зарлага', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    state = fields.Selection([
            ('draft', u'Бүгд'),
            ('confirmed', u'Бэлэн болохыг хүлээж байгаа'), 
            ('assigned', u'Бэлэн'),
            ('done', u'Дууссан'),
        ], default='done', string=u'Төлөв', required=True,)
    transfer_type = fields.Selection([
            ('incoming', 'Орлого'), 
            ('outgoing', u'Зарлага'),
            ('internal', u'Дотоод Хөдөлгөөн'), 
            ], readonly=True, string=u'Шилжүүлгийн Төрөл')
    def _select(self):
        return """
            SELECT 
                    sml.id as id,
                    sp.partner_id as partner_id,
                    sl.id as location_id,
                    sl2.id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    0 as qty_first,
                    0 as price_unit_first,
                    0 as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_expense,
                    sm.price_unit as price_unit_expense,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_expense,
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    sl.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _select2(self):
        return """
            SELECT 
                    sml.id as id,
                    sp.partner_id as partner_id,
                    sl2.id as location_id,
                    sl.id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    0 as qty_first,
                    0 as price_unit_first,
                    0 as total_price_first,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_income,
                    sm.price_unit as price_unit_income,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    sl2.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    
    def _select3(self):
        return """
            SELECT 
                    sml.id*-1 as id,
                    sp.partner_id as partner_id,
                    sml.location_dest_id as location_id, 
                    sml.location_id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_first,
                    sm.price_unit as price_unit_first,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    null::date as date_expected,
                    (sml.date + interval '8 hour')::date as date_balance,
                    sl.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    
    def _select4(self):
        return """
            SELECT 
                    sml.id*-33 as id,
                    sp.partner_id as partner_id,
                    sml.location_id as location_id, 
                    sml.location_dest_id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end)) as qty_first,
                    sm.price_unit as price_unit_first,
                    -((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_first,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    null::date as date_expected,
                    (sml.date + interval '8 hour')::date as date_balance,
                    sl.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _select_main(self):
        return """
            SELECT 
                    id,
                    partner_id,
                    location_id, 
                    location_dest_id,
                    description,
                    state,
                    picking_id,
                    stock_move_id,
                    categ_id,
                    uom_id,
                    lot_id,
                    barcode,
                    default_code,
                    product_id,
                    product_tmpl_id,
                    price_unit,
                    qty_first,
                    price_unit_first,
                    total_price_first,
                    qty_income,
                    price_unit_income,
                    total_price_income,
                    qty_expense,
                    price_unit_expense,
                    total_price_expense,
                    (qty_first+qty_income-qty_expense) as qty_last,
                    (total_price_first+total_price_income-total_price_expense) as total_price_last,
                    date_expected,
                    date_balance,
                    warehouse_id,
                    transfer_type
        """
    def _from(self):
        return """
            FROM stock_move_line as sml
        """
    def _from2(self):
        return """
            FROM stock_move_line as sml
        """
    def _from3(self):
        return """
            FROM stock_move_line as sml
        """
    def _from4(self):
        return """
            FROM stock_move_line as sml
        """
    def _join(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join2(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join3(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join4(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    

    def _where(self):
        return """"""
    def _where2(self):
        return """"""
    def _where3(self):
        return """  """
    def _where4(self):
        return """  """
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                FROM (
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                ) as temp_bayasaa
            )
        """ % (self._table,self._select_main(), self._select(), self._from(), self._join(), self._where(),
        self._select2(), self._from2(), self._join2(), self._where2(),
        self._select3(), self._from3(), self._join3(), self._where3(),
        self._select4(), self._from4(), self._join4(), self._where4())
        )

class ProductBothIncomeExpenseReport(models.Model):
    _name = "product.both.income.expense.report"
    _description = "Product both income expense report"
    _auto = False
    _order = 'product_id'

    picking_id = fields.Many2one('stock.picking', u'Баримт', readonly=True)
    stock_move_id = fields.Many2one('stock.move', u'Хөдөлгөөн', readonly=True)
    partner_id = fields.Many2one('res.partner', u'Харилцагч', readonly=True)
    location_id = fields.Many2one('stock.location', u'Гарах байрлал', readonly=True)
    location_dest_id = fields.Many2one('stock.location', u'Хүрэх байрлал', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', u'Гарах агуулах', readonly=True)
    warehouse_dest_id = fields.Many2one('stock.warehouse', u'Хүрэх агуулах', readonly=True)
    date_expected = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/Template', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж',readonly=True)
    lot_id = fields.Many2one('stock.production.lot', string=u'Цуврал',readonly=True)
    default_code = fields.Char(string=u'Дотоод Код',readonly=True)
    barcode = fields.Char(string=u'Баркод',readonly=True)
    description = fields.Char(u'Тайлбар', readonly=True)
    qty_income = fields.Float(u'Орлого', readonly=True)
    total_price_income = fields.Float(u'Өртөг Орлого', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    price_unit_income = fields.Float(u'Нэгж Өртөг Орлого', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    qty_expense = fields.Float(u'Зарлага', readonly=True)
    total_price_expense = fields.Float(u'Өртөг Зарлага', readonly=True, groups="mw_stock_product_report.group_stock_see_price_unit")
    price_unit_income = fields.Float(u'Нэгж Өртөг Зарлага', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    price_unit = fields.Float(u'Нэгж Өртөг', readonly=True, group_operator='avg',
        groups="mw_stock_product_report.group_stock_see_price_unit")
    state = fields.Selection([
            ('draft', u'Бүгд'),
            ('confirmed', u'Бэлэн болохыг хүлээж байгаа'), 
            ('assigned', u'Бэлэн'),
            ('done', u'Дууссан'),
        ], default='done', string=u'Төлөв', required=True,)
    transfer_type = fields.Selection([
            ('incoming', 'Орлого'), 
            ('outgoing', u'Зарлага'),
            ('internal', u'Дотоод Хөдөлгөөн'), 
            ], readonly=True, string=u'Шилжүүлгийн Төрөл')
    def _select(self):
        return """
            SELECT 
                    sml.id as id,
                    sp.partner_id as partner_id,
                    sl.id as location_id,
                    sl2.id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    0 as qty_income,
                    0 as price_unit_income,
                    0 as total_price_income,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_expense,
                    sm.price_unit as price_unit_expense,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_expense,
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    sl.set_warehouse_id as warehouse_dest_id,
                    sl2.set_warehouse_id as warehouse_id,
                    case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage!='internal' 
                    and sl2.usage='internal' then 'incoming' else 'outgoing' end as transfer_type
        """
    def _select2(self):
        return """
            SELECT 
                    sml.id*-1 as id,
                    sp.partner_id as partner_id,
                    sl.id as location_id,
                    sl2.id as location_dest_id,
                    sm.name as description,
                    sml.state as state,
                    sml.picking_id as picking_id,
                    sml.move_id as stock_move_id,
                    pt.categ_id as categ_id,
                    pt.uom_id,
                    sml.lot_id,
                    pp.barcode,
                    pp.default_code,
                    sml.product_id as product_id,
                    pt.id as product_tmpl_id,
                    sm.price_unit,
                    (case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) as qty_income,
                    sm.price_unit as price_unit_income,
                    ((case when main_uuu.uom_type!='reference' and main_uuu.id=sml.product_uom_id  then sml.qty_done else sml.qty_done/uu.factor end) * ABS(sm.price_unit)) as total_price_income,
                    0 as qty_expense,
                    0 as price_unit_expense,
                    0 as total_price_expense,
                    (sml.date + interval '8 hour')::date as date_expected,
                    null::date as date_balance,
                    sl2.set_warehouse_id as warehouse_dest_id,
                    sl.set_warehouse_id as warehouse_id,
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
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    def _join2(self):
        return """
            LEFT JOIN stock_move as sm on (sm.id = sml.move_id)
            LEFT JOIN stock_picking as sp on (sp.id = sml.picking_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
            LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
            LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
            LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
            LEFT JOIN uom_uom as main_uuu on (pt.uom_id = main_uuu.id)
        """
    
    def _where(self):
        return """
            
        """
    def _where2(self):
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
                UNION ALL
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where(),
        self._select2(), self._from2(), self._join2(), self._where2()
        ))