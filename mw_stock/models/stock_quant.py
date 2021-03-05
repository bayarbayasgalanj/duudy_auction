# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def update_mw_reserved_quantity(self):
        for item in self:
            sml_ids = self.env['stock.move.line'].search([
                ('product_id','=',self.product_id.id),
                ('location_id','=',self.location_id.id),
                ('lot_id','=',self.lot_id.id),
                ('state','not in',['done','cancel'])
                ])
            sml_res = sum(sml_ids.mapped('product_qty'))
            if sml_res!=item.reserved_quantity:
                item.sudo().reserved_quantity = sml_res

    def view_mw_reserved_quantity(self):
        sml_ids = self.env['stock.move.line'].search([
                ('product_id','=',self.product_id.id),
                ('location_id','=',self.location_id.id),
                ('lot_id','=',self.lot_id.id),
                ('state','not in',['done','cancel']),
                ('product_qty','>',0)
                ])
        return self.view_mw_reserved_quantity_sml(sml_ids)

    def view_mw_reserved_quantity_sml(self, sml_ids):
        context = {'create': False, 'edit': False}
        tree_view_id = self.env.ref('stock.view_move_line_tree').id
        form_view_id = self.env.ref('stock.view_move_line_form').id
        action = {
                'name': 'Нөөцлөлт',
                'view_mode': 'tree',
                'res_model': 'stock.move.line',
                'views': [(tree_view_id, 'tree')],
                'view_id': tree_view_id,
                'domain': [('id','in',sml_ids.ids)],
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current'
            }
        return action

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def update_mw_reserved_quantity_mw(self):
        for item in self.product_variant_ids:
            item.update_mw_reserved_quantity_mw()

    def view_mw_reserved_quantity_mw(self):
        sml_ids = self.env['stock.move.line'].search([
                ('product_id','in',self.product_variant_ids.ids),
                ('state','not in',['done','cancel']),
                ('product_qty','>',0)
                ])
        return self.env['stock.quant'].view_mw_reserved_quantity_sml(sml_ids)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_tuple(self, obj):
        if len(obj) > 1:
            return str(tuple(obj))
        else:
            return " ("+str(obj[0])+") "

    def update_mw_reserved_quantity_mw(self):
        for item in self.stock_quant_ids:
            item.update_mw_reserved_quantity()
        sml_ids = self.env['stock.move.line'].search([
                ('product_id','=',self.id),
                ('state','not in',['done','cancel']),
                ('location_id','not in',self.stock_quant_ids.mapped('location_id').ids),
                ('picking_id','!=',False),
                ])
        if sml_ids:
            ids = self.get_tuple(sml_ids.ids)
            query1 = """
                    DELETE from
                    stock_move_line where id in {0}
                """.format(ids)
            self.env.cr.execute(query1)
            
    def view_mw_reserved_quantity_mw(self):
        sml_ids = self.env['stock.move.line'].search([
                ('product_id','=',self.id),
                ('state','not in',['done','cancel']),
                ('product_qty','>',0)
                ])
        return self.env['stock.quant'].view_mw_reserved_quantity_sml(sml_ids)
        
            