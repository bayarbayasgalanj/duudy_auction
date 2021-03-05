# -*- coding: utf-8 -*-
from datetime import date, datetime,timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    comparison_line = fields.One2many('purchase.comparison', 'purchase_order_id', 'Харьцуулалт')
    is_comparison = fields.Boolean('ХА харьцуулалттай эсэх', default=False)
    win_partner_id = fields.Many2one('res.partner', 'Ялсан харилцагч', track_visibility='onchange', copy=False)
    default_partner_id = fields.Many2one('res.partner', 'Харьцуулалтын харилцагч')
    # visible_parter_ids = fields.Many2many('res.partner', string='Харагдах харилцагчид', compute='_compute_partner')

    # @api.depends('is_comparison','win_partner_id','partner_id','default_partner_id')
    # def _compute_partner(self):
    #     for item in self:
    #         if item.state not in ['cancel','purchase','done']:
    #             if item.is_comparison:
    #                 if item.win_partner_id:
    #                     item.visible_parter_ids = [item.win_partner_id.id]
    #                 elif item.default_partner_id:
    #                     item.visible_parter_ids = [item.default_partner_id.id]
    #                 else:
    #                     item.visible_parter_ids = self.env['res.partner'].search([])
    #             else:
    #                 item.visible_parter_ids = self.env['res.partner'].search([])
    #         else:
    #             item.visible_parter_ids = self.env['res.partner'].search([])

    @api.onchange('is_comparison', 'win_partner_id')
    def onchange_is_comparison(self):
        # domain = [('supplier', '=', True)]
        if self.is_comparison:
            IrDefault = self.env['ir.default'].sudo()
            default_com_partner_id = IrDefault.get('purchase.order', "default_partner_id", company_id=self.company_id.id or self.env.user.company_id.id)
            
            if default_com_partner_id and self.partner_id.id!=default_com_partner_id:
                self.partner_id = default_com_partner_id
            
            win_line = self.comparison_line.filtered(lambda r: r.status == 'win')
            if win_line:
                self.currency_id = win_line[0].currency_id.id
            if self.win_partner_id:
                self.partner_id = self.win_partner_id.id
                for item in self.comparison_line.filtered(lambda r: r.status == 'win').line_ids:
                    item.po_line_id.price_unit = item.price_unit
        else:
            if self.partner_id:
                self.partner_id = False
        
class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    @api.model
    def create(self, vals):
        line = super(purchase_order_line, self).create(vals)
        comp_obj_line = self.env['purchase.comparison.line']
        for item in line:
            if item.order_id.is_comparison and item.order_id.comparison_line:
                for comp_line in item.order_id.comparison_line:
                    result = {
                    'comparison_id': comp_line.id,
                    'po_line_id': item.id,
                    'price_unit': item.price_unit,
                    }
                    comp_obj_line.create(result)  
        
        return line

    def unlink(self):
        comp_obj_line = self.env['purchase.comparison.line']
        for item in self:
            if item.order_id.is_comparison and item.order_id.comparison_line:
                # comp_obj_line.search([('comparison_id','in')])
                item.order_id.comparison_line.mapped('line_ids').filtered(lambda r: r.po_line_id.id == item.id).unlink()

        return super(purchase_order_line, self).unlink()

