
# -*- coding: utf-8 -*-
from datetime import date, datetime,timedelta

import odoo
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import odoo.addons.decimal_precision as dp

class purchase_comparison(models.Model):
    _name = 'purchase.comparison'
    _description = 'Purchase comparison'
   
    @api.depends('line_ids.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
        
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed) if order.currency_id else amount_untaxed,
                'amount_tax': order.currency_id.round(amount_tax) if order.currency_id else amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })
    partner_id = fields.Many2one('res.partner', string='Харилцагч')
    purchase_order_id = fields.Many2one('purchase.order', string='Худалдан авалтын захиалга', readonly=True, ondelete='cascade')
    state = fields.Selection(related='purchase_order_id.state', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Валют',store=True, compute='_compute_curr')
    line_ids = fields.One2many('purchase.comparison.line','comparison_id','Бараа comparison line')
    desc = fields.Text('Тайлбар')
    
    amount_untaxed = fields.Monetary(string='Татваргүй дүн', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    amount_tax = fields.Monetary(string='Татвар', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Нийт', store=True, readonly=True, compute='_amount_all')
    status = fields.Selection([('not','Тодорхойгүй'), ('win','Ялсан'), ('loss','Ялагдсан')], default='not', string='Ялсан эсэх')
    select_user_id = fields.Many2one('res.users', 'Сонгосон хэрэглэгч', readonly=True)

    @api.depends('purchase_order_id')
    def _compute_curr(self):
        for item in self:
            item.currency_id = item.purchase_order_id.currency_id.id

    def action_select(self):
        self.select_user_id = self.env.user.id
        self.status = 'win'
        self.purchase_order_id.win_partner_id = self.partner_id.id
        for item in self.purchase_order_id.comparison_line:
            if item.id !=self.id:
                item.status ='loss'
        return self.purchase_order_id.onchange_is_comparison()

    def action_un_select(self):
        self.select_user_id = False
        self.purchase_order_id.win_partner_id = False
        for item in self.purchase_order_id.comparison_line:
            item.status ='not'

        return self.purchase_order_id.onchange_is_comparison()
    
    # def action_create_po_line(self):
    #     po_line_ids = self.line_ids.mapped('po_line_id')
    #     for item in po_line_ids:
    #         item.po
class purchase_comparison_line(models.Model):
    _name = 'purchase.comparison.line'
    _description = 'Purchase comparison line'
    
    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.price_unit, line.comparison_id.currency_id, line.product_qty, product=line.product_id, partner=line.comparison_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    po_line_id = fields.Many2one('purchase.order.line', 'Харгалзах ХА мөр', readonly=True)
    product_id = fields.Many2one('product.product',related='po_line_id.product_id', store=True)
    product_uom = fields.Many2one('uom.uom', related='po_line_id.product_uom', readonly=True)
    product_qty = fields.Float(related='po_line_id.product_qty', readonly=True, store=True)
    taxes_id = fields.Many2many('account.tax', related='po_line_id.taxes_id', readonly=True)
    price_unit = fields.Float('Нэгж үнэ')  
    desc = fields.Char('Тайлбар')
    comparison_id = fields.Many2one('purchase.comparison', 'Purchase comparison', ondelete='cascade')
    partner_id = fields.Many2one('res.partner',related='comparison_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='comparison_id.currency_id')
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Дэд дүн', store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Дэд дүн татвартай', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Татвар', store=True)
    
class purchase_comparison_create(models.TransientModel):
    _name='purchase.comparison.create'
    _description = 'Purchase comparison Create'

    partner_id = fields.Many2one('res.partner', string='Харилцагч', required=True)
    
    def action_done(self):
        obj = self.env['purchase.order'].browse(self._context['active_id'])
        if obj:
            comparison_obj = self.env['purchase.comparison']
            result = {
            'partner_id': self.partner_id.id,
            'purchase_order_id': obj.id,
            }
            res = []
            for item in obj.order_line:
                line_values = {
                    'po_line_id': item.id,
                    'price_unit': item.price_unit,
                    }
                res.append((0,0, line_values))
            result['line_ids'] = res
            comparison_obj.create(result)  
            # self.line_ids = input_lines
        