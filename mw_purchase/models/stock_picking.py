# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    invoice_number = fields.Char('Нийлүүлэгчийн баримтын дугаар', tracking=True)
    
    def action_done(self):
        res = super(StockPicking, self).action_done()
        for picking in self:
            # Нэхэмжлэх үүсгэх
            if picking.picking_type_id.code == 'incoming':
                if picking.purchase_id and picking.purchase_id.company_id.auto_create_vendor_bill:
                    if picking.move_lines[0].product_id.purchase_method == 'receive':
                        invoice = picking.purchase_id.create_auto_invoice('receive', picking=picking)
                        if picking.purchase_id.company_id.auto_validate_vendor_bill and invoice:
                            invoice.action_post()
        return res
    
    def create_invoice_po(self):
        for picking in self:
            # Нэхэмжлэх үүсгэх
            if picking.purchase_id:
                invoice = picking.purchase_id.create_auto_invoice(picking.move_lines[0].product_id.purchase_method, picking=picking)
                if invoice:
                    invoice.action_post()