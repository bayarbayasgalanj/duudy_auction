# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _


class Pricelist(models.Model):
    _inherit = "product.pricelist.item"

    product_barcode = fields.Char('Баркод', compute='_get_product_barcode')

    @api.depends('product_id',)
    def _get_product_barcode(self):
        for obj in self:
            barcode = ''
            if obj.applied_on == '0_product_variant' and obj.product_id:
                barcode = obj.product_id.barcode
            obj.product_barcode = barcode
