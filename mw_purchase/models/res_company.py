# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    is_change_po_uom_to_uom = fields.Boolean("Худалдан авалтын хэмжих нэгжийг үндсэн нэгжээр солих", default=False)
    auto_create_vendor_bill = fields.Boolean("Нэхэмжлэлийг автомат үүсгэх", default=False)
    auto_validate_vendor_bill = fields.Boolean("Үүсгэсэн нэхэмжлэхийг автомат батлах", default=False)
