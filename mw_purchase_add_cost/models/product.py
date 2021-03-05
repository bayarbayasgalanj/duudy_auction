# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _expense_count(self):
        for template in self:
            template.expense_count = sum([p.expense_count for p in template.product_variant_ids])
        return True

    expense_count = fields.Integer(compute='_expense_count', string='# Expenses')

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    expense_line_ids = fields.One2many('purchase.order.expenses', 'product_id', 'Expense')

    def _expense_count(self):
        for product in self:
            product.expense_count = len(product.sudo().expense_line_ids.mapped('order_id'))

    expense_count = fields.Integer(compute='_expense_count', string='# Expenses')
