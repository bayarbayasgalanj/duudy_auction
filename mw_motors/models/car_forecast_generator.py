# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import time

import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO

from calendar import monthrange

import logging
_logger = logging.getLogger(__name__)

class CarForecastGenerator(models.Model):
	_name = 'car.forecast.generator'
	_description = 'Car Forecast Generator'
	_order = 'date_start desc'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	date = fields.Datetime(string=u'Үүсгэсэн огноо', readonly=True, default=datetime.now(), copy=False)
	name = fields.Char(string=u'Нэр', copy=False, 
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
	date_start = fields.Date(string=u'Эхлэх огноо', copy=True, required=True,
		states={'done': [('readonly', True)]})
	date_end = fields.Date(string=u'Дуусах огноо', copy=True, required=True,
		states={'done': [('readonly', True)]})

	planner_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, default=_get_user)
	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], default='draft', required=True, string=u'Төлөв', track_visibility=True)

	plan_generated_line = fields.One2many('car.forecast.generator.line', 'parent_id', 'Lines', copy=False,
		states={'done': [('readonly', True)]})

	car_setting_line = fields.One2many('car.forecast.setting.line', 'parent_id', 'Lines', copy=True,
		states={'done': [('readonly', True)]})

	forecast_type = fields.Selection([
			('weekly', u'Төлөвлөгөө үүсгэх'),
			('monthly', u'Сараар'),
			('year', u'Жилээр'),
			('other', u'Бусад'),
		], default='weekly', required=True, string=u'Хугацааны төрөл',
		states={'done': [('readonly', True)]})
	start_last_info = fields.Boolean(string='Сүүлд хийгдсэн мэдээллээс эхлэх', default=False,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})
	is_date_start = fields.Boolean(string=u'Эхлэх огнооноос эсэх?', default=False)

	@api.depends('plan_generated_line')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.mapped('plan_generated_line.total_amount'))
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн', track_visibility=True, default=0)

	excel_data = fields.Binary('Excel file')
	file_name = fields.Char('File name')

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Устгахын тулд эхлээд ноороглох ёстой!'))
		return super(CarForecastGenerator, self).unlink()

	# ============ Custom methods =========
	def export_excel_template(self):
		# INIT
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet('Import template')
		file_name = 'car_import_template.xlsx'

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(10)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		# Draw rows
		worksheet.write(0, 0, u"ID", contest_left)
		worksheet.write(0, 1, u"Техник", contest_left)
		worksheet.write(0, 2, u"Эхлэх гүйлт", contest_left)
		worksheet.write(0, 3, u"Сард ажиллах цаг", contest_left)
		r = 1
		for line in self.env['motors.car'].search([('state','!=','draft')], order="name"):
			worksheet.write(r, 0, line.id, contest_left)
			worksheet.write(r, 1, line.name, contest_left)
			worksheet.write(r, 3, line.car_setting_id.work_time_per_month, contest_left)
			r += 1
		# Close, Save
		workbook.close()
		out = base64.encodestring(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}
	# Excel ээс импорт хийх
	def import_from_excel(self):
		# Өмнөх дата г цэвэрлэх
		self.car_setting_line.unlink()

		if not self.excel_data:
			raise UserError(_(u'Choose import excel file!'))

		# File нээх
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			 raise osv.except_osv(u'Error',u'Importing error.\nCheck excel file!')
		
		book = xlrd.open_workbook(fileobj.name)
		try :
			 sheet = book.sheet_by_index(0)
		except:
			 raise osv.except_osv(u'Warning', u'Wrong Sheet number.')
		
		# Унших
		nrows = sheet.nrows
		setting_lines = []
		for r in range(1,nrows):
			row = sheet.row(r)
			if row[0].value:
				car_id = row[0].value
				start_odometer = row[2].value or 0
				worktime = row[3].value or 0
				_logger.info("--------import ======%s %s ",str(start_odometer), str(car_id))
				temp = (0,0,{
					'car_id': int(car_id),
					'start_odometer': start_odometer,
					'work_time_per_month': worktime,
				})
				setting_lines.append(temp)

		if setting_lines:
			self.car_setting_line = setting_lines
		return True

	# Одоогийн ДАТА наас импорт хийх
	def import_from_current(self):
		self.car_setting_line.unlink()
		cars = self.env['motors.car'].search([
			('state','in',['working','repairing']),
			], order='report_order')
		_logger.info("--------import from ==%d====",len(cars))
		setting_lines = []
		for tt in cars:
			temp = (0,0,{
				'car_id': tt.id,
				'last_pm_priority': tt.last_pm_priority,
				'last_date': tt.last_pm_date,
				'maintenance_type_id': tt.last_pm_id.id,
				'start_odometer': tt.last_pm_odometer,
				'work_time_per_month': tt.work_time_per_month if tt.work_time_per_month > 0 else tt.car_setting_id.work_time_per_month,
			})
			setting_lines.append(temp)
		if setting_lines:
			self.car_setting_line = setting_lines
		return True

	@api.onchange('car_id','car_setting_id')
	def onchange_car_id(self):
		if self.car_setting_id:
			self.work_time_per_month = self.car_setting_id.work_time_per_month

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		self.planner_id = self.env.user.id
		if not self.car_setting_line:
			raise UserError(_(u'Техникүүдийн мэдээллийг оруулна уу!'))
		self.state = 'confirmed'
	
	def action_to_done(self):
		self.planner_id = self.env.user.id
		if not self.plan_generated_line:
			raise UserError(_(u'Урьдчилсан төлөвлөгөө үүсээгүй байна!\n"Generate" товч дээр дарна уу!'))
		for line in self.plan_generated_line:
			line.create_plan()
		self.state = 'done'

	def generate_lines(self):
		# Өмнөх мөрийг устгах
		self.plan_generated_line.unlink()
		for setting_line in self.car_setting_line:
			technic = setting_line.car_id
			last_odometer = setting_line.start_odometer or technic.last_pm_odometer
			last_pm_priority = setting_line.last_pm_priority or technic.last_pm_priority
			last_pm_date = setting_line.last_date or technic.last_pm_date

			# Сүүлд хийгдсэн PM мэдээлэл шалгах
			if not last_odometer:
				raise UserError(_(u'Сүүлд хийгдсэн PM үйлчилгээний гүйлт оруулаагүй байна!\n %s'%technic.name))
			if not last_pm_priority:
				raise UserError(_(u'Сүүлд хийгдсэн PM үйлчилгээний дугаар оруулаагүй байна!\n %s'%technic.name))
			if not last_pm_date:
				raise UserError(_(u'Сүүлд хийгдсэн PM үйлчилгээний огноо оруулаагүй байна!\n %s'%technic.name))

			work_time_per_month = technic.car_setting_id.work_time_per_month

			if work_time_per_month == 0:
				raise UserError(_(u'Сард ажиллах цаг 0 байна! %s %d' % (technic.car_setting_id.name, technic.car_setting_id.id)))

			if not technic.car_setting_id.pm_material_config:
				raise UserError(_(u'PM үйлчилгээний тохиргоо хийгдээгүй байна! %s' % technic.car_setting_id.name))

			pm_line_ids = [0]
			for pm_line in technic.car_setting_id.pm_material_config:
				pm_line_ids.append(pm_line.id)

			# Сүүлд хийгдсэн PM дугаар авна
			idx = last_pm_priority
			# Сүүлд хийгдсэн PM огноо байвал авна, үгүй бол эхлэх огноог авна
			first = True
			# NEW
			if self.is_date_start:
				temp_date = self.date_start
			else:
				temp_date = datetime.now().date()

			# Дуусах огноо хүртэл давтана
			while temp_date < self.date_end:
				# Next PM олох
				if idx+1 < len(pm_line_ids):
					idx += 1
				else:
					idx = 1

				# Дараагийн PM авах
				pm_config = self.env['car.pm.material.config'].browse(pm_line_ids[idx])
				if pm_config.work_time <= 0:
					continue
				interval = pm_config.interval
				if interval <= 0:
					raise UserError(_(u'Interval-ийг тохируулна уу! %s' % technic.car_setting_id.name))
				# INTERVAL-ийг өдөр лүү хөрвүүлнэ
				months = round(interval / work_time_per_month)

				# Техникийн тохиргоон дээр ажиллаж эхлэх огноо байгаа эсэхийг шалгах
				# Хэрэв эхлэх огноо байхгүй бол хэвийн forecast гүйж үргэлжлэнэ
				# Эхлэх огноо зааж өгсөн байгаад болоогүй бол forecast ийг гүйлгэхгүй алгасна
				if setting_line.start_date and setting_line.start_date > temp_date:
					temp_date = self._date_increase(temp_date,months)
					continue
				# ===========================================

				_logger.info("\n---generate ======%s %s %d %d %d",technic.name, temp_date, last_odometer, technic._get_odometer(), interval)
				# Зөв эхлэлийг олох
				# Хэрэв хийгдэх гүйлт нь болоогүй бол хойшлуулна
				if first:
					current_mh = technic._get_odometer()
					print('===', current_mh)
					# ===========================
					diff = (last_odometer+interval) - current_mh
					back_day = round(diff / work_time_per_month)
					if back_day >= 1 and diff > 0:
						temp_date = self._date_increase(temp_date,back_day)
					first = False
				_logger.info("\n---generate 2=====%s %s %d %d %d",pm_config.name, temp_date, (last_odometer+interval), diff, back_day)
				# Өнгөрсөн бол давталтаас гарах
				if temp_date > self.date_end:
					break

				last_odometer += interval
				# Материалын дата бэлдэх
				material_datas = []
				for m_line in pm_config.pm_material_line:
					product = m_line.material_id
					temp = (0,0,{
						'material_id': product.id,
						'price_unit': product.standard_price,
						'qty': m_line.qty,
						'warehouse_id': m_line.warehouse_id.id,
					})
					material_datas.append(temp)

				# Forecast үүсгэх
				vals = {
					'parent_id': self.id,
					'maintenance_type_id': pm_config.maintenance_type_id.id,
					'pm_priority': idx,
					'date_plan': temp_date,
					'car_id': technic.id,
					'pm_odometer': last_odometer,
					'work_time': pm_config.work_time,
					'man_hours': pm_config.total_man_hours,
					'pm_material_line': material_datas,
					'description': pm_config.maintenance_type_id.name,
				}
				line = self.env['car.forecast.generator.line'].create(vals)
				temp_date = self._date_increase(temp_date,months)

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, months):
		add = 30*months
		return temp_date + timedelta(days=add)

	# Miils рүү хөрвүүлэх
	def _unix_time_millis(self, dt, add):
		epoch = datetime.utcfromtimestamp(0)
		date_start = dt
		date_start += timedelta(hours=8+add)
		return (date_start - epoch).total_seconds() * 1000.0

	# Calendar дата бэлдэх
	def get_plan_calendar_datas(self, g_id, mt_ids, context=None):
		datas = {}
		obj = self.env['car.forecast.generator'].browse(g_id)
		series = []
		pm_names = {}
		for line in obj.plan_generated_line:
			if mt_ids:
				# Хэрэв шүүлттэй бол
				if line.maintenance_type_id.id in mt_ids:
					temp = {
						'id': 0,
						'name': line.name,
						'equipment_name': line.car_id.name,
						'pm_odometer': line.pm_odometer,
						'work_time': line.work_time,
						'color': line.maintenance_type_id.color,
						'startDate': self._date_increase(line.date_plan,0),
						'endDate': self._date_increase(line.date_plan,round(line.work_time/24)),
					}
					series.append(temp)
			else:
				# Шүүлтгүй бол бүгдийг зурна
				temp = {
					'id': 0,
					'name': line.name,
					'equipment_name': line.car_id.name,
					'pm_odometer': line.pm_odometer,
					'work_time': line.work_time,
					'color': line.maintenance_type_id.color,
					'startDate': self._date_increase(line.date_plan,0),
					'endDate': self._date_increase(line.date_plan,round(line.work_time/24)),
				}
				series.append(temp)
			if line.maintenance_type_id.name not in pm_names:
				pm_names[line.maintenance_type_id.name] = {
					'name':line.maintenance_type_id.name,
					'id': line.maintenance_type_id.id,
					'color': line.maintenance_type_id.color,
				}
		if series:
			datas['calendar_data'] = series
			datas['pm_names'] = pm_names
		else:
			datas['calendar_data'] = False
			datas['pm_names'] = False
		return datas
	
	# Timeline дата бэлдэх
	def get_plan_datas(self, g_id, context=None):
		datas = {}
		obj = self.env['car.forecast.generator'].browse(g_id)
		series = []
		temp_dict = {}
		for line in obj.plan_generated_line:
			temp = {
				'from': self._unix_time_millis(line.date_plan, 0), 
				'to': self._unix_time_millis(line.date_plan, line.work_time),
				'equipment_name': line.car_id.name,
				'info': u'<b>Гүйлт: '+str(line.pm_odometer)+u', Зогсох цаг: '+str(line.work_time)+'</b>',
			}
			if line.name not in temp_dict:
				temp_dict[ line.name ] = [temp]
			else:
				temp_dict[ line.name ].append(temp)
		
		for key in temp_dict:
			temp = {
				'name': key,
				'intervals': temp_dict[key],
			}
			series.append(temp)
		if series:
			datas['timeline_data'] = series
		else:
			datas['timeline_data'] = False
		return datas

	# Pivot оор харах
	def see_expenses_view(self):
		if self.plan_generated_line:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		
			search_res = mod_obj.get_object_reference('mw_motors', 'car_forecast_pivot_report_search')
			search_id = search_res and search_res[1] or False
			pivot_res = mod_obj.get_object_reference('mw_motors', 'car_forecast_pivot_report_pivot')
			pivot_id = pivot_res and pivot_res[1] or False

			return {
				'name': self.name,
				'view_mode': 'pivot',
				'res_model': 'car.forecast.pivot.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('g_id','=',self.id)],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

	def export_report(self):
		# GET datas
		query = """
			SELECT 
				tt.report_order as report_order,
				tt.equipment_type as equipment_type,
				tt.equipment_name as equipment_name,
				tt.car_id as car_id,
				tt.dddd as dddd,
				array_agg(tt.description) as description,
				min(tt.mtt_id) as mtt_id,
				sum(tt.work_time) as work_time
			FROM (
				SELECT 
					t.report_order as report_order,
					'left' as equipment_type,
					t.name as equipment_name,
					t.id as car_id,
					to_char(plan.date_plan,'YYYY/MM') as dddd,
					plan.description as description,
					plan.maintenance_type_id as mtt_id,
					plan.work_time as work_time
				FROM car_forecast_generator_line as plan
				LEFT JOIN motors_car as t on (t.id = plan.car_id)
				WHERE 
					  plan.parent_id = %d and 
					  plan.date_plan >= '%s' and 
					  plan.date_plan <= '%s'

				UNION ALL
				
				SELECT 
					t.report_order as report_order,
					'left' as equipment_type,
					t.name as equipment_name,
					t.id as car_id,
					null as dddd,
					'' as description,
					null as mtt_id,
					0 as work_time
				FROM car_forecast_setting_line as tsl
				LEFT JOIN motors_car as t on (t.id = tsl.car_id)
				WHERE 
					  tsl.parent_id = %d 
			) as tt
			GROUP BY tt.report_order, tt.equipment_type, tt.equipment_name, tt.car_id, tt.dddd
			ORDER BY tt.report_order, tt.equipment_type, tt.equipment_name, tt.dddd
		""" % (self.id, self.date_start, self.date_end, self.id)
		self.env.cr.execute(query)
		# print '======', query
		plans = self.env.cr.dictfetchall()
		# GET dates
		query_dates = """
			SELECT to_char(generate_series('%s', '%s', '1 month'::interval)::date,'YYYY/MM') as dddd
		""" % (self.date_start, self.date_end)
		self.env.cr.execute(query_dates)
		dates_result = self.env.cr.dictfetchall()

		if plans:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Forecast report.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_font_size(10)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#E9A227')

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(10)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			header_date = workbook.add_format({'bold': 1})
			header_date.set_text_wrap()
			header_date.set_font_size(7)
			header_date.set_align('center')
			header_date.set_align('vcenter')
			header_date.set_border(style=1)
			header_date.set_bg_color('#E9A227')

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(10)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#FABC51')

			grand_total = workbook.add_format({'bold': 1})
			grand_total.set_text_wrap()
			grand_total.set_font_size(10)
			grand_total.set_align('center')
			grand_total.set_align('vcenter')
			grand_total.set_border(style=1)
			grand_total.set_bg_color('#E49000')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(10)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right0 = workbook.add_format({'italic':1})
			contest_right0.set_text_wrap()
			contest_right0.set_font_size(10)
			contest_right0.set_align('right')
			contest_right0.set_align('vcenter')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(10)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(10)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			# PM ийн өнгө авах
			color_styles = {}
			for mtt in self.env['motors.maintenance.type'].search([]):
				contest_time = workbook.add_format()
				contest_time.set_text_wrap()
				contest_time.set_font_size(10)
				contest_time.set_align('center')
				contest_time.set_align('vcenter')
				contest_time.set_border(style=1)
				contest_time.set_bg_color(mtt.color)
				color_styles[mtt.id] = [mtt.name, contest_time]

			# Борлуулагчаар харуулах sheet
			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.set_zoom(65)
			worksheet.write(0,2, self.name, h1)

			# TABLE HEADER
			row = 1
			worksheet.merge_range(row, 0, row+1, 0, u"№", header)
			worksheet.set_row(2, 20)
			worksheet.set_column(0, 0, 5)
			worksheet.set_column(1, 1, 4)
			worksheet.merge_range(row, 1, row+1, 2, u"Техникийн модел", header_wrap)
			worksheet.set_column(2, 2, 25)
			worksheet.merge_range(row, 3, row+1, 3, u"Парк дугаар", header_wrap)
			worksheet.set_column(3, 3, 10)
			# Сарын өдрүүд зурах
			start_date = self.date_start
			end_date = self.date_end
			col = 4
			col_dict = {}
			for ll in dates_result:
				worksheet.write(row+1, col, ll['dddd'], header_wrap)
				col_dict[ll['dddd']] = col
				col += 1
			worksheet.set_column(4, col-1, 8)
			
			worksheet.merge_range(row, 4, row, col-1, self.date_start.strftime("%Y-%m-%d")+u" -> "+ self.date_end.strftime("%Y-%m-%d"), header_date)
			days = (end_date-start_date).days
			# --------------
			worksheet.merge_range(row, col, row+1, col, u"Хийгдэх ажил", header_wrap)
			worksheet.set_column(col, col, 25)
			worksheet.merge_range(row, col+1, row+1, col+1, u"Ажиллавал зохих цаг", header_wrap)
			worksheet.merge_range(row, col+2, row+1, col+2, u"Т/З/Ц", header_wrap)
			worksheet.merge_range(row, col+3, row+1, col+3, u"ТББК", header_wrap)
			worksheet.freeze_panes(3, 4)
			
			row = 3
			number = 1
			type_dict = {}
			equipment_dict = {}
			descriptions = ''
			type_name = ''
			row_start = 3
			first = True
			total_font_time = 0
			total_repair_time = 0

			sub_totals_address = {
				1:[],2:[],3:[]
			}

			descriptions_dict = {}

			for line in plans:
				if not first and type_name != line['equipment_type']:
					worksheet.merge_range(row, 0, row, col, u'НИЙТ: '+type_name, sub_total)
					type_dict[type_name] = [row_start, row]
					row += 1
					row_start = row

				if line['equipment_name'] not in equipment_dict:
					equipment_dict[line['equipment_name']] = row
					# DATA
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 2, line['equipment_name'], contest_left)
					worksheet.write(row, 3, '', contest_left)
					equipment = self.env['motors.car'].browse(line['car_id'])
					
					norm = equipment.car_setting_id.work_time_per_month or 1
					worksheet.write(row, col+1, days*norm, contest_center)
					worksheet.write_formula(row, col+2, 
						'{=SUM('+self._symbol(row,4) +':'+ self._symbol(row, col)+')}', contest_center)
					worksheet.write_formula(row, col+3, 
						'{=ROUND(100-('+self._symbol(row,col+2) +'*100/'+ self._symbol(row, col+1)+'),2)}', contest_center)
					sub_totals_address[3].append(self._symbol(row,col+3))
					
					number += 1
					row += 1

				rr = equipment_dict[line['equipment_name']]
				if line['dddd'] in col_dict:
					cc = col_dict[line['dddd']]
					# TIME COLOR
					tmp_style = False
					if line['mtt_id']:
						tmp_style = color_styles[line['mtt_id']][1]
					worksheet.write(rr, cc, line['work_time'], tmp_style)
				
				# Тайлбар
				if line['description']:
					txt = ','.join(line['description'])
					if rr in descriptions_dict:
						descriptions_dict[rr] += ', '+txt
					else:
						descriptions_dict[rr] = txt

				first = False
				type_name = line['equipment_type']

			# Last Subtotal
			worksheet.merge_range(row, 0, row, col, u'НИЙТ: '+type_name, sub_total)
			type_dict[type_name] = [row_start, row]
			row += 1
			# Нийт тайлбар зурах
			for key in descriptions_dict:
				worksheet.write(key, col, descriptions_dict[key], contest_left)

			# Sub total
			row_start = 3
			for key in type_dict:
				rr = type_dict[key][1]
				row_start = type_dict[key][0]
				worksheet.write_formula(rr, col+1, 
					'{=SUM('+self._symbol(row_start,col+1) +':'+ self._symbol(rr-1, col+1)+')}', sub_total)
				worksheet.write_formula(rr, col+2, 
					'{=SUM('+self._symbol(row_start,col+2) +':'+ self._symbol(rr-1, col+2)+')}', sub_total)
				worksheet.write_formula(rr, col+3, 
					'{=AVERAGE('+self._symbol(row_start,col+3) +':'+ self._symbol(rr-1, col+3)+')}', sub_total)
				row_start = rr+1

				sub_totals_address[1].append(self._symbol(rr,col+1))
				sub_totals_address[2].append(self._symbol(rr,col+2))

			# Grand total
			worksheet.merge_range(row, 0, row, col, u'Нийт ТББК:', grand_total)
			worksheet.write_formula(row, col+1,'{=IFERROR('+ '+'.join(sub_totals_address[1]) +',0)}', grand_total)
			worksheet.write_formula(row, col+2,'{=IFERROR('+ '+'.join(sub_totals_address[2]) +',0)}', grand_total)
			ttbbk = '{=IFERROR(ROUND(('+ '+'.join(sub_totals_address[3]) +')/%d,2),0)}' % len(sub_totals_address[3])
			worksheet.write_formula(row, col+3, ttbbk, grand_total)
			row += 1
			
			# PM colors DESC
			row += 1
			for key in color_styles:
				worksheet.write(row, 2, color_styles[key][0], contest_right0)
				worksheet.write(row, 3, '', color_styles[key][1])
				row += 1

			# =============================
			workbook.close()
			out = base64.encodestring(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})


			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!')) 

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol

class CarForecastGeneratorLine(models.Model):
	_name = 'car.forecast.generator.line'
	_description = 'Car Forecast Generator line'
	_order = 'date_plan, maintenance_type_id'

	@api.depends('maintenance_type_id')
	def _set_name(self):
		for obj in self:
			obj.name = str(obj.maintenance_type_id.name)
		return True

	# Columns
	parent_id = fields.Many2one('car.forecast.generator', string=u'Parent generator', ondelete='cascade')
	name = fields.Char(compute='_set_name',string=u'Нэр', readonly=True, store=True)

	maintenance_type_id = fields.Many2one('motors.maintenance.type', string=u'Maintenance type', required=True,)
	date_plan = fields.Date(u'Огноо', copy=False, required=True,)

	car_id = fields.Many2one('motors.car', string='Тээврийн хэрэгсэл', readonly=True, required=True,)
	pm_odometer = fields.Float(string=u'Хийгдэх гүйлт', required=True,)
	pm_priority = fields.Integer(string=u'PM дугаар', readonly=True, default=0)
	
	work_time = fields.Float(string=u'Засварын цаг', )
	man_hours = fields.Float(string=u'Хүн цаг', copy=False, readonly=True, )
	description = fields.Char(string='Тайлбар', )

	ro_id = fields.Many2one('car.repair.order', string=u'REF plan', readonly=True, )

	# Нийт зардал
	@api.depends('pm_material_line')
	def _methods_compute(self):
		for obj in self:
			obj.total_amount = sum(obj.pm_material_line.mapped('amount'))
	total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн', digits=(16,1))
	pm_material_line = fields.One2many('car.pm.material.line', 'generator_id', string='Material lines', )

	# ============ Override ===============

	# ============ Custom =================
	def create_plan(self):
		for obj in self:
			# Сарынx бол төлөвлөгөө үүсгэхгүй
			if obj.parent_id.forecast_type != 'weekly':
				return
			# Material data
			material_datas = []
			for m_line in obj.pm_material_line:
				temp = (0,0,{
					'product_id': m_line.material_id.id,
					'price_unit': m_line.material_id.standard_price,
					'qty': m_line.qty,
					'is_pm_material': True,
					'warehouse_id': m_line.warehouse_id.id,
				})
				material_datas.append(temp)

			# Өдрийн ПЛАН үүсгэх
			vals = {
				'origin': 'Generated: '+obj.parent_id.name,
				'maintenance_type_id': obj.maintenance_type_id.id,
				'pm_priority': obj.pm_priority,
				'maintenance_type': 'pm_service',
				'contractor_type': 'internal',
				'generator_line_id': obj.id,
				'date_required': obj.date_plan,
				'car_id': obj.car_id.id,
				'start_odometer': obj.pm_odometer,
				'work_time': obj.work_time,
				'description': obj.name,
				'required_material_line': material_datas,
			}
			plan = self.env['car.repair.order'].create(vals)
			plan.action_to_confirm()
			obj.ro_id = plan.id
			obj.description = 'Plans: '+ str(plan.id)

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, months):
		add = 30*months
		return temp_date + timedelta(days=add)

class CarForecastSeetingLine(models.Model):
	_name = 'car.forecast.setting.line'
	_description = 'Car forecast setting line'
	_order = 'car_id'

	@api.depends('maintenance_type_id')
	def _set_name(self):
		for obj in self:
			obj.name = str(obj.maintenance_type_id.name)
		return True

	# Columns
	parent_id = fields.Many2one('car.forecast.generator', string=u'Parent generator', ondelete='cascade')

	car_id = fields.Many2one('motors.car', string=u'Тээврийн хэрэгсэл', required=True,)
	car_setting_id = fields.Many2one(related='car_id.car_setting_id', 
		string=u'Техникийн тохиргоо', readonly=True, )
	start_odometer = fields.Float(string=u'Эхлэх гүйлт', required=True,)
	work_time_per_month = fields.Float(string=u'Сард ажиллах цаг', )

	last_date = fields.Date(string=u'Хийгдсэн огноо', )
	last_pm_priority = fields.Integer(string=u'PM дугаар', default=0)
	maintenance_type_id = fields.Many2one('motors.maintenance.type', string=u'PM нэр', readonly=True, )
	description = fields.Text(string=u'Тайлбар', readonly=True, )

	start_date = fields.Date(string=u'Ажиллах эхлэх', )

	@api.onchange('car_id')
	def onchange_car_id(self):
		if self.car_id.car_setting_id:
			self.work_time_per_month = self.car_id.car_setting_id.work_time_per_month

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, months):
		add = 30*months
		return temp_date + timedelta(days=add)

	# Зөвхөн 1 техникийн Forecast үүсгэх
	def create_one_forecast(self):
		# Өмнөх мөрийг устгах
		self.env['car.forecast.generator.line'].search([
			('parent_id','=',self.parent_id.id),
			('car_id','=',self.car_id.id)]).unlink()

		# Шинээр техникийн план үүсгэх
		last_odometer = self.start_odometer
		last_pm_priority = self.car_id.last_pm_priority
		work_time_per_month = self.work_time_per_month

		if work_time_per_month == 0:
				raise UserError(_(u'Сард ажиллах цаг 0 байна! %s %d' % (self.car_id.car_setting_id.name, equipment.car_setting_id.id)))

		if not self.car_id.car_setting_id.pm_material_config:
			raise UserError(_(u'PM үйлчилгээний тохиргоо хийгдээгүй байна!'))
		
		pm_line_ids = [0]
		for pm_line in self.car_id.car_setting_id.pm_material_config:
			pm_line_ids.append(pm_line.id)

		# Сүүлд хийгдсэн PM дугаар авна
		idx = last_pm_priority
		# Сүүлд хийгдсэн PM огноо байвал авна, үгүй бол эхлэх огноог авна
		first = True
		temp_date = datetime.now().date()
		if self.parent_id.forecast_type == 'year':
			if self.parent_id.start_last_info:
				temp_date = self.last_date
				last_odometer = self.start_odometer
			else:
				temp_date = self.parent_id.date_start
		# Дуусах огноо хүртэл давтана
		while temp_date < self.parent_id.date_end:
			# Next PM олох
			if idx+1 < len(pm_line_ids):
				idx += 1
			else:
				idx = 1

			# Дараагийн PM авах
			pm_config = self.env['car.pm.material.config'].browse(pm_line_ids[idx])
			interval = pm_config.interval
			if interval <= 0:
				raise UserError(_(u'Interval-ийг тохируулна уу! %s' % pm_config.name))

			# INTERVAL-ийг өдөр лүү хөрвүүлнэ
			days = round(interval / work_time_per_month)
			_logger.info("---generate ======%s %s %d %d %d",self.car_id.name, temp_date, last_odometer, self.car_id._get_odometer(), interval)
			# Зөв эхлэлийг олох
			# Хэрэв хийгдэх гүйлт нь болоогүй бол хойшлуулна
			if first:
				current_mh = self.car_id._get_odometer()
				diff = (last_odometer+interval) - current_mh 
				back_day = round(diff / work_time_per_month)
				if back_day >= 1  and diff > 0:
					temp_date = self._date_increase(temp_date,back_day)
				first = False
			_logger.info("---generate 2=====%s %d %d %d %d",temp_date, (last_odometer+interval), diff, back_day, days)

			# Өнгөрсөн бол давталтаас гарах
			if temp_date >= self.parent_id.date_end:
				break
			
			last_odometer += interval
			# Материалын дата бэлдэх
			material_datas = []
			for m_line in pm_config.pm_material_line:
				temp = (0,0,{
					'material_id': m_line.material_id.id,
					'price_unit': m_line.price_unit,
					'qty': m_line.qty,
				})
				material_datas.append(temp)

			# Forecast үүсгэх
			vals = {
				'parent_id': self.parent_id.id,
				'maintenance_type_id': pm_config.maintenance_type_id.id,
				'pm_priority': idx,
				'date_plan': temp_date,
				'car_id': self.car_id.id,
				'pm_odometer': last_odometer,
				'work_time': pm_config.work_time,
				'pm_material_line': material_datas,
				'description': pm_config.maintenance_type_id.name,
			}
			line = self.env['car.forecast.generator.line'].create(vals)
			# ++
			temp_date = self._date_increase(temp_date,days)
			_logger.info("--=========-added date %s \n",temp_date)
