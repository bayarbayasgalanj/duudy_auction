
# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class transport_track(models.Model):
    _name = 'transport.track'
    _description = 'transport.track'

    name = fields.Char('Нэр', required=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', u'Тээвэрлэх машины нэр давхардаж байна!'),
    ]
    

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    transport_track_id = fields.Many2one('transport.track','Тээвэрлэх машин')

    def action_view_po_id_mw(self):
        view = self.env.ref('purchase.purchase_order_form')
        return {
            'name': 'Худалдан авалтын захиалга',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            # 'target': 'new',
            'res_id': self.purchase_id.id,
            'context': dict(
                self.env.context
            ),
        }