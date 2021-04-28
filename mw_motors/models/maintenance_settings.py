# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class MaintenanceStall(models.Model):
	_name = 'motors.maintenance.stall'
	_description = 'Motors Maintenance Stall'
	_order = 'name'
	# Columns
	name = fields.Char(string=u'Нэр', required=True, size=64, copy=False )

	_sql_constraints = [('name_uniq', 'unique(name)','Нэр давхардсан байна!'),]

class MaintenanceType(models.Model):
	_name = 'motors.maintenance.type'
	_description = 'Motors Maintenance type'
	_order = 'name'

	# Columns
	name = fields.Char(string=u'Нэр', required=True, size=64, copy=False )
	color = fields.Char(string=u'Өнгө', required=True, default='#fcba03')
	is_pm = fields.Boolean(string=u'PM үйлчилгээ эсэх', default=False)
	
	price = fields.Integer(string='Үнэ', compute='compute_price', store=True)
	work_time = fields.Float(string='Зарцуулах цаг', default=1, required=True,)
	product_id = fields.Many2one('product.product', string=u'Холбоотой Сэлбэг/Материал', )
	product_code = fields.Char(related='product_id.default_code', string=u'Parts NO', readonly=True,  store=True,)

	description = fields.Text(string=u'Тайлбар', )

	maintenance_type = fields.Selection([
			('express_maintenance', 'Express maintenance'),
			('general_repair', 'General repair'),
			('body_and_paint', 'Body & paint'),
			('tuning_and_upgrade', 'Tuning & upgrade')],
		string=u'Засварын төрөл', )

	@api.depends('product_id')
	def compute_price(self):
		for item in self:
			item.price = item.product_id.list_price
	
	_sql_constraints = [
		('type_name_uniq', 'unique(name)','Нэр давхардсан байна!'),
		('type_product_id_uniq', 'unique(product_id)','Бараа давхардсан байна!'),
	]

class product_product(models.Model):
	_inherit = 'product.product'
	
	motors_maintenance_type_ids = fields.One2many('motors.maintenance.type', 'product_id', string='Засварын төрөл')

class MotorsRepairJobDescription(models.Model):
	_name = 'motors.repair.job.description'
	_description = 'Motors Repair Job Description'
	_order = 'name'

	# Columns
	name = fields.Char(string='Засварын нэр', required=True, )

	_sql_constraints = [('name_uniq', 'unique(name)','Нэр давхардсан байна!')]

class MotorsDamagedReason(models.Model):
	_name = 'motors.damaged.reason'
	_description = 'Motors damaged reason'
	_order = 'name'

	@api.depends('code','name')
	def name_get(self):
		result = []
		for s in self:
			name = s.code +'. '+ s.name
			result.append((s.id, name))
		return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('code', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()

	# Columns
	name = fields.Char(u'Нэр', required=True, size=64, )
	code = fields.Char(u'Код', required=True, size=8, )
	description = fields.Text(u'Тайлбар', )

	_sql_constraints = [('damaged_reason_name_uniq', 'unique(name)','Нэр давхардсан байна!')]

class MotorsDamagedType(models.Model):
	_name = 'motors.damaged.type'
	_description = 'Motors damaged type'
	_order = 'name'

	@api.depends('code','name')
	def name_get(self):
		result = []
		for s in self:
			name = s.code +' / '+ s.name
			result.append((s.id, name))
		return result

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('code', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()

	# Columns
	name = fields.Char(u'Нэр', required=True, size=64, )
	code = fields.Char(u'Код', required=True, size=10, )
	parent_id = fields.Many2one('motors.damaged.type', string=u'Толгой систем', copy=False,)
	description = fields.Text(u'Тайлбар', )

	_sql_constraints = [('damaged_type_name_uniq', 'unique(name)','Нэр давхардсан байна!')]