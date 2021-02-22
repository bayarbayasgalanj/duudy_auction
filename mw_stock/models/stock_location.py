# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Location(models.Model):
    _inherit = "stock.location"

    def_warehouse_id = fields.Many2one('stock.warehouse', compute='get_compute_warehouse')
    set_warehouse_id = fields.Many2one('stock.warehouse', 'Гараар зоож өгөх Агуулах')

    
    @api.depends('location_id','complete_name')
    def get_compute_warehouse(self):
        """ Returns warehouse id of warehouse that contains location """
        for item in self:
            wh_id = self.env['stock.warehouse'].search([
                ('view_location_id.parent_left', '<=', item.parent_left),
                ('view_location_id.parent_right', '>=', item.parent_left)], limit=1)
            item.def_warehouse_id = wh_id.id

    
    def action_set_warehouse_id(self):

        for item in self.env['stock.location'].search([('set_warehouse_id','=',False)]):
            # print item.id
            for wh in self.env['stock.warehouse'].search([]):
                loc_ids = self.env['stock.location'].search([('id','child_of',wh.view_location_id.id)])
                if item.id in loc_ids.ids:
                    item.set_warehouse_id = wh.id
                    break;
