# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
from dateutil.relativedelta import relativedelta
import collections
from odoo.osv import expression

class CarBrand(models.Model):
	_name = 'motors.car.brand'
	_description = 'Car Brand'
	_order = 'name'

	name = fields.Char(string=u'Үйлдвэрлэгч', size=32, required=True,)
	description = fields.Text(string=u'Тайлбар', )
	image = fields.Binary(string='Logo', required=True, attachment=True,
		help="This field holds the image used as logo for the brand, limited to 1024x1024px.")

	image_medium = fields.Binary(string="Medium-sized image", attachment=True,
		help="Medium-sized logo of the brand. It is automatically "
			 "resized as a 128x128px image, with aspect ratio preserved. "
			 "Use this field in form views or some kanban views.")
	image_small = fields.Binary(string="Small-sized image", attachment=True,
		help="Small-sized logo of the brand. It is automatically "
			 "resized as a 64x64px image, with aspect ratio preserved. "
			 "Use this field anywhere a small image is required.")

	_sql_constraints = [
		('name_uniq', 'unique(name)', 'Нэр давхардсан байна!'),
	]

class CarModel(models.Model):
	_name = 'motors.car.model'
	_description = 'Car Model'
	_order = 'name'

	@api.depends('brand_id', 'modelname')
	def _set_modelname(self):
		for item in self:
			if item.brand_id and item.modelname:
				item.name = str(item.brand_id.name)+' / '+str(item.modelname)
			else:
				item.name = "New"

	name = fields.Char(compute='_set_modelname', string=u'Нэр',
					   readonly=True, store=True, default="-")
	modelname = fields.Char(string=u'Загварын нэр', size=64, required=True,)
	brand_id = fields.Many2one('motors.car.brand', string=u'Үйлдвэрлэгч', required=True,)
	image = fields.Binary(related='brand_id.image_medium', string='Зураг', readonly=True,
		help="This field holds the image used as logo for the brand, limited to 1024x1024px.", )
	car_setting_id = fields.Many2one('motors.car.setting', string=u'Тээврийн хэрэгсэл тохиргоо', )
	car_type = fields.Selection(
		related='car_setting_id.car_type', readonly=True, store=True)

	_sql_constraints = [
		('name_uniq', 'unique(name)', 'Нэр давхардсан байна!'),
	]

class CarSetting(models.Model):
	_name = 'motors.car.setting'
	_description = 'Car setting'
	_order = 'report_order, name'

	@api.onchange('model_id')
	def onchange_set_name(self):
		if self.model_id:
			self.name = self.model_id.name+' : Тохиргоо'
		else:
			self.name = "New"

	name = fields.Char(string=u'Нэр', default="-", required=True, )
	model_id = fields.Many2one('motors.car.model', string=u'Загварын нэр', required=True,)
	receive_inspection_id = fields.Many2one('car.inspection.setting', string=u'Хүлээн авах үзлэг', )
	simple_inspection_id = fields.Many2one('car.inspection.setting', string=u'Энгийн үзлэг', )

	report_order = fields.Char(string='Тайлангийн эрэмбэ', default='999')
	seats = fields.Integer(string='Суудлын тоо', help='Number of seats of the vehicle')
	doors = fields.Integer(string='Хаалганы тоо', help='Number of doors of the vehicle')
	fuel_type = fields.Selection([
		('gasoline', 'Gasoline'),
		('diesel', 'Diesel'),
		('electric', 'Electric'),
		('petrol', 'Petrol'),
		('hybrid', 'Hybrid')],
		string='Шатахууны төрөл', help='Fuel Used by the vehicle')

	engine_capacity = fields.Float(string='Хөдөлгүүрийн багтаамж, литр',
		digits=(16, 1), help='Engine capacity litre')
	engine_mark = fields.Char(string='Хөдөлгүүрийн модель', help='Engine mark...')
	engine_type = fields.Char(string='Хөдөлгүүрийн бренд', help='Engine type...')

	body_length = fields.Float(string='Нийт урт, м', digits = (16,1), )
	body_width = fields.Float(string='Нийт өргөн, м', digits = (16,1), )
	body_height = fields.Float(string='Нийт өндөр, м', digits = (16,1), )

	tonnage = fields.Float(string='Даац /кг', digits=(16, 1), )
	fuel_tank_capacity = fields.Float(string='Түлшний танкны багтаамж, литр', digits = (16,1), )
	weight = fields.Float(string='Бүх жин /кг', digits = (16,1), )

	transmission = fields.Selection([
		('manual', 'Механик'),
		('automatic', 'Автомат'),
		('electric', 'Цахилгаан'),
		('hydro', 'Гидро')],
		string='Хурдны хайрцаг', help='Transmission Used by the vehicle')
	transmission_type = fields.Char(string="Модель", help="Transmission type")
	transmission_mark = fields.Char(string="Бренд", help="Transmission mark")

	rpm_min = fields.Float(string='RPM Min',digits = (16,1), required=True)
	rpm_ave = fields.Float(string='RPM Average',digits = (16,1), required=True)
	rpm_max = fields.Float(string='RPM Max',digits = (16,1), required=True)
	fuel_low_idle = fields.Float(string='Fuel low idle',digits = (16,1), required=True)
	fuel_medium_idle = fields.Float(string='Fuel medium idle',digits = (16,1), required=True)
	fuel_high_idle = fields.Float(string='Fuel high idle',digits = (16,1), required=True)

	odometer_unit = fields.Selection([
		('km','Км'),
		('mile','Mile'),
		('m3','м3'),
		('motoh','Мото/цаг'),
		('kmh','Км/цаг')],
		string='Гүйлтийн нэгж',required=True)

	car_type = fields.Selection([
		('sedan','SEDAN'),
		('hatchback','HATCH BACK'),
		('roadster','ROADSTER'),
		
		('cuv','CUV'),
		('suv','SUV'),
		('pickup','PICKUP'),

		('micro','MICRO'),
		('coupe','COUPE'),
		('supercar','SUPER CAR'),

		('coupe','COUPE'),
		('van','VAN'),
		('mini_van','MINI VAN'),

		('campervan','CAMPERVAN'),
		('mini_truck','MINI TRUCK'),
		('truck','TRUCK'),
		],
		string ='Тээврийн хэрэгслийн төрөл',required=True)

	rubber_tired = fields.Boolean(string='Дугуйтай эсэх?', default=True)
	position_format = fields.Char(string='Байрлалын формат', help=u'ЖШ: 1-2,2-2, дамп 1-2,2-4 гэх мэт')
	tire_counts = fields.Integer(string=u'Нийт дугуйн тоо', default=0)

	# Баталгаат хугацаа, гүйлт
	warranty_period = fields.Integer(string=u'Баталгаат хугацаа, сар', help=u'Баталгаат хугацааг сараар тооцно')
	warranty_odometer = fields.Integer(string=u'Баталгаат гүйлт', help=u'Баталгаа өгсөн гүйлт')

	work_time_per_month = fields.Float(string=u'Сарын гүйлт', required=True,
		help=u"Тээврийн хэрэгслийн сард гүйх гүйлт")

	_sql_constraints = [
		('name_uniq', 'unique(model_id)', 'Нэр давхардсан байна!'),
	]

	# ------------ OVERRIDE ================
	def write(self, vals):
		res = super(CarSetting, self).write(vals)
		if 'model_id' in vals:
			model = self.env['motors.car.model'].browse(vals['model_id'])
		return res

	# Methods
	def get_position_format(self, setting_id, context=None):
		obj = self.env['motors.car.setting'].browse(setting_id)
		return obj.position_format or False

class CarPmMaterialConfig(models.Model):
	_name = 'car.pm.material.config'
	_description = 'Car PM material config'
	_order = 'priority, name'

	@api.depends('maintenance_type_id')
	def _set_name(self):
		for obj in self:
			if obj.maintenance_type_id:
				obj.name = obj.maintenance_type_id.name+' / PM config'
			else:
				obj.name = "PM config"
		return True

	@api.depends('pm_material_line')
	def _methods_compute(self):
		# Нийт тоог олгох
		for obj in self:
			obj.total_amount = sum(obj.mapped('pm_material_line.amount'))

	priority = fields.Integer(string='Зэрэглэл', required=True,)
	name = fields.Char(compute='_set_name',string='Нэр', readonly=True, store=True)
	engine_type = fields.Char(string='Хөдөлгүүрийн төрөл', required=True,)

	maintenance_type_id = fields.Many2one('motors.maintenance.type', string=u'Засварын төрөл', required=True,
		domain=[('is_pm','=',True)])
	interval = fields.Integer(string=u'Үйлчилгээний интервал', required=True,)
	work_time = fields.Float(string=u'Засварын цаг', required=True,)
	pm_material_line = fields.One2many('car.pm.material.line', 'parent_id', string='Parent',
		required=True, copy=True)
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн', default=0)
	
	is_main_pm = fields.Boolean(string='Үндсэн PM', default=False,)

	reference_product_id = fields.Many2one('product.product', string=u'Холбоотой үйлчилгээ', 
		domain=[('type','=','service')])
	inspection_setting_id = fields.Many2one('car.inspection.setting', string=u'PM үзлэгийн тохиргоо', )
	fuel_type = fields.Selection([
		('gasoline', 'Gasoline'),
		('diesel', 'Diesel'),
		('electric', 'Electric'),
		('petrol', 'Petrol'),
		('hybrid', 'Hybrid')],
		string='Шатахууны төрөл', help='Fuel Used by the vehicle', default='petrol', required=True,)

	# Хүн цагийн мэдээлэл бүртгэх
	employee_man_hour_line = fields.One2many('motors.pm.employee.man.hour.line', 'parent_id', string='Parent',
		required=True, copy=True)
	total_man_hours = fields.Float(compute='_compute_total_man_hours',
		string=u'Нийт хүн цаг', copy=False, store=True)
	@api.depends('employee_man_hour_line')
	def _compute_total_man_hours(self):
		for obj in self:
			obj.total_man_hours = sum(obj.employee_man_hour_line.mapped('qty')) * obj.work_time

class CarPmMaterialLine(models.Model):
	_name = 'car.pm.material.line'
	_description = 'Car PM material line'
	_order = 'material_id'

	@api.depends('price_unit','qty')
	def _get_amount(self):
		for obj in self:
			obj.amount = obj.qty * obj.price_unit

	parent_id = fields.Many2one('car.pm.material.config', string=u'PM тохиргоо', ondelete='cascade')
	generator_id = fields.Many2one('car.forecast.generator.line', string=u'Forecast', ondelete='cascade')

	maintenance_type_id = fields.Many2one(related='parent_id.maintenance_type_id', string=u'Засварын төрөл', readonly=True,)

	material_id = fields.Many2one('product.product',string='Бараа', required=True,)
	categ_id = fields.Many2one(related='material_id.categ_id', string=u'Ангилал', readonly=True, store=True )
	price_unit = fields.Float(string='Нэгж үнэ', required=True,)
	qty = fields.Float(string='Тоо хэмжээ', digits = (16,1), required=True, default=1)
	amount = fields.Float(compute='_get_amount',
		store=True, string=u'Дүн', copy=False)
	description = fields.Char('Тайлбар', )
	is_depend_season = fields.Boolean(string='Улирлаас хамааралтай эсэх', default=False,
		help="Тухайн материал нь улиралаас хамаарч өөрчлөгддөг эсэх")

	warehouse_id = fields.Many2one('stock.warehouse',string=u'Агуулах', required=False)

	@api.onchange('material_id')
	def onchange_qty(self):
		if self.material_id:
			price_unit = self.material_id.standard_price
			self.price_unit = price_unit

class EmployeeManHourLine(models.Model):
	_name = 'motors.pm.employee.man.hour.line'
	_description = 'Employe Man Hour Line'
	_order = 'job_id'

	parent_id = fields.Many2one('car.pm.material.config', string=u'PM config', ondelete='cascade')
	job_id = fields.Many2one('hr.job',string='Албан тушаал', required=True,)
	qty = fields.Integer(string='Тоо', required=True, default=1)