# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for picking in self:
            # Нэхэмжлэх үүсгэх
            if picking.picking_type_id.code == 'incoming' and picking.purchase_id and picking.partner_id.purchase_receive_invoice and picking.partner_id.purchase_method:
                invoice = picking.purchase_id.create_auto_invoice(picking.partner_id.purchase_method, picking=picking)
                if invoice:
                    invoice.action_post()
        return res
