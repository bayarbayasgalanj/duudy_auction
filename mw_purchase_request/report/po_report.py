# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class po_report_mw(models.Model):
    """ CRM Lead Analysis """

    _name = "po.report.mw"
    _auto = False
    _description = "Purchase order report mw"
    # _rec_name = 'name'

    date = fields.Date('PO Огноо', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Салбар', readonly=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', string='Төлөв', readonly=True)
    flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо', readonly=True)
    state_type = fields.Char(string='Төлөвийн төрөл', readonly=True)
    product_id = fields.Many2one('product.product', 'Бараа', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', 'Бараа Темплати', readonly=True)
    product_type = fields.Selection([('product','Хадгалах бараа'), ('consu', 'Хэрэглээний бараа'), ('service', 'Үйлчилгээ')], 'Барааны төрөл', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', readonly=True)
    default_code = fields.Char('Барааны Дотоод Код', readonly=True)
    product_code = fields.Char('Барааны Код', readonly=True)
    categ_id = fields.Many2one('product.category', 'Барааны Ангилал', readonly=True)

    po_id = fields.Many2one('purchase.order', 'PO дугаар', readonly=True)
    po_user_id = fields.Many2one('res.users', 'PO Ажилтан', readonly=True)
    po_date = fields.Datetime('PO Огноо', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Худалдаж авсан Харилцагч', readonly=True)
    qty_po = fields.Float('PO Тоо Хэмжээ', readonly=True)
    qty_received = fields.Float('Хүлээж авсан тоо', readonly=True)
    qty_invoiced = fields.Float('Нэхэмжилсэн тоо', readonly=True)
    qty_inv_rec = fields.Float('Хүлээж авсан - Нэхэмжилсэн = Зөрүү', readonly=True)
    qty_po_rec = fields.Float('PO Тоо Хэмжээ - Хүлээж авсан = Зөрүү', readonly=True)
    
    price_total = fields.Float('PO Нийт үнэ', readonly=True)
    price_average = fields.Float('Нэгж үнэ дундаж', readonly=True, group_operator="avg")

    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
            WITH currency_rate as (%s)
                SELECT 
                    pol.id,
                    po.date_order as po_date,
                    pol.product_id,
                    pp.default_code,
                    pt.type as product_type,
                    pt.product_code,
                    pp.product_tmpl_id,
                    pt.categ_id,
                    po.stage_id,
                    po.branch_id,
                    pol.product_qty/u.factor*u2.factor as qty_po,
                    pol.order_id as po_id,
                    po.user_id as po_user_id,
                    spt.warehouse_id,
                    pol.qty_invoiced/u.factor*u2.factor as qty_invoiced,
                    pol.qty_received/u.factor*u2.factor as qty_received,
                    (pol.qty_received/u.factor*u2.factor)-(pol.qty_invoiced/u.factor*u2.factor) as qty_inv_rec,
                    (pol.product_qty/u.factor*u2.factor)-(pol.qty_received/u.factor*u2.factor) as qty_po_rec,
                    ((pol.product_qty * pol.price_unit / COALESCE(cr.rate, 1.0))/NULLIF((pol.product_qty/u.factor*u2.factor),0.0))::decimal(16,2) as price_average,
                    (pol.price_unit / COALESCE(cr.rate, 1.0) * pol.product_qty)::decimal(16,2) as price_total

                FROM
                    purchase_order_line pol
                LEFT JOIN
                    purchase_order po ON (po.id=pol.order_id)
                LEFT JOIN
                    product_product pp ON (pp.id=pol.product_id)
                LEFT JOIN
                    product_template pt ON (pt.id=pp.product_tmpl_id)
                left join uom_uom u on (u.id=pol.product_uom)
                left join uom_uom u2 on (u2.id=pt.uom_id)
                left join stock_picking_type spt on (spt.id=po.picking_type_id)
                left join currency_rate cr on (cr.currency_id = po.currency_id and
                        cr.company_id = po.company_id and
                        cr.date_start <= coalesce(po.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(po.date_order, now())))
                where po.state not in ('draft','cancel')
            )
        """ % (self._table, self.env['res.currency']._select_companies_rates())
        )


# SELECT
#                 r.currency_id,
#                 COALESCE(r.company_id, c.id) as company_id,
#                 r.rate,
#                 r.name AS date_start,
#                 (SELECT name FROM res_currency_rate r2
#                  WHERE r2.name > r.name AND
#                        r2.currency_id = r.currency_id AND
#                        (r2.company_id is null or r2.company_id = c.id)
#                  ORDER BY r2.name ASC
#                  LIMIT 1) AS date_end
#             FROM res_currency_rate r
#             JOIN res_company c ON (r.company_id is null or r.company_id = c.id)
    