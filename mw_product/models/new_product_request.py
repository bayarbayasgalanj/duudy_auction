# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime

class NewProductRequest(models.Model):
	_name = 'new.product.request'
	_description = 'new.product.request'
	
	_order = 'date_sent, date_done'
	_inherit = ['mail.thread']

	
	def _get_user(self):
		return self.env.user.id
	
	name = fields.Char(u'Нэр', readonly=True, )
	description = fields.Text(u'Дэлгэрэнгүй тайлбар', required=True,
		states={'sent': [('readonly', True)],'created': [('readonly', True)],
				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	date = fields.Datetime(u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
	date_sent = fields.Datetime(u'Илгээсэн огноо', readonly=True)
	date_done = fields.Datetime(u'Бараа бүртгэсэн огноо', readonly=True)

	user_id = fields.Many2one('res.users', u'Хүсэлт гаргасан', default=_get_user, readonly=True)
	create_user_id = fields.Many2one('res.users', u'Бараа үүсгэсэн', readonly=True)
	
	new_product_id = fields.Many2one('product.product', u'Шинэ бараа', 
		states={'sent': [('readonly', True)],
				'done': [('readonly', True)],'cancelled': [('readonly', True)]})
	done_description = fields.Text(u'Гүйцэтгэсэн тайлбар', 
		states={'draft': [('readonly', True)],'done': [('readonly', True)],'cancelled': [('readonly', True)]})

	state = fields.Selection([
			('draft', u'Ноорог'), 
			('sent', u'Илгээсэн'),
			('created', u'Барааг үүсгэсэн'),
			('done', u'Дууссан'),
			('cancelled', u'Цуцлагдсан'),], 
			default='draft', string=u'Төлөв', track_visibility=True)

	
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Ноорог төлөвтэй бичлэгийг устгаж болно!'))
		return super(NewProductRequest, self).unlink()

	# ----------- CUSTOM METHODs -----------------
	
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_send(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('new.product.request')

		self.state = 'sent'
		self.date_sent = datetime.now()
		self.user_id = self.env.user.id
		# Chat илгээх
		res_model = self.env['ir.model.data'].search([
				('module','=','mw_product'),
				('name','=','group_stock_product_creating')])
		group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		for receiver in group.users:
			if receiver.partner_id:
				if self.env.user.partner_id.id != receiver.partner_id.id:
					channel_ids = self.env['mail.channel'].search([
					   ('channel_partner_ids', 'in', receiver.partner_id.id),
					   ('channel_partner_ids', 'in', self.env.user.partner_id.id),
					   ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
					if not channel_ids:
						vals = {
							'channel_type': 'chat', 
							'name': u''+receiver.partner_id.name+u', '+self.env.user.name, 
							'public': 'private', 
							'channel_partner_ids': [(4, receiver.partner_id.id), (4, self.env.user.partner_id.id)], 
							'email_send': False
						}
						new_channel = self.env['mail.channel'].create(vals)
						notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
						new_channel.message_post(body=notification, message_type="notification", subtype="mail.mt_comment")
						channel_info = new_channel.channel_info('creation')[0]
						self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info)
						channel_ids = [new_channel.id]
					# MSG илгээх
					self.env['mail.message'].create({
							   'message_type': 'comment', 
							   'subtype_id': 1,
							   'body': u"<span style='font-size:10pt; font-weight:bold; color:red;'>Шинэ барааны хүсэлт: " + self.name +u' та шалгана уу!</span>',
							   'channel_ids':  [(6, 0, channel_ids),]
							   })

	def action_to_created(self):
		self.state = 'created'
		self.date_done = datetime.now()
		self.create_user_id = self.env.user.id

	def action_to_done(self):
		self.state = 'done'
		self.date_done = datetime.now()
		self.create_user_id = self.env.user.id
		# Chat илгээх
		receiver = self.user_id
		if receiver.partner_id:
			if self.env.user.partner_id.id != receiver.partner_id.id:
				channel_ids = self.env['mail.channel'].search([
				   ('channel_partner_ids', 'in', receiver.partner_id.id),
				   ('channel_partner_ids', 'in', self.env.user.partner_id.id),
				   ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
				if not channel_ids:
					vals = {
						'channel_type': 'chat', 
						'name': u''+receiver.partner_id.name+u', '+self.env.user.name, 
						'public': 'private', 
						'channel_partner_ids': [(4, receiver.partner_id.id), (4, self.env.user.partner_id.id)], 
						'email_send': False
					}
					new_channel = self.env['mail.channel'].create(vals)
					notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
					new_channel.message_post(body=notification, message_type="notification", subtype="mail.mt_comment")
					channel_info = new_channel.channel_info('creation')[0]
					self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info)
					channel_ids = [new_channel.id]
				# MSG илгээх
				self.env['mail.message'].create({
						   'message_type': 'comment', 
						   'subtype_id': 1,
						   'body': u"<span style='font-size:10pt; font-weight:bold; color:red;'>Шинэ барааны код: " + str(self.new_product_id.name) +u' та шалгана уу!</span>',
						   'channel_ids':  [(6, 0, channel_ids),]
						   })

	def action_to_cancel(self):
		self.state = 'cancelled'
		self.date_done = datetime.now()
		self.create_user_id = self.env.user.id
