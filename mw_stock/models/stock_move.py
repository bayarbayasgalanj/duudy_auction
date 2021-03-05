# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp
from datetime import datetime, timedelta

class StockMode(models.Model):
    _inherit = 'stock.move'

    view_from_loc_on_hand = fields.Boolean(related='picking_type_id.view_from_loc_on_hand', readonly=True)
    on_hand_from_loc = fields.Float('Үлдэгдэл', compute='_compute_on_hand_from_loc')
    move_product_view_on_hand = fields.Boolean(related='picking_id.move_product_view_on_hand', readonly=False)
    
    @api.depends('picking_id.location_id','location_id','product_id')
    def _compute_on_hand_from_loc(self):
        for item in self:
            location_id = item.picking_id.location_id or item.location_id
            if location_id.usage=='internal' and item.product_id.type=='product' and item.view_from_loc_on_hand and item.state not in ['done','cancel']:
                res_qty = sum(item.product_id.stock_quant_ids.filtered(lambda r: r.location_id.id==location_id.id).mapped('reserved_quantity'))
                qty = sum(item.product_id.stock_quant_ids.filtered(lambda r: r.location_id.id==location_id.id).mapped('quantity'))
                item.on_hand_from_loc = qty-res_qty
            else:
                item.on_hand_from_loc = 0
    
    
    @api.depends('product_id', 'has_tracking')
    def _compute_show_details_visible(self):
        """ According to this field, the button that calls `action_show_details` will be displayed
        to work on a move from its picking form view, or not.
        """
        has_package = self.user_has_groups('stock.group_tracking_lot')
        multi_locations_enabled = self.user_has_groups('stock.group_stock_multi_locations')
        consignment_enabled = self.user_has_groups('stock.group_tracking_owner')

        show_details_visible = has_package
        # core-iig darj turdee ingej haav
        # show_details_visible = multi_locations_enabled or has_package

        for move in self:
            if not move.product_id:
                move.show_details_visible = False
            else:
                move.show_details_visible = (((consignment_enabled and move.picking_id.picking_type_id.code != 'incoming') or
                                             show_details_visible or move.has_tracking != 'none') and
                                             (move.state != 'draft' or (move.picking_id.immediate_transfer and move.state == 'draft')) and
                                             move.picking_id.picking_type_id.show_operations is False)

class StockModeLine(models.Model):
    _inherit = 'stock.move.line'

    price_unit = fields.Float(related='move_id.price_unit')    


        
