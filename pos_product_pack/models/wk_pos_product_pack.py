# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
# 
#################################################################################
from odoo import api, fields, models, _
from odoo.tools import float_is_zero

import logging
_logger = logging.getLogger(__name__)

class PosPackOrderLine(models.Model):
    _name = "pos.pack.order.line"
    _description = "pos.pack.order.line"
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product', string='Product')
    price_unit = fields.Float(string='Unit Price')
    qty = fields.Float(string='Quantity')
    wk_order_id = fields.Many2one('pos.order', string='Order Ref', ondelete='cascade')


class PosOrder(models.Model):
    _inherit = 'pos.order'

    wk_product_pack_lines = fields.One2many('pos.pack.order.line', 'wk_order_id', string='Order Lines')
    def create_picking(self):
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        # If no email is set on the user, the picking creation and validation will fail be cause of
        # the 'Unable to log message, please configure the sender's email address.' error.
        # We disable the tracking in this case.
        if not self.env.user.partner_id.email:
            Picking = Picking.with_context(tracking_disable=True)
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                if not order.lines.filtered(lambda l: l.product_id.is_pack):
                    continue
            address = order.partner_id.address_get(['delivery']) or {}
            picking_type = order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = picking_type.default_location_src_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            if picking_type:
                message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
                picking_vals = {
                    'origin': order.name,
                    'partner_id': address.get('delivery', False),
                    'user_id': False,
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                }
                pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu'] or x.product_id.is_pack])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    if self.env.user.partner_id.email:
                        order_picking.message_post(body=message)
                    else:
                        order_picking.sudo().message_post(body=message)
                neg_qty = any([x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu'] or x.product_id.is_pack])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    if self.env.user.partner_id.email:
                        return_picking.message_post(body=message)
                    else:
                        return_picking.message_post(body=message)

        # ****************** staaaart start ***********
            for line in order.lines.filtered(lambda l: (l.product_id.type in ['product', 'consu']  and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding )) or (l.product_id.is_pack and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding))):
                if line.product_id.is_pack and line.product_id.pack_stock_management != 'decrmnt_pack':
                    for wk_pack_product in line.product_id.wk_product_pack.filtered(lambda l: l.product_name.type in ['product', 'consu']):
                        pack_qty = (wk_pack_product.product_quantity) *line.qty
                        moves |= Move.create({
                            'name': wk_pack_product.product_name.name,
                            'product_uom': wk_pack_product.product_name.uom_id.id,
                            'picking_id': order_picking.id if pack_qty >= 0 else return_picking.id,
                            'picking_type_id': picking_type.id if pack_qty >= 0 else return_pick_type.id,
                            'product_id': wk_pack_product.product_name.id,
                            'product_uom_qty': abs(pack_qty),
                            'state': 'draft',
                            'location_id': location_id if pack_qty >= 0 else destination_id,
                            'location_dest_id': destination_id if pack_qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        })
                        
                if line.product_id.type != 'service':
                    if line.product_id.is_pack and line.product_id.pack_stock_management != 'decrmnt_pack' and line.product_id.id in line.product_id.wk_product_pack.product_name.ids:
                        _logger.info('nemegdeh duhluu', abs(line.qty))
                    else:
                        moves |= Move.create({
                            'name': line.name,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                            'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                            'product_id': line.product_id.id,
                            'product_uom_qty': abs(line.qty),
                            'state': 'draft',
                            'location_id': location_id if line.qty >= 0 else destination_id,
                            'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        })
    # ****************** eeeenddd packk ***********

            # for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
            #     moves |= Move.create({
            #         'name': line.name,
            #         'product_uom': line.product_id.uom_id.id,
            #         'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
            #         'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
            #         'product_id': line.product_id.id,
            #         'product_uom_qty': abs(line.qty),
            #         'state': 'draft',
            #         'location_id': location_id if line.qty >= 0 else destination_id,
            #         'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
            #     })


            # prefer associating the regular order picking, not the return
            order.write({'picking_id': order_picking.id or return_picking.id})

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                moves._action_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

        return True


    # def create_picking(self):
    #     """Create a picking for each order and validate it."""
    #     Picking = self.env['stock.picking']
    #     Move = self.env['stock.move']
    #     StockWarehouse = self.env['stock.warehouse']
    #     for order in self:
    #         address = order.partner_id.address_get(['delivery']) or {}
    #         picking_type = order.picking_type_id
    #         return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
    #         order_picking = Picking
    #         return_picking = Picking
    #         moves = Move
    #         # location_id = order.location_id.id
    #         location_id = picking_type.default_location_src_id.id
    #         if order.partner_id:
    #             destination_id = order.partner_id.property_stock_customer.id
    #         else:
    #             if (not picking_type) or (not picking_type.default_location_dest_id):
    #                 customerloc, supplierloc = StockWarehouse._get_partner_locations()
    #                 destination_id = customerloc.id
    #             else:
    #                 destination_id = picking_type.default_location_dest_id.id

    #         if picking_type:
    #             message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
    #             picking_vals = {
    #                 'origin': order.name,
    #                 'partner_id': address.get('delivery', False),
    #                 'date_done': order.date_order,
    #                 'picking_type_id': picking_type.id,
    #                 'company_id': order.company_id.id,
    #                 'move_type': 'direct',
    #                 'note': order.note or "",
    #                 'location_id': location_id,
    #                 'location_dest_id': destination_id,
    #             }
    #             pos_qty = any([x.qty >= 0 for x in order.lines])
    #             if pos_qty:
    #                 order_picking = Picking.create(picking_vals.copy())
    #                 order_picking.message_post(body=message)
    #             neg_qty = any([x.qty < 0 for x in order.lines])
    #             if neg_qty:
    #                 return_vals = picking_vals.copy()
    #                 return_vals.update({
    #                     'location_id': destination_id,
    #                     'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
    #                     'picking_type_id': return_pick_type.id
    #                 })
    #                 return_picking = Picking.create(return_vals)
    #                 return_picking.message_post(body=message)

    #         for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']  or l.product_id.is_pack):
    #             if line.product_id.is_pack and line.product_id.pack_stock_management != 'decrmnt_pack':
    #                 for wk_pack_product in line.product_id.wk_product_pack.filtered(lambda l: l.product_name.type in ['product', 'consu']):
    #                     pack_qty = (wk_pack_product.product_quantity) *line.qty
    #                     moves |= Move.create({
    #                         'name': wk_pack_product.product_name.name,
    #                         'product_uom': wk_pack_product.product_name.uom_id.id,
    #                         'picking_id': order_picking.id if pack_qty >= 0 else return_picking.id,
    #                         'picking_type_id': picking_type.id if pack_qty >= 0 else return_pick_type.id,
    #                         'product_id': wk_pack_product.product_name.id,
    #                         'product_uom_qty': abs(pack_qty),
    #                         'state': 'draft',
    #                         'location_id': location_id if pack_qty >= 0 else destination_id,
    #                         'location_dest_id': destination_id if pack_qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
    #                     })

    #             if(line.product_id.type != 'service'):
    #                 if line.product_id.is_pack and line.product_id.pack_stock_management != 'decrmnt_pack' and line.product_id.id in line.product_id.wk_product_pack.product_name.ids:
    #                     _logger.info('nemegdeh duhluu', abs(line.qty))
    #                 else:
    #                     moves |= Move.create({
    #                         'name': line.name,
    #                         'product_uom': line.product_id.uom_id.id,
    #                         'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
    #                         'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
    #                         'product_id': line.product_id.id,
    #                         'product_uom_qty': abs(line.qty),
    #                         'state': 'draft',
    #                         'location_id': location_id if line.qty >= 0 else destination_id,
    #                         'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
    #                     })

    #         # prefer associating the regular order picking, not the return
    #         order.write({'picking_id': order_picking.id or return_picking.id})

    #         if return_picking:
    #             order._force_picking_done(return_picking)
    #         if order_picking:
    #             order._force_picking_done(order_picking)

    #         # when the pos.config has no picking_type_id set only the moves will be created
    #         if moves and not return_picking and not order_picking:
    #             moves._action_assign()
    #             moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

    #     return True

    