# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class PrReport(models.Model):
    _name = "pr.report"
    _auto = False
    _description = "Purchase requist report"
    
    date = fields.Date('Хүсэлтийн Огноо', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Салбар', readonly=True)
    # flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', readonly=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', string='Төлөв', readonly=True)

    state_type = fields.Char(string='Төлөвийн төрөл', readonly=True)
    product_id = fields.Many2one('product.product', 'Бараа', readonly=True)
    product_id_pr = fields.Many2one('product.product', 'Бараа PR', readonly=True)
    product_id_po = fields.Many2one('product.product', 'Бараа PO', readonly=True)
    product_id_st = fields.Many2one('product.product', 'Бараа Stock', readonly=True)
    request_id = fields.Many2one('purchase.request', 'Хүсэлтийн Дугаар', readonly=True)
    pr_line_id = fields.Many2one('purchase.request.line', 'Хүсэлтийн Мөр', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Хүсэлтийн Ажилтан', readonly=True)
    name = fields.Char('Дугаар', readonly=True)
    qty = fields.Float('Хүсэлтийн Тоо Хэмжээ', readonly=True)
    description = fields.Char('Тайлбар Зориулалт', readonly=True)
    department_id = fields.Many2one('hr.department', 'Хэлтэс', readonly=True)
    default_code = fields.Char('Барааны Дотоод Код', readonly=True)
    product_code = fields.Char('Барааны Код', readonly=True)
    categ_id = fields.Many2one('product.category', 'Барааны Ангилал', readonly=True)

    po_id = fields.Many2one('purchase.order', 'PO Захиалга', readonly=True)
    po_user_id = fields.Many2one('res.users', 'PO Ажилтан', readonly=True)
    po_date = fields.Datetime('PO Огноо', readonly=True)
    po_date_in = fields.Datetime('PO Нийлүүлэх Хугацаа', readonly=True)
    stock_date = fields.Datetime('Агуулахын Орлогодсон Огноо', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Худалдаж авсан Харилцагч', readonly=True)
    qty_po = fields.Float('PO Тоо Хэмжээ', readonly=True)
    qty_received = fields.Float('PO Хүлээж авсан тоо', readonly=True)
    qty_invoiced = fields.Float('PO Нэхэмжилсэн тоо', readonly=True)
    actual_percent = fields.Float('Хүсэлтийн биелэлтийн %', readonly=True, group_operator="avg")
    price_unit_po = fields.Float('PO Нэгж үнэ', readonly=True, group_operator="avg")
    stage_id_po = fields.Many2one('dynamic.flow.line.stage', string='PO Төлөв', readonly=True)
    state_type_po = fields.Char(string='PO Төлөвийн төрөл', readonly=True)

    price_total = fields.Float('Худалдан авалт Нийт үнэ', readonly=True)
    warehouse_id_po = fields.Many2one('stock.warehouse', 'Худалдан авалт хйисэн Агуулах', readonly=True)
    picking_id = fields.Many2one('stock.picking', 'Хүлээн авсан баримт', readonly=True)
    po_date_count = fields.Integer('PO Нийлүүлэх Хоног', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    product_id,
                    product_id_pr,
                    product_id_po,
                    product_id_st,
                    default_code,
                    product_code,
                    categ_id,
                    id,
                    pr_line_id,
                    request_id,
                    po_id,
                    
                    stage_id,
                    flow_line_id,
                    state_type,
                    stage_id_po,
                    state_type_po,
                    branch_id,
                    date,
                    warehouse_id,
                    employee_id,
                    department_id,
                    description,
                    name,
                    po_user_id,
                    po_date,
                    po_date_in,
                    stock_date,
                    partner_id,
                    picking_id,
                    warehouse_id_po,
                    po_date_count,
                    qty as qty,
                    qty_po as qty_po,
                    qty_received as qty_received,
                    qty_invoiced as qty_invoiced,
                    price_unit_po as price_unit_po,
                    price_total as price_total,
                    0 as actual_percent
                    
                FROM 
                (SELECT
                    prl.id,
                    prl.id as pr_line_id,
                    prl.product_id,
                    pp.default_code,
                    pt.product_code,
                    pt.categ_id,
                    pr.flow_line_id,
                    pr.stage_id,
                    pr.state_type,
                    pr.branch_id,
                    pr.date,
                    pr.warehouse_id,
                    pr.employee_id,
                    pr.department_id,
                    pr.desc as description,
                    pr.name,
                    pr.id as request_id,
                    po.id as po_id,
                    po.user_id as po_user_id,
                    po.date_planned as po_date,
                    po.date_planned as po_date_in,
                    po.partner_id as partner_id,
                    spt.warehouse_id as warehouse_id_po,
                    po.stage_id as stage_id_po,
                    po.state_type as state_type_po,
                    prl.product_id as product_id_pr,
                    null::int as product_id_po,
                    null::int as product_id_st,
                    max(sm.picking_id) as picking_id,
                    max(sm.date) as stock_date,
                    max(prl.qty) as qty,
                    0 as qty_received,
                    0 as qty_po,
                    0 as qty_invoiced,
                    0 as price_unit_po,
                    0 as price_total,
                    0 as po_date_count
                FROM purchase_request_line AS prl
                    LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.pr_line_id=prl.id)
                    LEFT JOIN purchase_order_line AS pol on (pol.id=po_pr_rel.po_line_id)
                    LEFT JOIN product_product pp on (pp.id=prl.product_id)
                    LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
                    LEFT JOIN purchase_order AS po on (po.id=pol.order_id)
                    LEFT JOIN stock_picking_type spt on (po.picking_type_id=spt.id)
                    LEFT JOIN purchase_request AS pr on (pr.id=prl.request_id)
                   left join stock_move as sm on (pol.id=sm.purchase_line_id)
                   
                where pr.state_type!='cancel'
                group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26
                UNION ALL
                SELECT
                    pol.id*-1 as id,
                    prl.id as pr_line_id,
                    pol.product_id,
                    pp.default_code,
                    pt.product_code,
                    pt.categ_id,
                    pr.flow_line_id,
                    pr.stage_id,
                    pr.state_type,
                    pr.branch_id,
                    pr.date,
                    
                    pr.warehouse_id,
                    pr.employee_id,
                    pr.department_id,
                    pr.desc as description,
                    pr.name,
                    prl.request_id as request_id,
                    
                    po.id as po_id,
                    po.user_id as po_user_id,
                    po.date_planned as po_date,
                    po.date_planned as po_date_in,
                    po.partner_id,
                    spt.warehouse_id as warehouse_id_po,
                    po.stage_id as stage_id_po,
                    po.state_type as state_type_po,
                    null::int as product_id_pr,
                    pol.product_id as product_id_po,
                    null::int as product_id_st,
                    0 as picking_id,
                    null::timestamp as stock_date,
                    0 as qty,
                    pol.qty_received,
                    pol.product_qty as qty_po,
                    pol.qty_invoiced,
                    pol.price_unit as price_unit_po,
                    pol.price_total as price_total,
            CASE WHEN po.date_planned is not null and pr.date  is not null and po.date_planned>pr.date THEN po.date_planned::DATE-  pr.date::DATE ELSE 0 END as po_date_count
                FROM purchase_order_line as pol
                LEFT JOIN purchase_order AS po on (po.id=pol.order_id)
                    LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.po_line_id=pol.id)
                    LEFT JOIN purchase_request_line AS prl on (prl.id=po_pr_rel.pr_line_id)
                    LEFT JOIN product_product pp on (pp.id=pol.product_id)
                    LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
                    
                    LEFT JOIN stock_picking_type spt on (po.picking_type_id=spt.id)
                    LEFT JOIN purchase_request AS pr on (pr.id=prl.request_id)
        where po.state!='cancel'
                UNION ALL
                SELECT
                    sm.id*-100 as id,
                    prl.id as pr_line_id,
                    sm.product_id,
                    
                    pp.default_code,
                    pt.product_code,
                    pt.categ_id,
                    pr.flow_line_id,
                    pr.stage_id,
                    pr.state_type,
                    pr.branch_id,
                    pr.date,
                    
                    pr.warehouse_id,
                    pr.employee_id,
                    pr.department_id,
                    pr.desc as description,
                    pr.name,
                    prl.request_id as request_id,
                    
                    po.id as po_id,
                    po.user_id as po_user_id,
                    po.date_planned as po_date,
                    po.date_planned as po_date_in,
                    po.partner_id,
                    spt.warehouse_id as warehouse_id_po,
                    po.stage_id as stage_id_po,
                    po.state_type as state_type_po,
                    null::int as product_id_pr,
                    null::int as product_id_po,
                    sm.product_id as product_id_st,
                    sm.picking_id as picking_id,
                    sm.date as stock_date,
                    0 as qty,
                    0 as qty_received,
                    0 as qty_po,
                    0 as qty_invoiced,
                    0 as price_unit_po,
                    0 as price_total,
                    0 as po_date_count
                FROM stock_move AS sm
                    LEFT JOIN purchase_order_line AS pol on (pol.id=sm.purchase_line_id)
                    LEFT JOIN purchase_order AS po on (po.id=pol.order_id)
                    LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.po_line_id=pol.id)
                    LEFT JOIN stock_picking_type spt on (po.picking_type_id=spt.id)
                    LEFT JOIN purchase_request_line AS prl on (prl.id=po_pr_rel.pr_line_id)
                    LEFT JOIN purchase_request AS pr on (pr.id=prl.request_id)
                    LEFT JOIN product_product pp on (pp.id=sm.product_id)
                    LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
                    
                where sm.state='done' and sm.purchase_line_id is not null
                
                
) as temp_pr_report 
 
            )
        """ % (self._table)
        )


    