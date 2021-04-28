# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class CarDiagnosis(models.Model):
	_name = 'car.diagnosis'
	_description = 'Car diagnosis'
	_order = 'date_receive desc, date_to_hand desc'
	_inherit = 'mail.thread'

	@api.model
	def _get_user(self):
		return self.env.user.id

	branch_id = fields.Many2one('res.branch', string=u'Салбар', 
		states={'open':[('readonly',True)],'proccessing':[('readonly',True)],'done':[('readonly',True)]})

	origin = fields.Text(string=u"Эх баримт", readonly=True)
	name = fields.Char(string=u'Дугаар', readonly=True,)

	date_receive = fields.Date(string='Хүлээн авах огноо', copy=False,
		states={'proccessing': [('readonly', True)],'done': [('readonly', True)]})
	date_to_hand = fields.Datetime(string=u'Хүлээлгэн өгөх огноо', copy=False,
		states={'proccessing': [('readonly', True)],'done': [('readonly', True)]})

	user_id = fields.Many2one('res.users', string=u'Ажилтан', default=_get_user, required=True,
		states={'open': [('readonly', True)],'proccessing': [('readonly', True)],'done': [('readonly', True)]})
	customer_id = fields.Many2one('res.partner', string=u'Харилцагч', copy=False, 
		states={'open': [('readonly', True)],'proccessing': [('readonly', True)],'done': [('readonly', True)]})
	customer_phone = fields.Char(related='customer_id.phone', string="Утас", readonly=True, store=True,)
	customer_address = fields.Char(related='customer_id.street', string="Хаяг", readonly=True, store=True,)

	car_id = fields.Many2one('motors.car', string=u'Тээврийн хэрэгсэл', 
		#domain="[('partner_id','=',customer_id)]",
		states={'open': [('readonly', True)],'proccessing': [('readonly', True)],'done': [('readonly', True)]})
	car_start_date = fields.Date(related='car_id.start_date', readonly=True, store=True,)
	car_model_id = fields.Many2one(related='car_id.model_id', readonly=True, store=True,)
	car_vin_number = fields.Char(related='car_id.vin_number', readonly=True, store=True,)
	car_state_number = fields.Char(related='car_id.state_number', readonly=True, store=True,)

	odometer_value = fields.Float(string='Хүлээн авах үеийн гүйлт', digits = (16,1), required=True,
		states={'done': [('readonly', True)]})
	odometer_value_2 = fields.Float(string='Хүлээлгэн өгөх үеийн гүйлт', digits = (16,1),
		states={'done': [('readonly', True)]})

	state = fields.Selection([
			('draft', 'Ноорог'),
			('open', 'Нээлттэй'),
			('proccessing', 'Хийгдэж байгаа'),
			('done', 'Дууссан')],
			default='draft', string=u'Төлөв', track_visibility=True)
	# ===================
	receive_type = fields.Selection([
		('self', 'Үйлчлүүлэгч авч ирнэ'),
		('us', 'Очиж авна'),],
		default='self', string=u'Хүлээн авах төрөл', required=True,
		states={'done':[('readonly',True)]})
	to_hand_type = fields.Selection([
		('self', 'Үйлчлүүлэгч ирж авна'),
		('us', 'Аваачиж өгнө'),],
		default='self', string=u'Хүлээлгэн өгөх төрөл', required=True,
		states={'done':[('readonly',True)]})
	is_with_support_technic = fields.Boolean(string='Сэлгээний машин хэрэглэх?', default=False,
		states={'done':[('readonly',True)]})
	receive_partner_type = fields.Selection([
		('self', 'Эзэмшигч'),
		('family', 'Гэр бүл'),
		('other', 'Бусад'),],
		default='self', string=u'Үйлчлүүлэгчийг төлөөлж', required=True,
		states={'done':[('readonly',True)]})

	# Шинж тэмдэг илрэх үеийн нөхцөл
	description = fields.Text(string='Шинж тэмдэгүүд', 
		states={'done':[('readonly',True)]})
	from_where = fields.Selection([
		('nearly', 'Саяхан'),
		('weeks', '7 хоногийн өмнө'),
		('other', 'Бусад'),],
		string=u'Хэзээнээс', )
	frequency = fields.Selection([
		('always', 'Байнга'),
		('sometimes', 'Заримдаа'),
		('once', 'Ганц удаа'),
		('other', 'Бусад'),],
		string=u'Давтамж', 
		states={'done':[('readonly',True)]})
	road_type = fields.Selection([
		('simple_road', 'Энгийн зам'),
		('speed_road', 'Хурдны зам'),
		('slope', 'Налуу, Өгсүүр зам')],
		string=u'Зам', 
		states={'done':[('readonly',True)]})
	warning_flashing = fields.Selection([
		('turn_on', 'Ассан'),
		('twinkle', 'Анивчсан'),
		('multiple_flashing', 'Multiple flashing')],
		string=u'Анхааруулах гэрэл', 
		states={'done':[('readonly',True)]})
	# Нөхцөл байдал
	condition_type_1 = fields.Selection([
		('turn_on', 'Асахад'),
		('normalled', 'Нормалдахад'),
		('running_normal', 'Явахад/тогтмол'),
		('running_increase', 'Явахад/хурдлахад'),
		('running_decrease', 'Явахад/хурд хасахад')],
		string=u'Нөхцөл байдал 1', 
		states={'done':[('readonly',True)]})
	condition_type_2 = fields.Selection([
		('turn_off', 'Унтарсан үед'),
		('engine_cold', 'Мотор хүйтэн'),
		('engine_warm', 'Мотор дулаан'),
		('gear_position', 'Арааны байршил')],
		string=u'Нөхцөл байдал 2', 
		states={'done':[('readonly',True)]})
	condition_speed = fields.Integer(string=u'Хурд km/h', )
	condition_rpm = fields.Integer(string=u'Моторын эргэлт rpm', )
	condition_type_3 = fields.Selection([
		('forward', 'Урагшлахад'),
		('gear_change', 'Араа солиход'),
		('backward', 'Ухрахад'),
		('braking', 'Тормаслахад')],
		string=u'Нөхцөл байдал 2', 
		states={'done':[('readonly',True)]})
	condition_passanger_count = fields.Integer(string=u'Зорчигчдын тоо', 
		states={'done':[('readonly',True)]})
	condition_cargo_weight = fields.Integer(string=u'Ачааны жин/kg', 
		states={'done':[('readonly',True)]})
	condition_caravan_weight = fields.Integer(string=u'Чирчбуй жин, чиргүүлийн жин', 
		states={'done':[('readonly',True)]})

	road_type_2 = fields.Selection([
		('flat_road', 'Энгийн зам'),
		('not_normal_road', 'Овгор товгор'),
		('rocky_road', 'Бартаат'),
		('other_road', 'Бусад')],
		string=u'Замын нөхцөл', 
		states={'done':[('readonly',True)]})

	condition_weather = fields.Selection([
		('normal', 'Ердийн'),
		('cloudy', 'Үүлэрхэг'),
		('rainy', 'Бороотой'),
		('snowy', 'Цастай')],
		string=u'Цаг агаар', 
		states={'done':[('readonly',True)]})
	outside_temprature = fields.Integer(string=u'Гаднах темп', 
		states={'done':[('readonly',True)]})
	ac_temprature = fields.Integer(string=u'Темпратур', 
		states={'done':[('readonly',True)]})
	ac_fan_speed = fields.Integer(string=u'Сэнсний хурд', 
		states={'done':[('readonly',True)]})
	air_blast_setting = fields.Char(string=u'Салхивчны тохиргоо', 
		states={'done':[('readonly',True)]})
	air_blast_setting_2 = fields.Integer(string=u'Агаарын урсгалын тохиргоо', 
		states={'done':[('readonly',True)]})
	# 
	performance_description = fields.Text(string='Оношилгооны дэлгэрэнгүй/Үр дүн', 
		states={'done':[('readonly',True)]})
	main_damaged_reason = fields.Text(string='Үндсэн шалтгаан', 
		states={'done':[('readonly',True)]})
	maintenance_guidance = fields.Text(string='Засварын зааварчилгаа', 
		states={'done':[('readonly',True)]})
	is_warranty = fields.Boolean(string='Баталгаат', 
		states={'done':[('readonly',True)]})

	date_start = fields.Datetime(string='Эхэлсэн цаг', 
		states={'done':[('readonly',True)]})
	date_end = fields.Datetime(string='Эхэлсэн цаг', 
		states={'done':[('readonly',True)]})

	dtr = fields.Selection([
		('need', 'Хэрэгтэй'),
		('dont_need', 'Хэрэггүй')],
		string=u'DTR', 
		states={'done':[('readonly',True)]})
	# Машины байдал
	is_re_again = fields.Boolean(string='Дахин давтагдах', 
		states={'done':[('readonly',True)]})
	is_not_found_reason = fields.Boolean(string='Үндсэн шалтгааныг олохгүй', 
		states={'done':[('readonly',True)]})
	is_cant_repair = fields.Boolean(string='Засварлаж чадахгүй', 
		states={'done':[('readonly',True)]})
	# Хүсэлт
	is_diagnose = fields.Boolean(string='Машиныг үзүүлэх', 
		states={'done':[('readonly',True)]})
	is_maintenance_info = fields.Boolean(string='Засварын мэдээлэл', 
		states={'done':[('readonly',True)]})
	is_maintenance_help = fields.Boolean(string='Засварын тусламж', 
		states={'done':[('readonly',True)]})
	other = fields.Char(string='Бусад', 
		states={'done':[('readonly',True)]})

	# Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноорог бичлэг устгах боломжтой!'))
		return super(CarDiagnosis, self).unlink()

	# ====== CUSTOM METHODs ===================
	@api.onchange('car_id')
	def onchange_car_id(self):
		if self.car_id:
			self.odometer_value = self.car_id.total_odometer

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_cancel(self):
		self.state = 'cancelled'

	def action_to_open(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('car.diagnosis')
		self.state = 'open'

	def action_to_done(self):
		self.state = 'done'
		self.user_id = self.env.user.id
