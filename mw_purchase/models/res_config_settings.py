# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    is_change_po_uom_to_uom = fields.Boolean(related="company_id.is_change_po_uom_to_uom", string="Худалдан авалтын хэмжих нэгжийг үндсэн нэгжээр солих", readonly=False)
    auto_create_vendor_bill = fields.Boolean(related="company_id.auto_create_vendor_bill", readonly=False)
    auto_validate_vendor_bill = fields.Boolean(related="company_id.auto_validate_vendor_bill", readonly=False)
