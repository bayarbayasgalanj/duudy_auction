# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    purchase_method = fields.Selection([
        ('purchase', 'Захиалсан тоогоор'),
        ('receive', 'Хүлээж авсан Тоогоор'),
    ], string="Худалдан Авалтын Нэхэмжлэх Үүсгэх", default="purchase")
    purchase_receive_invoice = fields.Boolean(string="Орлого Хүлээж Авсанны Дараа Нэхэмжлэх Үүсгэх", default=False)