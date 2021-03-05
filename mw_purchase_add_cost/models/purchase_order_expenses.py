# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

PORTION_SELECTION = [
        ('weight', 'Weight'),
        ('volume', 'Volume'),
        ('price', 'Unit Price'),
        ('subtotal', 'SubTotal')
    ]

class PurchaseOrderExpenses(models.Model):
    _name = 'purchase.order.expenses'
    _description = 'Purchase Expenses Mapping'

    order_id = fields.Many2one('purchase.order', 'Order id', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Зардлын Бараа', domain=[('type', '=', 'service')])
    partner_id = fields.Many2one('res.partner', 'Харилцагч')
    amount = fields.Float('Зардлийн дүн', default=0.0, digits=dp.get_precision('Product Price'))
    current_amount = fields.Float('Үндсэн нийт', default=0.0, digits=dp.get_precision('Product Price'))
    currency_id = fields.Many2one('res.currency', 'Валют', default=lambda self: self.env.user.company_id.currency_id.id)
    portion_method = fields.Selection(PORTION_SELECTION, 'Хувиарлах Арга', default='subtotal')
    purchase_lines = fields.Many2many('purchase.order.line', 'po_expenses_line_rel', 'prod_id', 'line_id', 'Хувиарлагдах мөрүүд')
    taxes_id = fields.Many2many('account.tax', 'po_expenses_taxes_rel', 'prod_id', 'tax_id', 'Татвар')
    notes = fields.Text('Тэмдэглэл')
    invoice_id = fields.Many2one('account.move', 'Нэхэмжлэх')
    expense_type = fields.Selection([('transport', 'Transport'), ('customs', 'Customs'), ('other', 'Other')], 'Expense type')
    is_without_cost = fields.Boolean('Өртөгд оруулахгүй /НӨАТ../', default=False)
    in_cost = fields.Boolean('Өртөгд оруулж бодох /Гадаад Тээвэр../', default=False)
    out_cost = fields.Boolean('Өртөгд оруулсануудыг гадна гаргах /Гаалийн татвар../', default=False)

    date_cur = fields.Date('Ханш бодох огноо', default=fields.Date.context_today)
    invoice_ref = fields.Char('Нэхэмжлэхийн дугаар')

    current_cur = fields.Float('Бодогдож байгаа ханш', compute='_compute_current_cur')

    @api.depends('amount', 'current_amount')
    def _compute_current_cur(self):
        for item in self:
            if item.amount != 0:
                item.current_cur = item.current_amount / item.amount
            else:
                item.current_cur = 0

    def get_po_id(self):
        if self.order_id:
            return self.order_id
        
class account_move(models.Model):
    _inherit = 'account.move'

    purchase_order_expenses = fields.One2many('purchase.order.expenses', 'invoice_id', string='Нэмэгдэл')
    