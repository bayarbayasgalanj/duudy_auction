# -*- coding: utf-8 -*-

from odoo import api, fields, models, fields
from datetime import date,datetime,timedelta
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    car_ids = fields.One2many('motors.car','partner_id', string='Тээврийн хэрэгслийн мэдээлэл', readonly=False)
    ro_ids = fields.One2many('car.repair.order','customer_id', string='RO ids', readonly=True)
    model_display = fields.Char(string="Тээврийн хэрэгслийн загвар", compute="_compute_model", store=True, readonly=True)
    partner_car_ids = fields.One2many('motors.car','partner_id', string='Тээврийн хэрэгслийн мэдээлэл', readonly=False)
    @api.depends('car_ids')
    def _compute_model(self):
        for item in self:
            muba = []
            try:
                for x in item.car_ids:
                    muba.append(x.model_id.display_name+' '+ x.state_number)
            except:
                pass
            item.model_display = '| '.join(muba)



