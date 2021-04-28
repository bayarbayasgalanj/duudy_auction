# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import calendar

import logging
_logger = logging.getLogger(__name__)

class MotorsStallOrderSetting(models.Model):
	_name = 'motors.stall.order.setting'
	_description = 'Motors Stall Order Setting'
	_order = 'name'

	# Columns
	branch_id = fields.Many2one('res.branch', string='Салбар', 
		states={'confirmed': [('readonly', True)]})
	name = fields.Char(string='Нэр', required=True, copy=False,
		states={'confirmed': [('readonly', True)]})
	setting_date = fields.Date(string='Эхлэх огноо', copy=False, 
		states={'confirmed': [('readonly', True)]})
	line_ids = fields.One2many('motors.stall.order.setting.line', 'parent_id', string='Lines', copy=True,
		states={'confirmed': [('readonly', True)]})
	validator_id = fields.Many2one('res.users', string='Баталсан', readonly=True)

	start_time = fields.Float(string='Эхлэх цаг', digits=(16,2), default=0, required=True, copy=True,
		states={'confirmed': [('readonly', True)]})
	end_time = fields.Float(string='Дуусах цаг', digits=(16,2), default=0, required=True, copy=True, 
		states={'confirmed': [('readonly', True)]})
	multipler_time = fields.Float(string='Бүхэлдэх цаг', digits=(16,2),
		help="Захиалгын цаг дуусах үед дараагийн захиалга эхлэх цагийг бүхэлдэх тохиргоо",
		states={'confirmed': [('readonly', True)]})

	lunch_time = fields.Float(string='Цайны цаг', digits=(16,2), default=0, required=True, copy=True, 
		help="Үргэлжлэх хугацаа байна",
		states={'confirmed': [('readonly', True)]})

	src_warehouse_id = fields.Many2one('stock.warehouse', string='Үндсэн агуулах', 
		states={'confirmed': [('readonly', True)]})
	dest_warehouse_id = fields.Many2one('stock.warehouse', string='Дундын агуулах', 
		states={'confirmed': [('readonly', True)]})
	
	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', 'Хаасан'),
		], default='draft', required=True, string='State', )

	_sql_constraints = [
        ('setting_date_uniq', 'unique (branch_id, setting_date)','Эхлэх өдөр давхардсан байна!')]

	# --------- OVERRIDED ----------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Зөвхөн ноорог бичлэгийг устгах боломтой!'))
		return super(MotorsStallOrderSetting, self).unlink()

	# Өгөгдсөн өдрийн эхлэх, дуусах цаг авах
	def _get_min_max_dates(self, dddd):
		dddd += timedelta(hours=8)
		day_name = dddd.strftime("%A").lower()
		setting = self.env['motors.stall.order.setting'].search([
			('state','=','confirmed'),
			('setting_date','<=',dddd)], order='setting_date desc', limit=1)
		if not setting:
			raise UserError(_('Цагийн хуваарийн тохиргоо олдсонгүй, Admin-д хандана уу!'))
		min_date = self.env['motors.stall.order.setting.day.line'].search([
				('parent_parent_id','=',setting.id),
				('day','=',day_name)], order='start_time', limit=1)
		max_date = self.env['motors.stall.order.setting.day.line'].search([
			('parent_parent_id','=',setting.id),
			('day','=',day_name)], order='end_time desc', limit=1)
		if min_date:
			return {'min': int(min_date.start_time),
			        'max': int(max_date.end_time),
			        'multipler': setting.multipler_time,
			        'id': setting.id }
		else:
			False
	# Өгөгдсөн өдрийн цагийн хуваарийг авна
	def _get_timetable_lines(self, dddd):
		dddd += timedelta(hours=8)
		day_name = dddd.strftime("%A").lower()
		setting = self.env['motors.stall.order.setting'].search([
			('state','=','confirmed'),
			('setting_date','<=',dddd)], order='setting_date desc', limit=1)
		if not setting:
			raise UserError(_('Цагийн хуваарийн тохиргоо олдсонгүй, Admin-д хандана уу!'))
		# CELL
		lines = self.env['motors.stall.order.setting.line'].search([
			('parent_id','=',setting.id)], order='sequence, name')
		if lines:
			return lines
		else:
			return False

	# ---------- CUSTOM ------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		if not self.line_ids:
			raise UserError(_('Хуваарийн мөрийг оруулна уу!'))
		self.state = 'confirmed'
		self.validator_id = self.env.user.id

class MotorsStallOrderSettingLine(models.Model):
	_name = 'motors.stall.order.setting.line'
	_description = 'Stall Order Setting Line'
	_order = 'sequence, name'

	@api.model
	def _set_timetable_line(self):
		lines = []
		st = 0
		et = 0
		lt = 0
		context = self.env.context
		if context.get("start_time") > 0:
			st = context.get("start_time")
		if context.get("end_time") > 0:
			et = context.get("end_time")
		if context.get("lunch_time") > 0:
			lt = context.get("lunch_time")
		temp = {'day': 'monday','start_time': st,'end_time': et,'lunch_time': lt}
		ll = self.env['motors.stall.order.setting.day.line'].create(temp)
		lines.append(ll.id)
		temp = {'day': 'tuesday','start_time': st,'end_time': et,'lunch_time': lt}
		ll = self.env['motors.stall.order.setting.day.line'].create(temp)
		lines.append(ll.id)
		temp = {'day': 'wednesday','start_time': st,'end_time': et,'lunch_time': lt,}
		ll = self.env['motors.stall.order.setting.day.line'].create(temp)
		lines.append(ll.id)
		temp = {'day': 'thursday','start_time': st,'end_time': et,'lunch_time': lt,}
		ll = self.env['motors.stall.order.setting.day.line'].create(temp)
		lines.append(ll.id)
		temp = {'day': 'friday','start_time': st,'end_time': et,'lunch_time': lt,}
		ll = self.env['motors.stall.order.setting.day.line'].create(temp)
		lines.append(ll.id)
		temp = {'day': 'saturday','start_time': st,'end_time': et,'lunch_time': lt,}
		ll = self.env['motors.stall.order.setting.day.line'].create(temp)
		lines.append(ll.id)
		temp = {'day': 'sunday','start_time': st,'end_time': et,'lunch_time': lt,}
		ll = self.env['motors.stall.order.setting.day.line'].create(temp)
		lines.append(ll.id)
		return [(6,0, lines)]

	parent_id = fields.Many2one('motors.stall.order.setting', string="Parent ID", ondelete='cascade')
	
	state = fields.Selection(related='parent_id.state', readonly=True, store=True,)
	setting_date = fields.Date(related='parent_id.setting_date', readonly=True, store=True,)

	sequence = fields.Integer(string='Дараалал', required=True,)
	
	@api.depends('stall_id')
	def _compute_fields(self):
		for obj in self:
			obj.name = obj.stall_id.name if obj.stall_id else "---"
	name = fields.Char(string='Нэр', readonly=True, store=True, compute=_compute_fields )
	stall_id = fields.Many2one('motors.maintenance.stall', string="Stall", required=True,)
	
	employee_ids = fields.Many2many('hr.employee', string="Ажилтан", )

	line_ids = fields.One2many('motors.stall.order.setting.day.line', 'parent_id', string='Хуваарь', 
		default=_set_timetable_line, copy=True)

	total_work_time = fields.Float(string='Нийт ажиллах цаг', compute='_compute_fields', store=True, readonly=True, )
	total_lunch_time = fields.Float(string='Нийт цайны цаг', compute='_compute_fields', store=True, readonly=True, )
	@api.depends('line_ids','line_ids.work_time','line_ids.day')
	def _compute_fields(self):
		for obj in self:
			obj.total_work_time = sum(obj.line_ids.mapped('work_time'))
			obj.total_lunch_time = sum(obj.line_ids.mapped('lunch_time'))

	_sql_constraints = [
		  ('user_line_uniq','unique(parent_id, name)',_('Ажилтан давхардсан байна!'))
	]

	# Ажиллахгүй цаг эсэх
	def _is_blank(self, day_name, start_time):
		cell = self.env['motors.stall.order.setting.day.line'].search([
			('parent_id','=',self.id),
			('day','=',day_name),
			('start_time','<=',start_time),
			('end_time','>=',start_time)], limit=1)
		if cell:
			return False
		else:
			return True

class MotorsStallOrderSettingDayLine(models.Model):
	_name = 'motors.stall.order.setting.day.line'
	_description = 'Stall Order Setting day Line'
	_order = 'start_time'

	parent_id = fields.Many2one('motors.stall.order.setting.line', string="Parent ID", ondelete='cascade')
	
	parent_parent_id = fields.Many2one(related='parent_id.parent_id', readonly=True, store=True,)
	state = fields.Selection(related='parent_id.state', readonly=True, store=True,)
	setting_date = fields.Date(related='parent_id.setting_date', readonly=True, store=True,)
	sequence = fields.Integer(related='parent_id.sequence', readonly=True, store=True,)
	name = fields.Char(related='parent_id.name', readonly=True, store=True,)

	start_time = fields.Float(string='Эхлэх цаг', digits=(16,2), default=0, required=True, copy=True)
	end_time = fields.Float(string='Дуусах цаг', digits=(16,2), default=0, required=True, copy=True)

	work_time = fields.Float(string='Ажиллах цаг', compute='_compute_work_time', store=True, readonly=True, )
	lunch_time = fields.Float(string='Цайны цаг', digits=(16,2), default=1, required=True, copy=True,
		help="Үргэлжлэх хугацаа байна",)
	description = fields.Char(string='Тайлбар', copy=True)

	day = fields.Selection([
			('monday', 'Даваа'),
			('tuesday', 'Мягмар'),
			('wednesday', 'Лхагва'),
			('thursday', 'Пүрэв'),
			('friday', 'Баасан'),
			('saturday', 'Бямба'),
			('sunday', 'Ням'),
		], string="Төрөл", required=True, copy=True)

	@api.depends('start_time','end_time')
	def _compute_work_time(self):
		for obj in self:
			if obj.start_time <= obj.end_time: 
				obj.work_time = obj.end_time - obj.start_time
			else:
				obj.work_time = 0
