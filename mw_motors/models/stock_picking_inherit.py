# -*- coding: utf-8 -*-

from odoo import api, models, fields

class StockPicking(models.Model):
	_inherit = 'stock.picking'
	# Columns
	car_repair_order_id = fields.Many2one('car.repair.order', string='Repair Order')
	car_id = fields.Many2one('motors.car', related="car_repair_order_id.car_id", string=u'Тээврийн хэрэгсэл', readonly=True)

	def action_done(self):
		res = super(StockPicking, self).action_done()
		for picking in self:
			# Нэхэмжлэх үүсгэх
			if picking.picking_type_id.code == 'incoming' and picking.purchase_id and picking.purchase_id.ro_ids:
				roos = picking.purchase_id.ro_ids
				ilgeeh_parts = roos.mapped('assigned_user_id')
				for item in ilgeeh_parts:
					html = '<b>'+picking.purchase_id.display_name+'</b>'+' Орлого авагдлаа '+', '.join(roos.filtered(lambda r: r.assigned_user_id ==item).mapped('display_name'))
					self.env['res.users'].send_chat(html, item.partner_id)
			elif picking.car_repair_order_id:
				html = picking.car_repair_order_id.get_ro_url(' Агуулахаас СЭЛБЭГИЙН хөдөлгөөн батлагдлагдлаа')
				partner_ids = picking.car_repair_order_id.assigned_user_id.partner_id+picking.car_repair_order_id.repairman_ids.mapped('partner_id')
				self.env['res.users'].send_chat(html, partner_ids)
		return res

class StockMove(models.Model):
	_inherit = 'stock.move'
	# Columns
	car_repair_order_part_line_id = fields.Many2one('repair.order.parts.request.line', readonly=True, string=u'RO part line')
	car_repair_order_id = fields.Many2one('car.repair.order', readonly=True, store=True,
		related="car_repair_order_part_line_id.parent_id", string=u'RO', )
	car_id = fields.Many2one('motors.car', 
		related="car_repair_order_id.car_id", string=u'ТХ', readonly=True, )