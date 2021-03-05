# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    discount_percent = fields.Integer("ХА-н хөнгөлөлтийн хувь", company_dependent=True, default=0.0)
