# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	car_repair_order_id = fields.Many2one('car.repair.order', string='RO name', )
	ro_ids = fields.Many2many('car.repair.order', 'purchase_order_car_repair_order_rel', 'po_id', 'ro_id', string='ROs', compute='compute_ro')
	ro_count = fields.Integer(string='ROs count', compute='compute_ro')

	@api.depends('order_line.ro_part_line_many_ids')
	def compute_ro(self):
		for item in self:
			item.ro_ids = item.order_line.mapped('ro_part_line_many_ids.parent_id')
			item.ro_count = len(item.ro_ids)
	
	def view_ro(self):
		self.ensure_one()
		action = self.env.ref('mw_motors.action_car_repair_order').read()[0]
		action['domain'] = [('id','in',self.ro_ids.ids)]
		action['context'] = {}
		return action
	
class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	ro_part_line_many_ids = fields.Many2many('repair.order.parts.request.line', 'purchase_order_line_ro_parts_line', 'pol_id', 'parts_id', string='Order part line many', readonly=True)
	
class CarRepairOrder(models.Model):
	_name = 'car.repair.order'
	_description = 'Car Repair Order'
	_order = 'date_reception desc, date_delivery desc'
	_inherit = ['mail.thread','mail.activity.mixin']

	@api.model
	def _get_user(self):
		return self.env.user.id
	@api.model
	def _get_default_date(self):
		if 'date' in self.env.context:
			return self.env.context.get("date")
		else:
			return False
	@api.model
	def _get_default_time(self):
		if 'time' in self.env.context:
			return self.env.context.get("time")
		else:
			return 0
	@api.model
	def _get_default_stall(self):
		if 'stall_id' in self.env.context:
			return self.env.context.get("stall_id")
		else:
			return False
	@api.model
	def _get_default_branch(self):
		if self.env.user.branch_id:
			return self.env.user.branch_id.id
		else:
			return False

	branch_id = fields.Many2one('res.branch', string=u'Салбар', default=_get_default_branch,
		states={'open':[('readonly',True)],'being_serviced':[('readonly',True)],'waiting_for_delivery':[('readonly',True)]})

	origin = fields.Text(string=u"Эх баримт", readonly=True)
	name = fields.Char(string=u'Дугаар', readonly=True, copy=False)

	scheduled_date = fields.Date(string='Төлөвлөсөн өдөр', copy=False,
		default=_get_default_date,
		states={'open': [('readonly', True)],
			'waiting_for_service': [('readonly', True)],
			'being_serviced': [('readonly', True)],
			'paused': [('readonly', True)],
			'waiting_for_inspection': [('readonly', True)],
			'waiting_for_washing': [('readonly', True)],
			'waiting_for_invoicing': [('readonly', True)],
			'waiting_for_delivery': [('readonly', True)],
			'psfu': [('readonly', True)],
			'closed': [('readonly', True)]})
	scheduled_time = fields.Float(string='Төлөвлөсөн цаг', copy=False, required=True, default=_get_default_time,
		states={'open': [('readonly', True)],
			'waiting_for_service': [('readonly', True)],
			'being_serviced': [('readonly', True)],
			'paused': [('readonly', True)],
			'waiting_for_inspection': [('readonly', True)],
			'waiting_for_washing': [('readonly', True)],
			'waiting_for_invoicing': [('readonly', True)],
			'waiting_for_delivery': [('readonly', True)],
			'psfu': [('readonly', True)],
			'closed': [('readonly', True)]})
	spend_time = fields.Float(string='Зарцуулах цаг', digits=(16,2),
		states={'open': [('readonly', True)],
			'waiting_for_service': [('readonly', True)],
			'being_serviced': [('readonly', True)],
			'paused': [('readonly', True)],
			'waiting_for_inspection': [('readonly', True)],
			'waiting_for_washing': [('readonly', True)],
			'waiting_for_invoicing': [('readonly', True)],
			'waiting_for_delivery': [('readonly', True)],
			'psfu': [('readonly', True)],
			'closed': [('readonly', True)]})

	maintenance_type = fields.Selection([
			('diagnostic', 'Оношилгоо'),
			('express_maintenance', 'Express maintenance'),
			('general_repair', 'General repair'),
			('body_and_paint', 'Body & paint'),
			('tuning_and_upgrade', 'Tuning & upgrade')],
		string=u'Засварын төрөл', track_visibility=True, required=True,
		states={'open': [('readonly', True)],
			'waiting_for_service': [('readonly', True)],
			'being_serviced': [('readonly', True)],
			'paused': [('readonly', True)],
			'waiting_for_inspection': [('readonly', True)],
			'waiting_for_washing': [('readonly', True)],
			'waiting_for_invoicing': [('readonly', True)],
			'waiting_for_delivery': [('readonly', True)],
			'psfu': [('readonly', True)],
			'closed': [('readonly', True)]})
	pm_priority = fields.Integer(string=u'PM ийн дугаар', default=1,
		states={'open': [('readonly', True)],
			'waiting_for_service': [('readonly', True)],
			'being_serviced': [('readonly', True)],
			'paused': [('readonly', True)],
			'waiting_for_inspection': [('readonly', True)],
			'waiting_for_washing': [('readonly', True)],
			'waiting_for_invoicing': [('readonly', True)],
			'waiting_for_delivery': [('readonly', True)],
			'psfu': [('readonly', True)],
			'closed': [('readonly', True)]})

	total_price = fields.Float(string='Нийт үнэ', readonly=True, store=True, compute='_compute_total_price', tracking=True)
	total_price_service = fields.Float(string='Үйлчилгээний үнэ', readonly=True,store=True, compute='_compute_total_price', tracking=True)
	total_price_part = fields.Float(string='Сэлбэгийн үнэ', readonly=True, store=True,compute='_compute_total_price', tracking=True)
	@api.depends('parts_request_service_line','parts_request_line')
	def _compute_total_price(self):
		for obj in self:
			obj.total_price_service = sum(obj.parts_request_service_line.mapped('sub_total'))
			obj.total_price_part = sum(obj.parts_request_line.mapped('sub_total'))
			obj.total_price = obj.total_price_service + obj.total_price_part
	
	repairman_ids = fields.Many2many('res.users', string='Засварчин',
		domain="[('groups_id','=',group_id)]",
		states={'closed': [('readonly', True)],'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	@api.model
	def _get_default_group(self):
		group = self.env.ref('mw_motors.group_car_module_repairman')
		return group.id
	group_id = fields.Many2one('res.groups', string='Засварчин групп', default=_get_default_group)

	days_state = fields.Selection([
			('normal', 'Болоогүй'),
			('3days', '3-days before'),
			('2days', '2-days before'),
			('1days', '1-day before'),
			('start', 'Start')],
		string=u'Preparation state', default='normal', track_visibility=True, copy=False)
	date_3days = fields.Datetime(string='3-days огноо', readonly=True, )
	date_2days = fields.Datetime(string='2-days огноо', readonly=True, )
	date_1day = fields.Datetime(string='1-day огноо', readonly=True, )

	warning_messages = fields.Html(string='Warning message', compute='_compute_warning_messages', readonly=True, )
	is_warning = fields.Boolean(string='Is Warning', compute='_compute_warning_messages', readonly=True, )
	@api.depends('days_state','scheduled_date','state')
	def _compute_warning_messages(self):
		for obj in self:
			if obj.state in ['draft','open','waiting_for_service'] and obj.scheduled_date:
				today = datetime.now().date()
				days = (obj.scheduled_date-today).days
				print('====', obj.scheduled_date, today, days)
				# Эхлэхэд 3аас их хоног дутуу бол хэвийн, эхлэх болоогүй
				if days > 3:
					obj.warning_messages = False
					obj.is_warning = False
				# Эхлэхэд 3 хоног үлдсэн
				elif days == 3:
					if obj.days_state == 'normal':
						obj.warning_messages = "Хоцролтой байна. '3-days before'-н бэлтгэл ажлуудыг хийнэ үү!"
						obj.is_warning = True
					elif obj.days_state == '3days':
						obj.warning_messages = "Хэвийн. '3-days before'-н бэлтгэл ажлуудыг хийх ёстой!"
						obj.is_warning = False
					else:
						obj.warning_messages = False
						obj.is_warning = False
				# Эхлэхэд 2 хоног үлдсэн
				elif days == 2:
					if obj.days_state in ['normal','3days']:
						obj.warning_messages = "Хоцролтой байна. '2-days before'-н бэлтгэл ажлуудыг хийнэ үү!"
						obj.is_warning = True
					elif obj.days_state == '2days':
						obj.warning_messages = "Хэвийн. '2-days before'-н бэлтгэл ажлуудыг хийх ёстой!"
						obj.is_warning = False
					else:
						obj.warning_messages = False
						obj.is_warning = False
				# Эхлэхэд 1 хоног үлдсэн
				elif days == 1:
					if obj.days_state in ['normal','3days','2days']:
						obj.warning_messages = "Хоцролтой байна. '1-days before'-н бэлтгэл ажлуудыг хийнэ үү!"
						obj.is_warning = True
					elif obj.days_state == '1days':
						obj.warning_messages = "Хэвийн. '1-days before'-н бэлтгэл ажлуудыг хийх ёстой!"
						obj.is_warning = False
					else:
						obj.warning_messages = False
						obj.is_warning = False
				# Эхлэх хоног үлдээгүй
				else:
					# Эхэлсэн бол асуудалгүй
					if obj.days_state == 'start':
						obj.warning_messages = False
						obj.is_warning = False
					else:
						obj.warning_messages = "Өмнөх өдрийн бэлтгэл ажлууд хийгдээгүй байна!!!"
						obj.is_warning = True
			else:
				obj.warning_messages = False
				obj.is_warning = False

	warehouse_id = fields.Many2one('stock.warehouse', string='Агуулах', )
	dest_warehouse_id = fields.Many2one('stock.warehouse', string='Түр Агуулах', )

	ordered_po_id = fields.Many2one('purchase.order', string='Сэлбэгийн PO', readonly=True, )
	is_draft_po = fields.Boolean(string='Ноорог худалдан авалтанд нийлүүлэх', default=True, copy=False)

	state = fields.Selection([
			('draft', 'Draft'),
			('open', 'Open'),
			('waiting_for_service', 'Waiting for Service'),
			('being_serviced', 'Being Serviced'),
			('paused', 'Paused'),
			('waiting_for_inspection', 'Waiting for Inspection'),
			('waiting_for_washing', 'Waiting for Washing'),
			('waiting_for_invoicing', 'Waiting for Invoicing'),
			('waiting_for_delivery', 'Waiting for Delivery'),
			('psfu', 'PSFU'),
			('closed', 'Closed'),
			('cancelled', 'Cancelled')
			],
		default='draft', string=u'Төлөв', track_visibility=True)

	# Cancel шалтгаан
	cancel_type = fields.Selection([
			('cancelled_1', 'Шалтгаан 1'),
			('cancelled_2', 'Шалтгаан 2'),
			('cancelled_3', 'Шалтгаан 3'),
			('cancelled_4', 'Шалтгаан 4'),
			], string=u'Цуцалсан шалтгаан',
		states={'cancelled':[('readonly',True)],'closed':[('readonly',True)]})
	cancel_reason = fields.Text(string=u'Цуцалсан тайлбар',
		states={'cancelled':[('readonly',True)],'closed':[('readonly',True)]})

	date_open = fields.Datetime(string='Open date', readonly=True, )
	date_waiting_for_service = fields.Datetime(string='Waiting for Service date', readonly=True, )
	date_being_serviced = fields.Datetime(string='Being Serviced date', readonly=True, )
	date_paused = fields.Datetime(string='Paused date', readonly=True, )
	date_waiting_for_inspection = fields.Datetime(string='Waiting for Inspection date', readonly=True, )
	date_waiting_for_washing = fields.Datetime(string='Waiting for Washing date', readonly=True, )
	date_waiting_for_invoicing = fields.Datetime(string='Waiting for Invoicing date', readonly=True, )
	date_waiting_for_delivery = fields.Datetime(string='Waiting for Delivery date', readonly=True, )
	date_psfu = fields.Datetime(string='PSFU date', readonly=True, )
	date_close = fields.Datetime(string='Close date', readonly=True, )

	pause_type = fields.Selection([
		('personal', 'Хувийн'),
		('delayed', 'Саарал'),
		('checking', 'Шалгалт'),
		('additional_job', 'Нэмэлт засвар')],
		string='Түр зогсолтын шалтгаан', )

	assigned_user_id = fields.Many2one('res.users', string='Зөвлөх', default=_get_user,
		domain="[('groups_id','=',group_engineer_id)]",
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	@api.model
	def _get_default_engineer_group(self):
		group = self.env.ref('mw_motors.group_car_module_engineer')
		return group.id
	group_engineer_id = fields.Many2one('res.groups', string='SA групп', default=_get_default_engineer_group)

	# Repair Order HEADER
	customer_id = fields.Many2one('res.partner', string=u'Харилцагч', copy=False,
		domain="[('car_ids','!=',False)]",
		states={'open': [('readonly', True)],'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	customer_phone = fields.Char(related='customer_id.phone', string="Утас", readonly=True, store=True,)
	customer_address = fields.Char(related='customer_id.street', string="Хаяг", readonly=True, store=True,)

	car_id = fields.Many2one('motors.car', string=u'Тээврийн хэрэгсэл',
		domain="[('partner_id','=',customer_id)]",
		states={'open': [('readonly', True)],'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	car_start_date = fields.Date(related='car_id.start_date', readonly=True, store=True,)
	car_model_id = fields.Many2one(related='car_id.model_id', readonly=True, store=True,)
	car_vin_number = fields.Char(related='car_id.vin_number', readonly=True, store=True,)
	car_state_number = fields.Char(related='car_id.state_number', readonly=True, store=True,)

	odometer_value = fields.Float(string='Хүлээн авах үеийн гүйлт', digits = (16,1), required=True,
		states={'waiting_for_delivery': [('readonly', True)]})
	odometer_value_2 = fields.Float(string='Хүлээлгэн өгөх үеийн гүйлт', digits = (16,1),
		states={'waiting_for_delivery': [('readonly', True)]})
	receive_partner_type = fields.Selection([
		('self', 'Эзэмшигч'),
		('family', 'Гэр бүл'),
		('other', 'Бусад'),],
		default='self', string=u'Үйлчлүүлэгчийг төлөөлж', required=True,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})

	# ========== Bat-ochir ахын загвар дээрх талбар ==========================
	# Customer's requests
	is_clean_external = fields.Boolean(string='Гадна цэвэрхэн', default=False,)
	is_clean_internal = fields.Boolean(string='Дотор цэвэрхэн', default=False,)
	location_mirror_seat = fields.Boolean(string='Толь / Суудлын байрлал', default=False,)
	is_prevention = fields.Boolean(string='Хамгаалах хэрэгсэл авсан', default=False,)
	set_radio_time = fields.Boolean(string='Радио / Цаг тохируулга', default=False,)
	included_old_parts = fields.Boolean(string='Хуучин сэлбэг хийсэн', default=False,)

	repair_suggestion_line = fields.One2many('repair.suggestion.line','parent_id',
		string="Зөвлөгөө")

	before_repair_order_line = fields.One2many('car.repair.order','car_id',
		string="Өмнөх засварууд", readonly=True,
		domain=[('state','in',['waiting_for_delivery','psfu','closed'])])

	# ========== Customer Order Form =========================================
	date_reception = fields.Datetime(string='Хүлээн авах огноо', readonly=True, store=True,
		compute='_compute_date_reception')
	@api.depends('scheduled_date','scheduled_time')
	def _compute_date_reception(self):
		for obj in self:
			if obj.scheduled_date and obj.scheduled_time:
				str_date = "%s %d:00:00" % (obj.scheduled_date, obj.scheduled_time)
				dddd = datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S")
				obj.date_reception = dddd - timedelta(hours=8)
			else:
				obj.date_reception = False

	reception_type = fields.Selection([
		('self', 'Үйлчлүүлэгч авч ирнэ'),
		('us', 'Очиж авна'),],
		default='self', string=u'Хүлээн авах төрөл', required=True,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_with_support_technic = fields.Boolean(string='Сэлгээний машин хэрэглэх?', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	date_delivery = fields.Datetime(string='Хүлээлгэн өгөх огноо', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	delivery_type = fields.Selection([
		('self', 'Үйлчлүүлэгч ирж авна'),
		('us', 'Аваачиж өгнө'),],
		default='self', string=u'Хүлээлгэн өгөх төрөл', required=True,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})

	# Customer's requests
	is_appointment = fields.Boolean(string='Appointment', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_maintenance = fields.Boolean(string='Maintenance', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_internal = fields.Boolean(string='Internal', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_walk_in = fields.Boolean(string='Walk-in', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_general_repair = fields.Boolean(string='General repair (Diagnostic Questionnaire Entry)', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_warranty = fields.Boolean(string='Warranty', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_customer_waiting = fields.Boolean(string='Customer Waiting', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_repeat_repair = fields.Boolean(string='Repeat Repair', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	# Job details
	job_details = fields.Text(string='Job details',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	date_estimated = fields.Datetime(string='Estimated Job Time', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	estimation = fields.Float(string='Estimation time', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	cost_changed = fields.Float(string='Cost changed', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	date_appointment_offering_1 = fields.Datetime(string='Appointment Offering-1', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	date_appointment_offering_2 = fields.Datetime(string='Appointment Offering-2', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	date_appointment = fields.Datetime(string='Appointment date', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	appointment_user_id = fields.Many2one('res.users', string=u'Ажилтан', default=_get_user, required=True,
		states={'open': [('readonly', True)],'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})

	# Parts Stock Confirmation
	parts_request_line = fields.One2many('repair.order.parts.request.line', 'parent_id',
		string='Parts request line')
	parts_request_service_line = fields.One2many('repair.order.parts.request.line', 'parent_service_id',
		string='Үйлчилгээ')
	date_parts = fields.Datetime(string='Confirmation date', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	parts_user_id = fields.Many2one('res.users', string=u'Сэлбэг ажилтан',
		states={'waiting_for_delivery': [('readonly', True)]})

	# Walk-around Check
	is_additional_job_confirmation = fields.Boolean(string='Additional Job Confirmation', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_valuables = fields.Boolean(string='Valuables Yes/No', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_present_estimate_explanation = fields.Boolean(string='Present Estimate w/Explanation', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	car_wash = fields.Selection([
		('needed', 'Needed'),
		('unneeded', 'Unneeded')],
		string='Car Wash', )
	replaced_parts_keep = fields.Selection([
		('yes', 'Yes'),
		('no', 'No')],
		string='Replaced Parts Keep', default='yes')
	memo = fields.Text(string='Memo',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	# Courtesy Items
	seat_cover = fields.Boolean(string='Seat cover', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	floar_mat = fields.Boolean(string='Floor Mat', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	# Payment method
	payment_method = fields.Selection([
		('credit_card', 'Credit Card'),
		('cash', 'Cash'),
		('other', 'Other')],
		string='Payment Method', )
	date_confirmation = fields.Datetime(string='Reception date', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	reception_user_id = fields.Many2one('res.users', string=u'Staff name',
		states={'waiting_for_delivery': [('readonly', True)]})

	front_image = fields.Image(string="Урдаас зураг",
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	rear_image = fields.Image(string="Хойд зураг",
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	right_image = fields.Image(string="Баруун зураг",
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	left_image = fields.Image(string="Зүүн зураг",
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})

	# Signature
	digital_signature = fields.Binary(string='Signature',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	digital_signature_from_file = fields.Binary(string='Signature from File',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})

	@api.onchange('digital_signature_from_file')
	def onch_digital_signature_from_file(self):
		if self.digital_signature_from_file:
			self.digital_signature = self.digital_signature_from_file
			self.digital_signature_from_file = False

	# ========== Diagnosis ===============================================
	# Шинж тэмдэг илрэх үеийн нөхцөл
	diagnosis_description = fields.Text(string='Шинж тэмдэгүүд',
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
	is_warranty = fields.Boolean(string='Warranty',
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
	diagnosis_other = fields.Char(string='Бусад',
		states={'done':[('readonly',True)]})

	# ========== Job Instruction =========================================
	stall_id = fields.Many2one('motors.maintenance.stall', string='Stall NO',
		default=_get_default_stall, required=True,
		states={'open': [('readonly', True)],
			'waiting_for_service': [('readonly', True)],
			'being_serviced': [('readonly', True)],
			'paused': [('readonly', True)],
			'waiting_for_inspection': [('readonly', True)],
			'waiting_for_washing': [('readonly', True)],
			'waiting_for_invoicing': [('readonly', True)],
			'waiting_for_delivery': [('readonly', True)],
			'psfu': [('readonly', True)],
			'closed': [('readonly', True)]})
	stall_number = fields.Char(string='Stall NO',)
	date_estimated_completion = fields.Datetime(string='Estimated Completion', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	# parts_replaced_line = fields.One2many('repair.order.parts.replaced.line', 'parent_id',
	# 	string='Parts replaced line',)
	company_id = fields.Many2one('res.company', 'Компани', index=True, default=lambda self: self.env.company)
	pricelist_id = fields.Many2one('product.pricelist', string=u'Үнийн хүснэгт', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True, readonly=True)
	# Хэрэглэсэн сэлбэг материалууд
	wo_move_lines = fields.One2many('stock.move', 'car_repair_order_id', string=u'Хэрэглэсэн сэлбэг материал',
		readonly=True, help=u"Засварын ажилд хэрэглэгдсэн сэлбэг материал")

	# Ажилтны цаг
	employee_timesheet_line = fields.One2many('repair.order.timesheet.line', 'parent_id',
		string='Employee timesheet')
	@api.depends('employee_timesheet_line.date_start','employee_timesheet_line.date_end')
	def _compute_performance_dates(self):
		for obj in self:
			if obj.employee_timesheet_line:
				ll = obj.employee_timesheet_line.filtered(lambda r: r.date_start).mapped('date_start')
				obj.ji_date_start = min(ll) if ll else False

				ll = obj.employee_timesheet_line.filtered(lambda r: r.date_end).mapped('date_end')
				obj.ji_date_end = max(ll) if ll else False
			else:
				obj.ji_date_start = False
				obj.ji_date_end = False
	ji_date_start = fields.Datetime(string=u'Засвар эхлэх', compute=_compute_performance_dates, store=True, )
	ji_date_end = fields.Datetime(string=u'Засвар дуусах', compute=_compute_performance_dates, store=True, )
	@api.depends('ji_date_start','ji_date_end')
	def _compute_performance_time(self):
		for obj in self:
			if obj.ji_date_start and obj.ji_date_end:
				obj.performance_spend_time = (obj.ji_date_end-obj.ji_date_start).total_seconds() / 3600
				hh = (obj.ji_date_start.hour+8) if (obj.ji_date_start.hour+8) < 23 else (obj.ji_date_start.hour+8)-24
				mm = obj.ji_date_start.minute
				obj.performance_start_time = (hh*3600 + mm*60)/3600
				obj.performance_date_start = (obj.ji_date_start+timedelta(hours=8)).date()
			else:
				obj.performance_spend_time = 0
				obj.performance_start_time = 0
	performance_date_start = fields.Date(string='Эхэлсэн өдөр', compute=_compute_performance_time, store=True, readonly=True, )
	performance_start_time = fields.Float(string='Эхэлсэн цаг', compute=_compute_performance_dates, store=True, readonly=True, )
	performance_spend_time = fields.Float(string='Зарцуулсан цаг', compute=_compute_performance_time, store=True, readonly=True, )

	#
	other_findings_advice = fields.Text(string='Other Findings Advice',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})

	# Pre-delivery Confirmation

	# Job Result Explanation
	is_job_details_explanation = fields.Boolean(string='Job Details Explanation', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_fee_explanation = fields.Boolean(string='Fee Explanation', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_result_confirmation_customer = fields.Boolean(string='Result Confirmation w/Customer', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_fixed = fields.Boolean(string='Fixed', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_level_up = fields.Boolean(string='Level-up', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_no_fixed = fields.Boolean(string='No Fixed', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	is_psfu_plan = fields.Boolean(string='P.S.F.U(Plan)', default=False,
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	# P.S.F.U
	date_psfu_plan = fields.Datetime(string='P.S.F.U(Plan)', copy=False,
		states={'being_serviced': [('readonly', True)]})
	psfu_contact_telephone = fields.Char(string='Telephone NO',
		states={'closed':[('readonly',True)]})
	psfu_contact_email = fields.Char(string='E-mail',
		states={'closed':[('readonly',True)]})
	psfu_contact_other = fields.Char(string='Other',
		states={'closed':[('readonly',True)]})
	date_psfu_actual = fields.Datetime(string='P.S.F.U(Actual)', copy=False,
		states={'being_serviced': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})

	# ========== Estimation =========================================
	parts_invoice_line = fields.One2many('repair.order.parts.invoice.line', 'parent_id',
		string='Parts Invoice line',
		states={'waiting_for_delivery': [('readonly', True)],'waiting_for_delivery': [('readonly', True)]})
	additional_jobs = fields.Text(string='Additional jobs',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	total_estimation = fields.Float(string='Total Estimation',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	advice = fields.Text(string='Advice',
		states={'waiting_for_delivery':[('readonly',True)],'closed':[('readonly',True)]})
	pol_line_ids = fields.Many2many('purchase.order.line', string='Худалдан авалтын мөр', compute='compute_pol_line_ids')
	po_ids = fields.Many2many('purchase.order', string='Худалдан авалт', compute='compute_pol_line_ids')
	po_count = fields.Integer(string='PO тоо', compute='compute_pol_line_ids')
	picking_ids = fields.Many2many('stock.picking', string='Агуулахын баримт', compute='compute_picking')
	picking_count = fields.Integer(string='PO тоо', compute='compute_picking')
	is_ordered = fields.Boolean(string="Захиалагдсан?", readonly=True, compute='compute_po_state', store=True)
	is_nemelt_baraa = fields.Boolean(string="Нэмэлт бараа захиалсан?", compute='compute_is_nemelt_baraa')

	# ========== Close =========================================
	close_zasagdsan = fields.Boolean(string='Засагдсан', copy=False, states={'closed': [('readonly', True)]}, default=False)
	close_ergen_holboo = fields.Boolean(string='Эргэн холбогдох шаарлагатай', copy=False, states={'closed': [('readonly', True)]}, default=False)
	close_zasagdaagui = fields.Boolean(string='Засагдаагүй засварын захиалга', copy=False, states={'closed': [('readonly', True)]}, default=False)
	onoo = fields.Selection([('0','0'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10')], string='Оноо өгөх', copy=False, states={'closed': [('readonly', True)]})

	@api.depends('parts_request_line')
	def compute_is_nemelt_baraa(self):
		for item in self:
			item.is_nemelt_baraa = True if item.parts_request_line.filtered(lambda r:  not r.stock_move_ids) or item.parts_request_service_line.filtered(lambda r:  r.is_nemelt) else False
		
	@api.depends('parts_request_line.is_ordered')
	def compute_po_state(self):
		for item in self:
			item.is_ordered = True if item.parts_request_line.filtered(lambda r: r.is_ordered) else False

	@api.depends('parts_request_line')
	def compute_picking(self):
		for item in self:
			item.picking_ids = item.mapped('parts_request_line.stock_move_ids.picking_id')
			item.picking_count = len(item.picking_ids)
	
	@api.depends('parts_request_line')
	def compute_pol_line_ids(self):
		for item in self:
			item.pol_line_ids = item.mapped('parts_request_line.po_line_many_ids')
			item.po_ids = item.mapped('pol_line_ids.order_id')
			item.po_count = len(item.po_ids)
	
	def view_po(self):
		self.ensure_one()
		action = self.env.ref('purchase.purchase_form_action').read()[0]
		action['domain'] = [('id','in',self.po_ids.ids)]
		return action
	
	def view_picking(self):
		self.ensure_one()
		action = self.env.ref('stock.action_picking_tree_all').read()[0]
		action['domain'] = [('id','in',self.picking_ids.ids)]
		return action
	
	@api.onchange('customer_id','pricelist_id')
	def onchange_customer_id(self):
		self.pricelist_id = self.customer_id.property_product_pricelist and self.customer_id.property_product_pricelist.id or False
		for item in self.parts_request_line:
			item.onchange_price()
		for item in self.parts_request_service_line:
			item.onchange_price()

	_sql_constraints = [
		('name_uniq', 'unique(name)', 'ДУгаар давхардсан байна!'),
	]

	# Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноорог бичлэг устгах боломжтой!'))
		return super(CarRepairOrderSheet, self).unlink()

	# ====== CUSTOM METHODs ===================
	@api.onchange('car_id')
	def onchange_car_id(self):
		if self.car_id:
			self.odometer_value = self.car_id.total_odometer
	@api.onchange('stall_id')
	def onchange_stall_id(self):
		if self.stall_id:
			self.stall_number = self.stall_id.name
	# Үйлчилгээнээс зарцуулах цагийг олох
	@api.onchange('parts_request_service_line')
	def onchange_parts_request_service_line(self):
		self.spend_time = sum(self.parts_request_service_line.mapped('qty'))
			
	# Дуусах огноог олох
	@api.onchange('date_reception','spend_time')
	def onchange_date_reception(self):
		if self.date_reception and self.spend_time:
			self.date_delivery = self.date_reception + timedelta(hours=self.spend_time)
			self.estimation = self.spend_time

	def action_to_draft(self):
		self.state = 'draft'
		self.days_state = 'normal'
		# Бүгдийг нь буцаах
		self.ordered_po_id = False
		for ll in self.parts_request_line:
			ll.is_ordered = False

	def action_to_cancel(self):
		if not self.cancel_type:
			raise UserError(_('Цуцалсан шалтгааныг сонгоно уу!'))
		if not self.cancel_reason:
			raise UserError(_('Цуцалсан шалтгааны тайлбарыг бичнэ үү!'))
		self.state = 'cancelled'

	# Дугаарлалт бодох
	def _set_sequence(self):
		temp = '1'
		date_required = datetime.strftime(self.scheduled_date,'%Y-%m-%d')
		ros = self.env['car.repair.order'].search([('scheduled_date','ilike',date_required[:7])])
		if ros:
			temp = str(len(ros))
		number = 'RO%s%s-%s'%(date_required[2:4],date_required[5:7],temp.zfill(3))
		return number

	# Ажил нээх
	def action_to_open(self):
		# Стол цаг давхцаж шалгах
		if not self._check_stall_time(self):
			raise UserError(_('%s stall-ын %s цагтай давхацсан байна!' % (self.stall_id.name, self.scheduled_time)))
		if not self.name:
			self.name = self._set_sequence()

		setting = self.env['motors.stall.order.setting'].search([
			('state','=','confirmed'),
			('setting_date','<=',datetime.now())], order='setting_date desc', limit=1)
		if not setting:
			raise UserError(_('Stall тохиргоо хийгдээгүй байна!'))
		self.warehouse_id = setting.src_warehouse_id.id
		self.dest_warehouse_id = setting.dest_warehouse_id.id

		self.state = 'open'
		self.date_open = datetime.now()

	# Столны цаг давхцаж байгааг шалгах
	def _check_stall_time(self, ro):
		ros = self.env['car.repair.order'].search([
			('state','not in',['draft','cancelled']),
			('scheduled_date','=',ro.scheduled_date)], order='scheduled_time')
		for rr in ros:
			# Эхлэх цаг шалгах
			if rr.scheduled_time <= ro.scheduled_time and ro.scheduled_time <= rr.scheduled_time+rr.spend_time:
				return False
			# Дуусах цаг шалгах
			if rr.scheduled_time <= ro.scheduled_time+ro.spend_time and ro.scheduled_time+ro.spend_time <= rr.scheduled_time+rr.spend_time:
				return False
		return True

	# 3 дах өдөр лүү оруулах
	def action_to_3days(self):
		if self.state == 'open' and self.days_state == 'normal':
			self.days_state = '3days'
			self.date_3days = datetime.now()
	
	def get_pol_id(self, po_id, product_id):
		f_po_id = po_id.order_line.filtered(lambda r: r.product_id==product_id)
		return f_po_id[0] if f_po_id else False
	
	# Холбоотой сэлбэг захиалах, PO үүсгэх
	def create_purchase_order(self):
		po_id = False
		po_obj = self.env['purchase.order']
		partner = self._get_po_partner()
		dddd = datetime.now()
		if self.is_draft_po and partner:
			po_id = po_obj.search([('partner_id','=',partner),('state','=','draft')], limit=1)
		print ('partner--------',partner)
		if not po_id and self.ordered_po_id:
			po_id = self.ordered_po_id
		for ll in self.parts_request_line:
			if not ll.is_ordered and ll.product_id and ll.product_id.type!='service':
				# PO үүсгэх
				if not po_id:
					vals = {
						'date_order': dddd,
						'picking_type_id': self.warehouse_id.in_type_id.id,
						'date_planned': dddd,
						'origin': self.name,
						'partner_id': partner,
						'state': 'draft',
						'car_repair_order_id': self.id,
					}
					po_id = self.env['purchase.order'].create(vals)
					self.ordered_po_id = po_id.id
				ll.is_ordered = True
				# PO line бэлдэх, Үүсгэх
				# Багц бол багцын бараагаар үүсгэнэ
				if ll.product_id.is_pack:
					for pack in ll.product_id.wk_product_pack:
						pol_id = self.get_pol_id(po_id, ll.product_id)
						if pol_id:
							pol_id.product_qty += pack.product_quantity * ll.qty
						else:
							pol_vals = {
								'order_id': po_id.id,
								'product_id': pack.product_name.id,
								'name': pack.product_name.name,
								'date_planned': dddd,
								'product_qty': pack.product_quantity * ll.qty,
								'price_unit': 1,
								'product_uom': pack.product_name.uom_id.id,
							}
							pol_id = self.env['purchase.order.line'].create(pol_vals)
						ll.po_line_many_ids += pol_id
				# Багц биш бараа
				else:
					zahialah_too = ll.qty-ll.available_qty-ll.available_qty_nuuts
					if zahialah_too>0:
						pol_id = self.get_pol_id(po_id, ll.product_id)
						if pol_id:
							pol_id.product_qty += zahialah_too
						else:
							pol_vals = {
								'order_id': po_id.id,
								'product_id': ll.product_id.id,
								'name': ll.product_id.name,
								'date_planned': dddd,
								'product_qty': zahialah_too,
								'price_unit': 1,
								'product_uom': ll.product_id.uom_id.id,
							}
							pol_id = self.env['purchase.order.line'].create(pol_vals)
						ll.po_line_many_ids += pol_id

	def compute_available_button(self):
		for line in self.parts_request_line:
			line.compute_available()

	# 3 - 2 руу шилжихэд PO үүсгэх
	def action_to_2days(self):
		if not self.warehouse_id:
			raise UserError(_('Хэрэглэгч дээр агуулах тохируулаагүй байна!'))
		line_data = []
		dddd = datetime.now()
		self.create_purchase_order()
		self.action_to_expense_parts()
		self.days_state = '2days'
		self.date_2days = dddd
		self.date_parts = dddd
		self.parts_user_id = self.env.user.id

	# Захиалга хийх харилцагчийг олох
	def _get_po_partner(self):
		partner = int(self.env['ir.config_parameter'].sudo().get_param('motors_po_partner') or self.env.user.partner_id.id)
		return partner

	def action_to_1days(self):
		self.days_state = '1days'
		self.date_1days = datetime.now()

	# Үлдэгдэл шалгах
	def check_product_qty(self):
		for line in self.parts_request_line:
			quant_obj = self.env['stock.quant']
			domain = [('product_id','=',line.product_id.id),('location_id.usage','=','internal')]
			# Агуулах сонгосон бол агуулахаас хайх
			if self.warehouse_id:
				domain.append(('location_id.set_warehouse_id','=',self.warehouse_id.id))
			quant_ids = quant_obj.sudo().search(domain)
			qty = sum(quant_ids.mapped('quantity')) or 0
			line.is_available = True if line.qty <= qty else False

	def action_to_waiting_service(self):
		if not self.repairman_ids:
			raise UserError(_('Засварчинг сонгоно уу!'))
		for rm in self.repairman_ids:
			emp = self.env['hr.employee'].search([('user_id','=',rm.id)], limit=1)
			if emp:
				ll = self.env['repair.order.timesheet.line'].create(
					{'employee_id': emp.id, 'parent_id': self.id })
		self.state = 'waiting_for_service'
		self.date_waiting_for_service = datetime.now()
		self.days_state = 'start'
		# Мэдэгдэл илгээх
		if self.repairman_ids:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			action_id = self.env['ir.model.data'].get_object_reference('mw_motors', 'action_car_repair_order')[1]
			html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=car.repair.order&action=%s>%s</a></b> дугаартай ажил эхлэхэд бэлэн боллоо!"""% (base_url,self.id,action_id,self.name)
			self.env.user.send_chat(html, [usr.partner_id for usr in self.repairman_ids])

	# Эхлүүлэх
	def action_to_start_service(self):
		self.days_state = False
		self.state = 'being_serviced'
		self.date_being_serviced = datetime.now()
		self.days_state = 'start'
		self.pause_type = False
		# Сэлбэг материалыг зарлага үүсгэх
		# self.action_to_expense_parts()
		# Мэдэгдэл илгээх
		if self.assigned_user_id:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			action_id = self.env['ir.model.data'].get_object_reference('mw_motors', 'action_car_repair_order')[1]
			html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=car.repair.order&action=%s>%s</a></b> дугаартай ажил эхэлсэн."""% (base_url,self.id,action_id,self.name)
			self.env.user.send_chat(html, [self.assigned_user_id.partner_id])
	# Түр зогсоох
	def action_to_pause(self):
		if not self.pause_type:
			raise UserError(_('Түр зогсох шалтгааныг сонгоно уу!'))
		self.state = 'paused'
		self.date_paused = datetime.now()
		html = self.get_ro_url(' ажил Түр зогслоо!')
		self.env.user.send_chat(html, [self.assigned_user_id.partner_id])
	# Нэмэлт ажлын мэдээлэл илгээх
	def send_additional_job_info(self):
		nemelt_ajil = self.parts_request_line.filtered(lambda r:r.is_nemelt)+self.parts_request_service_line.filtered(lambda r:r.is_nemelt)
		if not nemelt_ajil:
			raise UserError(_('Нэмэлт ажлын мэдээллийг оруулна уу!'))
		self.pause_type = 'additional_job'
		self.action_to_pause()
		# Мэдэгдэл илгээх
		if self.assigned_user_id:
			html = self.get_ro_url('дугаартай ажилд нэмэлт ажил бүртгэгдлээ. Шалгана уу!')
			self.env.user.send_chat(html, [self.assigned_user_id.partner_id])

	# Сэлбэг материалыг зарлага үүсгэх
	def action_to_expense_parts(self):
		lines = self.parts_request_line.filtered(lambda r: not r.stock_move_ids)
		if lines:
			if not self.warehouse_id:
				raise UserError(_(u'Зарлага хийх агуулахыг сонгоно уу!'))
			if not self.dest_warehouse_id:
				raise UserError(_(u'Дундын агуулахыг сонгоно уу!'))

			picking_type_id = self.warehouse_id.int_type_id.id
			location_id = self.warehouse_id.lot_stock_id.id
			location_dest_id = self.dest_warehouse_id.lot_stock_id.id
			vals = {
				'scheduled_date': datetime.now(),
				'company_id': self.env.user.company_id.id,
				'location_id': location_id,
				'location_dest_id': location_dest_id,
				'picking_type_id': picking_type_id,
				'origin': self.name,
				'car_repair_order_id': self.id,
			}
			picking = self.env['stock.picking'].with_context(default_picking_type_id=picking_type_id, default_internal_approve=True).create(vals)
			for ll in lines:
				if ll.qty <= 0:
					raise UserError(_('Тоо хэмжээг шалгана уу!'))
				temp = {
					'name': self.name+' '+ll.product_id.display_name,
					'product_id': ll.product_id.id,
					'product_uom': ll.product_id.uom_id.id,
					'product_uom_qty': ll.qty,
					'date': datetime.now(),
					'date_expected': datetime.now(),
					'company_id': self.env.user.company_id.id,
					'state': 'confirmed',
					'location_id': location_id,
					'location_dest_id': location_dest_id,
					'picking_id': picking.id,
					'car_repair_order_part_line_id': ll.id
				}
				self.env['stock.move'].create(temp)
			picking.send_chat_picking_loc()
			# base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			# action_id = self.env['ir.model.data'].get_object_reference('stock', 'action_car_repair_order')[1]
			# html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=car.repair.order&action=%s>%s</a></b> дугаартай ажил дууслаа."""% (base_url,self.id,action_id,self.name)
			# self.env.user.send_chat
				# ll.is_out = True

	def get_ro_url(self, name=''):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('mw_motors', 'action_car_repair_order')[1]
		html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=car.repair.order&action=%s>%s</a></b> %s"""% (base_url,self.id,action_id,self.name, name)
		return html

	# Дуусгах
	def action_to_finish_service(self):
		# ll = self.parts_replaced_line.filtered(lambda r: not r.is_out)
		# if ll:
		# 	raise UserError(_(u'Зарлагадаагүй сэлбэг үлдсэн байна!'))
		not_done = self.wo_move_lines.filtered(lambda l: l.state not in ['done','cancel'])
		if not_done:
			raise UserError(_(u'Сэлбэгийн зарлагын баримт дуусаагүй байна!'))
		self.state = 'waiting_for_inspection'
		self.date_waiting_for_inspection = datetime.now()
		# Мэдэгдэл илгээх
		if self.assigned_user_id:
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			action_id = self.env['ir.model.data'].get_object_reference('mw_motors', 'action_car_repair_order')[1]
			html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=car.repair.order&action=%s>%s</a></b> дугаартай ажил дууслаа."""% (base_url,self.id,action_id,self.name)
			self.env.user.send_chat(html, [self.assigned_user_id.partner_id])

	# Хянах, Мөн холбоотой үнийн санал бэлдэх
	def action_to_invoice(self):
		if self.car_wash == 'needed' and self.state != 'waiting_for_washing':
			self.state = 'waiting_for_washing'
			self.date_waiting_for_washing = datetime.now()
			return
		# Дуусгах, Хянах үед check
		if not self.is_clean_external:
			raise UserError(_(u'Гадна цэвэрхэн эсэх!'))
		if not self.location_mirror_seat:
			raise UserError(_(u'Толь / Суудлын байрлал тохируулаагүй байна!'))
		if not self.is_clean_internal:
			raise UserError(_(u'Дотор цэвэрхэн эсэх!'))
		if not self.is_prevention:
			raise UserError(_(u'Хамгаалах хэрэгсэл аваагүй байна!'))
		if not self.set_radio_time:
			raise UserError(_(u'Радио / Цаг тохируулаагүй байна!'))
		self.state = 'waiting_for_invoicing'
		self.date_waiting_for_invoicing = datetime.now()
		# Үнийн санал бэлдэх
		# Үйлчилгээний бараа нэмэх
		# Amaraa huu buruu bodjee
		# for ll in self.maintenance_type_ids:
		# 	if ll.product_id:
		# 		vals = {'product_id':ll.product_id.id, 'qty':1,
		# 		        'labour_hours': ll.work_time, 'price': ll.price}
		# 		self.parts_invoice_line = [(0,0,vals)]
		# # Хэрэглэсэн сэлбэгээс нэмэх
		# for ll in self.wo_move_lines:
		# 	if ll.quantity_done > 0:
		# 		vals = {'product_id':ll.product_id.id, 'qty':ll.quantity_done,
		# 		        'labour_hours': 0, 'price': ll.product_id.lst_price}
		# 		self.parts_invoice_line = [(0,0,vals)]

	def action_to_back(self):
		self.state = 'being_serviced'
		# Мэдэгдэл илгээх
		# ('draft', 'Draft'),
		# ('open', 'Open'),
		# ('waiting_for_service', 'Waiting for Service'),
		# ('being_serviced', 'Being Serviced'),
		# ('paused', 'Paused'),
		# ('waiting_for_inspection', 'Waiting for Inspection'),
		# ('waiting_for_washing', 'Waiting for Washing'),
		# ('waiting_for_invoicing', 'Waiting for Invoicing'),
		# ('waiting_for_delivery', 'Waiting for Delivery'),
		# ('psfu', 'PSFU'),
		# ('closed', 'Closed'),
		# ('cancelled', 'Cancelled')
		if self.state=='open':
			self.state = 'draft'
		elif self.state=='waiting_for_service':
			self.state = 'open'
		elif self.state=='being_serviced':
			self.state = 'waiting_for_service'
		elif self.state=='paused':
			self.state = 'being_serviced'
		elif self.state=='waiting_for_inspection':
			self.state = 'paused'
		elif self.state=='waiting_for_washing':
			self.state = 'waiting_for_inspection'
		elif self.state=='waiting_for_invoicing':
			self.state = 'waiting_for_washing'
		elif self.state=='waiting_for_delivery':
			self.state = 'waiting_for_invoicing'
		elif self.state=='psfu':
			self.state = 'waiting_for_delivery'
		elif self.state=='closed':
			self.state = 'psfu'
		# if self.repairman_ids:
		html = self.get_ro_url('дугаартай ажил буцаагдлаа!')
		p_ids = self.repairman_ids.mapped('partner_id') + self.assigned_user_id.partner_id
		self.env.user.send_chat(html, p_ids)

	def action_to_paid(self):
		self.state = 'waiting_for_delivery'
		self.date_waiting_for_delivery = datetime.now()

	def action_to_psfu(self):
		if not self.date_psfu_plan:
			raise UserError('P.S.F.U өдрөө оруулна уу!!')
		if not self.psfu_contact_telephone:
			raise UserError('P.S.F.U Холбоо барих утасаа оруулна уу!!')
		self.state = 'psfu'
		self.date_waiting_for_delivery = datetime.now()

	def action_to_close(self):
		if not self.onoo:
			raise UserError('Оноогоо заавал оруулна!!')
		self.state = 'closed'
		self.date_close = datetime.now()

	# Автомат КРОНЫ методууд ==========================
	# Бэлтгэл ажил хийгдээгүй RO мэдээллэх
	@api.model
	def _check_warning_ros(self):
		# Мэдэгдэл илгээх
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('mw_motors', 'action_car_repair_order')[1]
		ros = self.env['car.repair.order'].sudo().search([
			('state','in',['draft','open','waiting_for_service']),
			('is_warning','=',True)])
		for ro in ros:
			html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=car.repair.order&action=%s>%s</a></b> дугаартай ажлын анхааруулга!<br/>%s"""% (base_url,ro.id,action_id,ro.name, ro.warning_messages)
			if ro.assigned_user_id:
				self.env.user.send_chat(html, [ro.assigned_user_id.partner_id])

class CarRepairOrderPartsRequestLine(models.Model):
	_name = 'repair.order.parts.request.line'
	_description = 'Repair Order Parts Request Line'
	_order = 'is_ordered desc, product_id, is_available'

	@api.model
	def _default_nemelt(self):
		print ('self.env.context',self.env.context)
		return self.env.context.get('is_nemelt', False)
	
	name = fields.Char('Нэр', compute='compute_name')
	parent_id = fields.Many2one('car.repair.order', string='Parent', ondelete='cascade', readonly=True)
	parent_service_id = fields.Many2one('car.repair.order', string='Parent service', ondelete='cascade', readonly=True)
	product_id = fields.Many2one('product.product', string=u'Сэлбэг/Материал', required=True,)
	default_code = fields.Char(string=u'Парт дугаар', readonly=True, related='product_id.default_code', store=True)
	qty = fields.Float(string='Тоо хэмжээ', required=True, default=1, digits=(16,1))
	available_qty = fields.Float(string=u'Үлд', compute='compute_available', store=True)
	available_qty_nuuts = fields.Float(string=u'Үлд нөөцлөлт', compute='compute_available', store=True)
	available_qty_template = fields.Float(string=u'Хөрөв үлд', compute='compute_available', store=True)
	is_available = fields.Boolean(string="Үлдэгдэл?", default=False)
	is_pm_material = fields.Boolean(string="PM material?", default=False)
	is_ordered = fields.Boolean(string="Захиалагдсан?", default=False, readonly=True, compute='compute_po_state', store=True)
	po_line_many_ids = fields.Many2many('purchase.order.line', 'purchase_order_line_ro_parts_line', 'parts_id', 'pol_id', string='POL many')
	eta_date = fields.Datetime(string="ETA", )
	delivered_qty = fields.Float(string='Delivered qty', readonly=True, store=True,
		compute='_compute_delivered_qty')
	price_unit = fields.Float('Нэгж үнэ', readonly=True)
	sub_total = fields.Float('Нийт үнэ', compute='compute_total', store=True, readonly=True)
	motors_maintenance_type_id = fields.Many2one('motors.maintenance.type', compute='compute_motors_maintenance_type_id', store=True)
	stock_move_ids = fields.One2many('stock.move', 'car_repair_order_part_line_id', string='Барааны хөдөлгөөн')
	stock_move_state = fields.Char(string='Хөд төлөв', compute='compute_sm_state')
	po_state = fields.Char(string='PO төлөв', compute='compute_po_state')
	is_nemelt = fields.Boolean(string=u'Нэмэлт эсэх', default=_default_nemelt)

	@api.depends('stock_move_ids.state')
	def compute_sm_state(self):
		for item in self:
			item.stock_move_state = '\n'.join(item.stock_move_ids.mapped('state'))

	@api.depends('po_line_many_ids.state')
	def compute_po_state(self):
		for item in self:
			item.po_state = '\n'.join(item.po_line_many_ids.mapped('state'))
			if all(m.state == 'cancel' for m in item.po_line_many_ids) or not item.po_line_many_ids:
				item.is_ordered = False
			else:
				item.is_ordered = True

	@api.depends('parent_id.warehouse_id','product_id')
	def compute_available(self):
		quant_obj = self.env['stock.quant']
		for item in self:
			quant_ids = []
			quant_temp_ids = []
			domain = self.env['product.product'].get_qty_template_domain(item.product_id)
			if item.parent_id.warehouse_id:
				quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.set_warehouse_id','=',item.parent_id.warehouse_id.id),('location_id.usage','=','internal')])
				domain+=[('location_id.set_warehouse_id','=',item.parent_id.warehouse_id.id),('location_id.usage','=','internal')]
				quant_temp_ids = quant_obj.search(domain)
			else:
				quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.usage','=','internal')])
				domain+=[('location_id.usage','=','internal')]
				quant_temp_ids = quant_obj.search(domain)
			item.available_qty_template = sum(quant_temp_ids.mapped('quantity'))
			item.available_qty = sum(quant_ids.mapped('quantity'))
			item.available_qty_nuuts = sum(quant_ids.mapped('reserved_quantity'))
			

	@api.depends('product_id')
	def compute_motors_maintenance_type_id(self):
		for item in self:
			item.motors_maintenance_type_id = item.product_id.motors_maintenance_type_ids[0].id if item.product_id.motors_maintenance_type_ids else False

	@api.depends('product_id','qty')
	def compute_name(self):
		for item in self:
			item.name = (item.product_id.name or '')+' '+("{0:,.0f}".format(item.qty) or '')
	
	@api.onchange('product_id','parent_id','parent_service_id')
	def onchange_price(self):
		final_price = 0
		p_list_id = False
		partner_id = False
		if self.parent_id.pricelist_id:
			p_list_id = self.parent_id.pricelist_id
			partner_id = self.parent_id.customer_id
		elif self.parent_service_id.pricelist_id:
			p_list_id = self.parent_service_id.pricelist_id
			partner_id = self.parent_service_id.customer_id
		if p_list_id and self.product_id:
			final_price, rule_id = p_list_id.get_product_price_rule(self.product_id, self.qty or 1.0, partner_id)
		elif self.product_id:
			final_price = self.product_id.lst_price
		self.price_unit = final_price
	
	@api.depends('price_unit','qty')
	def compute_total(self):
		for item in self:
			item.sub_total = item.qty*item.price_unit
	
	@api.depends('po_line_many_ids.qty_received')
	def _compute_delivered_qty(self):
		for obj in self:
			obj.delivered_qty = sum(obj.po_line_many_ids.mapped('qty_received'))
	
	@api.onchange('product_id')
	def onchange_product_id(self):
		if self.product_id:
			self.default_code = self.product_id.default_code

	# Overrided methods ================
	def unlink(self):
		for s in self:
			if s.is_ordered or s.po_line_many_ids:
				raise UserError(_('Бичлэг устгах боломжтой!'))
		return super(CarRepairOrderPartsRequestLine, self).unlink()

class CarRepairOrderPartsReplacedLine(models.Model):
	_name = 'repair.order.parts.replaced.line'
	_description = 'Repair Order Parts Replaced Line'
	_order = 'is_ordered desc, product_id, default_code'

	parent_id = fields.Many2one('car.repair.order', string='Parent', ondelete='cascade', readonly=True, )

	job_description_id = fields.Many2one('motors.repair.job.description', string='Засварын дэлгэрэнгүй',)
	product_id = fields.Many2one('product.product', string=u'Сэлбэг материал', required=True,)
	default_code = fields.Char(string=u'Парт дугаар', readonly=True, )
	qty = fields.Float(string='Тоо хэмжээ', required=True, default=0, digits=(16,1))
	qty_available = fields.Float(string=u'Үлдэгдэл', default=0, )
	qty_convert_available = fields.Float(string=u'Хөрвөсөн үлдэгдэл', default=0,
		help=u'Хөрвөсөн кодтой сэлбэгийн үлдэгдлийг харуулна')
	price_unit = fields.Float(string=u'Нэгж үнэ', required=True, default=0,)
	total_price = fields.Float(string=u'Нийт үнэ', required=True, compute=0,)
	result = fields.Selection([
		('processing', 'Хийгдэж байгаа'),
		('done', 'Дууссан')], string="Үр дүн", default='processing')
	user_id = fields.Many2one('res.users', string='Засварчин', )

	is_ordered = fields.Boolean(string="Ordered?", default=False)
	is_out = fields.Boolean(string="Зарлага үүссэн?", default=False)

	@api.onchange('product_id')
	def onchange_product_id(self):
		if self.product_id:
			self.default_code = self.product_id.default_code
			###

			quant_obj = self.env['stock.quant']
			domain = [('product_id','=',self.product_id.id),('location_id.usage','=','internal')]
			# Агуулах сонгосон бол агуулахаас хайх
			if self.parent_id.warehouse_id:
				domain.append(('location_id.set_warehouse_id','=',self.parent_id.warehouse_id.id))
			quant_ids = quant_obj.sudo().search(domain)
			qty = 0
			qty = sum(quant_ids.mapped('quantity'))
			self.qty_available = qty
			# Хөрвөсөн кодтой барааны үлдэгдэл
			domains = [('product_id','!=',self.product_id.id),
						 ('product_id.product_tmpl_id','=', self.product_id.product_tmpl_id.id),
						 ('location_id.usage','=', 'internal')]
			if self.parent_id.warehouse_id:
				domains.append(('location_id.set_warehouse_id','=', self.parent_id.warehouse_id.id))

			quant_template_ids = quant_obj.sudo().search(domains)
			qty = 0
			qty = sum(quant_template_ids.mapped('quantity'))
			self.qty_convert_available = qty

			# Хамгийн сүүлд зарлага хийсэн огноо

			# if self.parent_id.technic_id:
			# 	move = self.env['stock.move'].search([
			# 		('technic_id','=',self.parent_id.technic_id.id),
			# 		('state','=','done'),
			# 		('picking_id.picking_type_id.code','=','outgoing'),
			# 		('product_id','=',self.product_id.id)], limit=1, order='date desc')
			# 	if move:
			# 		self.last_expense_date = move.date
			# 	else:
			# 		self.last_expense_date = u'Өмнө нь гараагүй'


	# Overrided methods ================
	def unlink(self):
		for s in self:
			if s.is_ordered or s.is_out:
				raise UserError(_('Бичлэг устгах боломжтой!'))
		return super(CarRepairOrderPartsReplacedLine, self).unlink()

class RepairOrderAdditionalJobLine(models.Model):
	_name = 'repair.order.additional.job.line'
	_description = 'RO Additional Job Line'
	# Columns
	parent_id = fields.Many2one('car.repair.order', string='Parent ID', ondelete='cascade')

	job_description_id = fields.Many2one('motors.repair.job.description', string='Засварын дэлгэрэнгүй',)
	product_id = fields.Many2one('product.product', string=u'Сэлбэг материал', required=True,)
	default_code = fields.Char(string=u'Парт дугаар', readonly=True, )
	qty = fields.Float(string='Тоо хэмжээ', required=True, default=0, digits=(16,1))

	suggestion_type = fields.Selection([
		('change', 'Солих'),
		('add', 'Нэмэх'),
		('tuning', 'Тохируулах'),],
		default='change', string=u'Зөвлөгөө', required=True,)
	status = fields.Selection([
		('urgent', 'Яаралтай'),
		('short_time', 'Ойрын үед'),
		('long_time', 'Урт хугацаанд'),],
		default='urgent', string=u'Төлөв', required=True,)

	@api.onchange('product_id')
	def onchange_product_id(self):
		if self.product_id:
			self.default_code = self.product_id.default_code

class CarROTimesheetLine(models.Model):
	_name = 'repair.order.timesheet.line'
	_description = 'RO Timesheet Line'

	# Columns
	parent_id = fields.Many2one('car.repair.order', string='Parent ID', ondelete='cascade')

	employee_id = fields.Many2one('hr.employee', string=u'Засварчин', required=True, )
	notes = fields.Char(string=u'Тэмдэглэл', )
	date_start = fields.Datetime(string=u'Эхэлсэн цаг', copy=False,)
	date_end = fields.Datetime(string=u'Дууссан цаг', copy=False,)

	state = fields.Selection(related='parent_id.state', string=u'Төлөв', store=True, readonly=True, )

	@api.depends('date_start','date_end')
	def _compute_time(self):
		for obj in self:
			time = 0
			o1 = 0
			o2 = 0
			if obj.date_start and obj.date_end:
				# Ажилласан цаг
				date = obj.date_start
				end_date = obj.date_end
				time = (end_date-date).total_seconds() / (60*60)
				# Зарцуулсан цаг + байх ёстой
				if time < 0:
					raise UserError(_(u'Цагийг зөв оруулна уу!'))

			obj.spend_time = time
			obj.over_time = 0

	spend_time = fields.Float(compute=_compute_time, store=True, string=u'Зарцуулсан цаг')
	over_time = fields.Float(compute=_compute_time, store=True, string=u'Илүү цаг', default=0 )

class CarRepairOrderPartsInvoiceLine(models.Model):
	_name = 'repair.order.parts.invoice.line'
	_description = 'Repair Order Parts Invoice Line'
	_order = 'product_id, default_code'

	parent_id = fields.Many2one('car.repair.order', string='Parent', ondelete='cascade', readonly=True, )

	product_id = fields.Many2one('product.product', string=u'Replaced parts', required=True,)
	default_code = fields.Char(string=u'Part NO', )
	qty = fields.Float(string='Тоо хэмжээ', required=True, default=0, digits=(16,1))
	labour_hours = fields.Float(string="Labour Hours", )
	price = fields.Float(string="Price", )

class RepairSuggestionLine(models.Model):
	_name = 'repair.suggestion.line'
	_description = 'Repair Suggestion Line'
	_order = 'parent_system_id, system_id'

	parent_id = fields.Many2one('car.repair.order', string='Parent', ondelete='cascade', readonly=True, )

	parent_system_id = fields.Many2one('motors.damaged.type', string='Эд анги', required=True,
		domain="[('parent_id','=',False)]", )
	system_id = fields.Many2one('motors.damaged.type', string=u'Сэлбэг', required=True,
		domain="[('parent_id','=',parent_system_id)]", )
	suggestion_type = fields.Selection([
		('change', 'Солих'),
		('add', 'Нэмэх'),
		('tuning', 'Тохируулах'),],
		default='change', string=u'Зөвлөгөө', required=True,)
	status = fields.Selection([
		('urgent', 'Яаралтай'),
		('short_time', 'Ойрын үед'),
		('long_time', 'Урт хугацаанд'),],
		default='urgent', string=u'Төлөв', required=True,)

class product_product(models.Model):
	_inherit = 'product.product'

	def get_qty_template_domain(self, product_id):
		return [('product_id.product_tmpl_id','=',product_id.product_tmpl_id.id),('product_id','!=',product_id.id)]