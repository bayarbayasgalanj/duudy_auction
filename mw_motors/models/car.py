# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import collections
from odoo.osv import expression

class MotorsCar(models.Model):
	_name = 'motors.car'
	_description = 'Motors Car'
	_inherit = 'mail.thread'
	_order = 'report_order, name'

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('trim', operator, name),('name', operator, name)]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&'] + domain
		cars = self.search(domain + args, limit=limit)
		return cars.name_get()

	# Ерөнхий мэдээлэл
	car_setting_id = fields.Many2one('motors.car.setting', string=u'Тээврийн хэрэгслийн тохиргоо', )
	model_id = fields.Many2one(related='car_setting_id.model_id', string='Загвар', readonly=True, store=True)
	brand_id = fields.Many2one(related='model_id.brand_id', string='Үйлдвэрлэгч', readonly=True, store=True)
	# image = fields.Binary(string='Зураг', )
	trim = fields.Char(string='TRIM',)
	car_type = fields.Selection(related='car_setting_id.car_type', string='Тээврийн хэрэгслийн төрөл',
		readonly=True, store=True)
	report_order = fields.Char(related='car_setting_id.report_order', string='Тайлангийн эрэмбэ',
		readonly=True, store=True)
	rubber_tired = fields.Boolean(related='car_setting_id.rubber_tired', store=True, readonly=True, )
	odometer_unit = fields.Selection(related='car_setting_id.odometer_unit', string='Гүйлтийн нэгж',
		readonly=True, store=True)
	total_odometer = fields.Float(string='Нийт гүйлт', digits = (16,1), default=1, required=True)
	odometer_history_line = fields.One2many('motors.car.odometer.history.line', 'car_id', string='Гүйлтийн түүх', readonly=True, )

	work_time_per_month = fields.Float(string=u'Сарын дундаж гүйлт', default=0,
		help=u"Тээврийн хэрэгслийн сард гүйх гүйлт")

	position_format = fields.Char(related='car_setting_id.position_format', readonly=True)
	seats = fields.Integer(string='Суудлын тоо',)
	color = fields.Char(string='Өнгө', )
	fuel_type = fields.Selection([
		('gasoline', 'LPG'),
		('diesel', 'Diesel'),
		('electric', 'Electric'),
		('petrol', 'Petrol'),
		('hybrid', 'Hybrid')],
		string='Шатахууны төрөл',)

	# Тээврийн хэрэгслийн хувийн мэдээлэл
	name = fields.Char(string=u'Тээврийн хэрэгслийн нэр')
	vin_number = fields.Char(string='VIN дугаар', required=True)
	frame_number = fields.Char(string='Frame / Арлын дугаар')

	manufactured_date = fields.Date(string=u'Үйлдвэрлэсэн огноо', )
	start_date = fields.Date(string=u'Ашиглаж эхэлсэн', required=True, )
	
	state_number = fields.Char(string='Улсын дугаар', required=True,)
	document_number = fields.Char(string='Гэрчилгээний дугаар',)

	engine_serial = fields.Char(string='Хөдөлгүүрийн сериал',)
	engine_capacity = fields.Float(string='Хөдөлгүүрийн багтаамж',)
	transmission_serial = fields.Char(string='Хурдны хайрцагны сериал', )

	# Эзэмшигчийн мэдээлэл
	@api.model
	def _default_partner(self):
		return self.env.context.get('partner_id', False)

	partner_id = fields.Many2one('res.partner', string=u'Эзэмшигч харилцагч', default=_default_partner)
	partner_phone = fields.Char(related='partner_id.phone', store=True, readonly=True, )
	partner_vat = fields.Char(related='partner_id.vat', store=True, readonly=True, )
	partner_type = fields.Selection(related='partner_id.company_type', store=True, readonly=True, string="Харилцагчийн төрөл")
	
	# PM засварын мэдээлэл
	last_pm_id = fields.Many2one('motors.maintenance.type', string=u'Сүүлд хийгдсэн PM',)
	last_pm_odometer = fields.Float(string=u'Сүүлд хийгдсэн PM гүйлт', digits = (16,1),)
	last_pm_priority = fields.Integer(string=u'PM дугаар', default=0,)
	last_pm_date = fields.Date(string=u'Сүүлд хийгдсэн PM огноо', default=0,)

	state = fields.Selection([
		('draft','Draft'),
		('stopped','Stopped'),
		('working','Working'),
		('parking','Parking'),
		('repairing','Repairing'),
		('inactive',u'Актласан')],
		string='Төлөв', default='draft', track_visibility=True)
	status_note = fields.Text(string='Статус тайлбар', readonly=True, )

	# Даатгалын мэдээлэл
	with_insurance = fields.Boolean(string='Даатгалтай эсэх?', default=False,)
	insurance_payment_amount = fields.Float(string=u'Даатгалын төлбөр', )
	insurance_contract_number = fields.Char(string=u'Даатгал гэрээний дугаар', )
	insurance_type = fields.Char(string=u'Даатгал төрөл', )
	insurance_date_end = fields.Date(string=u'Даатгал дуусах', )
	# Татвар үзлэг хийх өдөр
	state_inspection_date_end = fields.Date(string=u'Улсын үзлэг дуусах огноо', )
	state_tax_date_end = fields.Date(string=u'Татвар төлөх огноо', )

	# Баталгаат хугацаа, гүйлт
	with_warrenty = fields.Boolean(string=u'Баталгаат эсэх?', default=False)
	warranty_period = fields.Integer(related='car_setting_id.warranty_period', string=u'Баталгаат хугацаа',
		help=u'Баталгаат хугацааг сараар тооцно', store=True, readonly=True, )
	warranty_odometer = fields.Integer(related='car_setting_id.warranty_odometer', string=u'Баталгаат гүйлт',
		help=u'Баталгаа өгсөн гүйлт', store=True, readonly=True, )
	warrenty_date = fields.Date(string=u'Баталгаа эхэлсэн огноо',)
	warrenty_finish_date = fields.Date(string=u'Баталгаа дуусах огноо', readonly=True, compute="_get_warranty_info",)
	warrenty_remaining_odometer = fields.Float(string=u'Баталгаат үлдсэн гүйлт', readonly=True, compute="_get_warranty_info",)
	ro_ids = fields.One2many('car.repair.order','car_id', string='RO ids', readonly=True)
	car_brand_id = fields.Many2one('motors.car.brand', string="Үйлдвэрлэгч")
	car_model_id = fields.Many2one('motors.car.model', string="Загвар")


	@api.depends('warranty_period','warranty_odometer','warrenty_date','with_warrenty')
	def _get_warranty_info(self):
		for obj in self:
			if obj.with_warrenty:
				txt = "-"
				r_odo = 0
				f_date = False
				if obj.warrenty_date and obj.car_setting_id.warranty_period > 0:
					a = obj.warrenty_date
					b = datetime.now().date()
					delta = b - a
					days = obj.warranty_period * 30
					if days > delta.days:
						date1 = obj.warrenty_date
						date2 = date1 + timedelta(days=days)
						f_date = date2
						txt = u"<b style='color:green;'>Дуусах өдөр: %s, Үлдсэн: %d өдөр</b>" % (date2.strftime('%Y-%m-%d'), days-delta.days)
					else:
						txt = u"<b style='color:red;'>Баталгаа дууссан! Хэтэрсэн өдөр: %d</b>" % (delta.days-days)
				if obj.car_setting_id.warranty_odometer > 0:
					delta = obj.car_setting_id.warranty_odometer - obj.total_odometer
					r_odo = delta 
					if delta > 0:
						txt += u"<br/><b style='color:green;'>Үлдсэн: %d гүйлт</b>" % (delta)
					else:
						txt += u"<br/><b style='color:red;'>Баталгаа дууссан! Хэтэрсэн гүйлт: %d</b>" % (delta)
				obj.warrenty_finish_date = f_date
				obj.warrenty_remaining_odometer = r_odo
				obj.warranty_info = txt
			else:
				obj.warrenty_finish_date = False
				obj.warrenty_remaining_odometer = 0
				obj.warranty_info = '-'

	warranty_info = fields.Html(string=u'Баталгааны мэдээлэл', readonly=True, compute="_get_warranty_info",)

	_sql_constraints = [
		('car_uniq', 'unique(vin_number)', "Тээврийн хэрэгслийн арлын дугаар давхардсан байна!"),
	]

	# =================== Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноороглох ёстой!'))
		return super(MotorsCar, self).unlink()

	# =================== Custom methods ===================
	# ТТ-ийн гүйлт авах
	def _get_odometer(self):
		return self.total_odometer

	@api.onchange('car_setting_id')
	def onchange_car_setting_id(self):
		if self.car_setting_id:
			self.engine_capacity = self.car_setting_id.engine_capacity
			self.seats = self.car_setting_id.seats

	def get_odometer_datas(self, t_id, context=None):
		if t_id:
			obj = self.env['motors.car'].browse(t_id)
			return {'total_odometer': obj.total_odometer}
		else:
			return {'total_odometer': 0}

	# Холбоотой үзлэгүүдийг харах
	def see_inspections(self):
		action = self.env.ref('mw_motors.action_car_inspection').read()[0]
		action['domain'] = [('car_id','=', self.id)]
		return action
	# Холбоотой засварууд харах
	def see_workorders(self):
		action = self.env.ref('mw_motors.action_car_repair_order').read()[0]
		action['domain'] = [('car_id','=', self.id)]
		return action

	# ================= CUSTOM METHODs =============
	# Гараар нэмэгдүүлэх
	def manual_increase_odometer(self):
		context = dict(self._context)
		context.update({'car_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'motors.car.odometer.increase',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}

	def _check_past_days(self, i_date, last_odometer):
		past_date = datetime.now() + timedelta(days=-4)
		if past_date.date() > i_date:
			return True
		else:
			return False

	# Тээврийн хэрэгсэл МЦ, КМ нэмэгдүүлэх func
	def _increase_odometer(self, i_date, last_odometer, is_manual=None):
		if self._check_past_days(i_date, last_odometer):
			return
		# Шинэчлэх
		self.total_odometer = last_odometer
		# Түүх үүсгэх
		vals = {
			'date': i_date,
			'car_id': self.id,
			'car_odometer': last_odometer,
			'user_id': self.env.user.id
		}
		self.env['motors.car.odometer.history.line'].sudo().create(vals)

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_parking(self):
		self.state = 'parking'

	def action_to_working(self):
		self.state = 'working'

	# Тээврийн хэрэгслийн Баталгаат хугацаа шалгах - Крон метод - CRON
	def _get_warrenty_period(self):
		if self.with_warrenty:
			if self.start_date and self.car_setting_id.warranty_period > 0:
				a = self.start_date
				b = datetime.now().date()
				delta = b - a
				days = self.warranty_period * 30
				return days - delta.days
			else:
				return 0
		else:
			return -1
	def _get_warrenty_odometer(self):
		if self.with_warrenty:
			if self.car_setting_id.warranty_odometer > 0:
				delta = self.car_setting_id.warranty_odometer - (self.total_odometer if self.odometer_unit == 'motoh' else self.total_km)
				return delta
			else:
				return 0
		return -1

	def test_check_car_warrenty(self):
		self._check_car_warrenty()

	@api.model
	def _check_car_warrenty(self):
		cars = self.env['motors.car'].search([
				('state','!=','draft'),
				('owner_type','=','own_asset'),
				('with_warrenty','=',True)
				], order='report_order, name')
		msg = []
		for line in cars:
			txt = ""
			days = line._get_warrenty_period()
			if 0 < days and days < 6:
				txt = u"%d Өдөр дутуу байна" % days
			motoh = line._get_warrenty_odometer()
			if 0 < motoh and motoh < 100:
				txt += u"%d Гүйлт дутуу байна" % motoh

			if txt:
				msg.append(str(line.name)+': '+txt)
		if msg:
			# Get group
			res_model = self.env['ir.model.data'].search([
				('module','=','mw_car_equipment'),
				('name','in',['group_car_module_admin'])])
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
						html = u"<span style='font-size:8pt; font-weight:bold; color:blue;'>Баталгаат хугацаа дуусч байгаа:<br/>" + ','.join(msg)+'</span>'
						mail_channel = self.env['mail.channel'].browse(channel_ids[0])
						message = mail_channel.with_context(mail_create_nosubscribe=True).message_post(
												   body=html,
												   message_type='comment',
												   subtype='mail.mt_comment')

	@api.model
	def _check_car_insurance(self):
		today = datetime.now()
		date_stop = today + timedelta(days=7)
		msg = []
		# Даатгалын огноо шалгах
		cars = self.env['motors.car'].search([
				('state','!=','draft'),
				('insurance_date_end','=',date_stop.date()),
				('with_insurance','=',True)
				], order='report_order, name')
		for tt in cars:
			txt = "%s-ын даатгал(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
			msg.append(txt)
		# Татвар огноо шалгах
		cars = self.env['motors.car'].search([
				('state','!=','draft'),
				('state_tax_date_end','=',date_stop.date()),
				('with_insurance','=',True)
				], order='report_order, name')
		for tt in cars:
			txt = "%s-ын татвар(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
			msg.append(txt)
		# Үзлэг огноо шалгах
		cars = self.env['motors.car'].search([
				('state','!=','draft'),
				('state_inspection_date_end','=',date_stop.date()),
				('with_insurance','=',True)
				], order='report_order, name')
		for tt in cars:
			txt = "%s-ын үзлэг(%s)" % (tt.park_number, tt.insurance_date_end.strftime("%Y-%m-%d"))
			msg.append(txt)

		# ===========================
		if msg:
			# Get group
			res_model = self.env['ir.model.data'].search([
				('module','=','mw_car_equipment'),
				('name','in',['group_car_insurance_user'])])
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
						html = u"<span style='font-size:8pt; font-weight:bold; color:blue;'>Хугацаа дуусч байгаа:<br/>" + ','.join(msg)+'</span>'
						mail_channel = self.env['mail.channel'].browse(channel_ids[0])
						message = mail_channel.with_context(mail_create_nosubscribe=True).message_post(
												   body=html,
												   message_type='comment',
												   subtype='mail.mt_comment')

class CarOdometerLine(models.Model):
	_name = 'motors.car.odometer.history.line'
	_description = 'Car odometer history line'
	_order = 'date desc'

	date = fields.Date(string=u'Огноо', required=True)
	car_id = fields.Many2one('motors.car', string='Тээврийн хэрэгсэл', ondelete='cascade')
	car_odometer = fields.Float(string='Гүйлт',digits = (16,1))
	user_id = fields.Many2one('res.users', string='Ажилтан', )

class CarOdometerIncrease(models.TransientModel):
	_name = 'motors.car.odometer.increase'
	_description = 'car odometer increase'

	# Columns
	date = fields.Date(string='Огноо', required=True)
	last_odometer =  fields.Float('Сүүлийн гүйлт',digits = (16,1), required=True,)

	def save_and_increase(self):
		if self._context.get('car_id'):
			car = self.env['motors.car'].browse(self._context.get('car_id'))
			car._increase_odometer(self.date, self.last_odometer, True)

		return True