# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        res = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self.purchase_line_id:
            if self.purchase_line_id.lot_id and self.location_id.usage == 'supplier':
                res.update({'lot_id': self.purchase_line_id.lot_id.id})
        return res
