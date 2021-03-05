# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.tools.float_utils import float_compare


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    def create_invoice_hand(self):
        res = self.create_auto_invoice(self.partner_id.purchase_method)
        if res:
            res.action_post()
        return res
class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def get_purchase_method(self, purchase_method):
        res = super(stock_picking, self).get_purchase_method(purchase_method)
        if self.partner_id.purchase_method:
            res = self.partner_id.purchase_method
        return res