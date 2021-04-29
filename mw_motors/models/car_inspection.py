# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class CarInspectionItem(models.Model):
	_name = 'car.inspection.item'
	_description = 'Car Inspect Item'
	_order = 'category, number, name'

	name = fields.Char(string=u'Нэр', size=256, required=True,)
	number = fields.Integer(string=u'Дугаар', )
	is_important = fields.Boolean(string='Чухал эсэх', default=False, )
	image = fields.Binary(string=u'Зураг', attachment=True,
		help="This field holds the image used as logo for the brand, limited to 1024x1024px.")

	category = fields.Selection([
		('ground','GET'),
		('engine','Engine'),
		('transmission','Transmission'),
		('cab','Cab'),
		('electric','Electric'),
		('hydraulic','Hydraulic'),
		('steering','Steering'),
		('breaking','Brake'),
		('frame_body','Frame and Body'),
		('operating','Operating'),
		('power_train','Power train'),
		('implements','Implements'),
		('lubrication','Lubrication'),
		('cooling_system','Cooling system'),
		('attachment','Attachment'),
		('travel','Travel'),
		('tire','Tire')], string='Ангилал', required=True)

	_sql_constraints = [
		('name_uniq', 'unique(name)', 'Нэр давхардсан байна!'),
	]

class CarInspectionSetting(models.Model):
	_name = "car.inspection.setting"
	_description = "Car Inspect Setting"

	name = fields.Char(string=u'Нэр', size=256, required=True,)
	item_line = fields.Many2many('car.inspection.item', string='Үзлэгийн зүйл', required=True)
	attachment_id = fields.Binary(string=u'Хэвлэх загвар', attachment=True,)
	file_name = fields.Char('Файл')

	_sql_constraints = [
		('name_uniq', 'unique(name)', 'Нэр давхардсан байна!'),
	]

	def print_template(self, ids):
		headers = [u' № ',u'Үзлэгийн нэр',u' Хэвийн эсэх', u'Тайлбар']
		datas = []
		obj = self.env['car.inspection.setting'].search([('id','=',ids)])
		categ_temp = ''
		for line in obj.item_line:
			categ_name = dict(line._fields['category'].selection).get(line.category)
			if categ_temp != categ_name:
				temp = ['',' - "'+categ_name+'"', '', '']
				datas.append(temp)
				categ_temp = categ_name

			desc = '__________________'
			temp = [str(line.number),(line.name), "__", desc]
			datas.append(temp)

		res = {'header': headers, 'data':datas}
		return res

class CarInspection(models.Model):
	_name = 'car.inspection'
	_description = 'Car inspection'
	_order = 'date_inspection desc, date_record desc'
	_inherit = 'mail.thread'

	@api.model
	def _get_user(self):
		return self.env.user.id

	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})

	origin = fields.Text(string=u"Эх баримт", readonly=True)
	name = fields.Char(string=u'Дугаар', readonly=True,)
	date_inspection = fields.Date(u'Үзлэгийн огноо', required=True, copy=False,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})
	date_record = fields.Datetime(u'Нээсэн огноо', readonly=True,
		copy=False, default=datetime.now())

	user_id = fields.Many2one('res.users', string=u'Ажилтан', default=_get_user, required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})
	customer_id = fields.Many2one('res.partner', string=u'Харилцагч', copy=False,
		states={'done': [('readonly', True)]})

	car_id = fields.Many2one('motors.car', string=u'Тээврийн хэрэгсэл', required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})
	odometer_value = fields.Float(string='Гүйлт', digits = (16,1), required=True,
		states={'done': [('readonly', True)]})

	inspection_type = fields.Selection([
			('simple', u'Энгийн үзлэг'),
			('receive', u'Хүлээх авах үзлэг'),
			('pm_express', u'PM express-ын үзлэг'),],
			default='simple', string=u'Үзлэгийн төрөл', required=True,)

	inspection_line = fields.One2many('car.inspection.line', 'parent_id',
		string='Үзлэгийн мөр', required=True,
		states={'done': [('readonly', True)]})

	previous_customer_note = fields.Text(string="Харилцагчийн өмнөх тэмдэглэл", readonly=True)
	customer_note = fields.Text("Харилцагчийн тэмдэглэл",
		states={'done': [('readonly', True)]})
	maintenance_note = fields.Text("Засварын тэмдэглэл",
		states={'done': [('readonly', True)]})

	state = fields.Selection([
			('draft', u'Ноорог'),
			('open', u'Нээлттэй'),
			('done', u'Дууссан'),
			('cancelled', u'Цуцлагдсан'),],
			default='draft', string=u'Төлөв', track_visibility=True)

	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд',
		states={'done': [('readonly', True)]})

	setting_name = fields.Char(string=u'Тохиргооны нэр', readonly=True,)

	# Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Must be draft!'))
		return super(CarInspection, self).unlink()

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
		if not self.inspection_line:
			inspection_setting = self.car_id.car_setting_id.inspection_config_id
			ctx = dict(self._context or {})
			if 'inspection_id' in ctx:
				inspection_setting = self.env['car.inspection.setting'].browse(ctx['inspection_id'])

			if inspection_setting:
				for line in inspection_setting.item_line:
					vals = {
						'parent_id': self.id,
						'item_id': line.id,
						'check_name': line.name,
						'is_check': True,
					}
					self.env['car.inspection.line'].create(vals)
				# Өмнөх үзлэгийн тайлбар
				last_ins = self.env['car.inspection'].search([
					('car_id','=',self.car_id.id),
					('state','=','done')], order="date_inspection desc", limit=5)
				notes= ''
				for ll in last_ins:
					if ll.customer_note:
						notes += ll.date_inspection.strftime("%Y-%m-%d")+' : \n('+ll.customer_note+')\n'
				self.previous_customer_note = notes
			else:
				raise UserError(_('Not found Inspection list configuration!'))

		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('car.inspection')
		self.setting_name = self.car_id.car_setting_id.inspection_config_id.name or ' - '
		self.state = 'open'

	def action_to_done(self):
		for line in self.inspection_line:
			if not line.is_check and line.item_id.is_important and not line.description:
				raise UserError(_(u'%s - үзлэг нь чухал тул ямар нэгэн тайлбар бичнэ үү!'%line.check_name))
		self.state = 'done'
		self.user_id = self.env.user.id
		# Хэрэв ТББ тооцох биш буюу хөнгөн тэрэг бол
		# Мото цаг, Км ийг update хийнэ
		if not self.car_id.car_setting_id.is_tbb_report:
			if self.odometer_value <= 0:
				raise UserError(_(u'Гүйлтийн заалтыг оруулна уу!'))
			self.car_id.sudo()._increase_odometer(self.date_inspection, self.odometer_value, False)

	def get_lines(self, ids):
		headers = [u' № ',u'Үзлэгийн нэр',u' Хэвийн эсэх', u'Тайлбар']
		datas = []
		obj = self.env['car.inspection'].search([('id','=',ids)])
		categ_temp = ''
		for line in obj.inspection_line:
			categ_name = dict(line.item_id._fields['category'].selection).get(line.category)
			if categ_temp != categ_name:
				temp = ['',' - "'+categ_name+'"', '', '']
				datas.append(temp)
				categ_temp = categ_name

			check = u'Тийм' if line.is_check else u'Үгүй'
			desc = line.description if line.description else '__________________'
			temp = [str(line.number),(line.item_id.name), check, desc]
			datas.append(temp)

		res = {'header': headers, 'data':datas}
		return res

class CarInspectionLine(models.Model):
	_name = "car.inspection.line"
	_description = "Car Inspect Line"
	_order = 'category, number, check_name'

	parent_id = fields.Many2one('car.inspection',string='Parent', ondelete='cascade')
	state = fields.Selection(related='parent_id.state', readonly=True, store=True)
	item_id = fields.Many2one('car.inspection.item',string='Үзлэг', required=True,)
	category = fields.Selection(related='item_id.category', readonly=True, store=True)
	number = fields.Integer(related='item_id.number', readonly=True, store=True)
	check_name = fields.Char(string='Үзлэгийн нэр', size=256, required=True)
	is_check = fields.Boolean(string='Хэвийн эсэх', default=True, )
	description = fields.Char(string='Тайлбар', size=256)

	@api.onchange('description')
	def onchange_description(self):
		if self.description:
			self.is_check = False

