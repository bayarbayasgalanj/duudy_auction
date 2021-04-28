# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

# Урьдчилсан төлөвлөгөөний материал
class CarForecastPivotReport(models.Model):
	_name = "car.forecast.pivot.report"
	_description = "Car Forecast Pivot Report"
	_auto = False
	_order = 'product_id'

	g_id = fields.Many2one('car.forecast.generator', string='Generator', readonly=True,  )
	gl_id = fields.Many2one('car.forecast.generator.line', string='Generator line', readonly=True,  )

	date = fields.Date(string=u'Огноо', readonly=True, )
	maintenance_type_id = fields.Many2one('motors.maintenance.type',string=u'Засварын төрөл', readonly=True, )
	car_id = fields.Many2one('motors.car', string=u'Тээврийн хэрэгсэл', readonly=True, )
	work_time = fields.Float(string='Засварын цаг', digits = (16,1), readonly=True, )
	man_hours = fields.Float(string=u'Хүн цаг', copy=False, readonly=True, )
	pm_odometer = fields.Char(string=u'Хийгдэх гүйлт', readonly=True, )
	planner_id = fields.Many2one('res.users', string=u'Төлөвлөгч', readonly=True, )

	product_id = fields.Many2one('product.product', string='Сэлбэг/Материал', readonly=True,  )
	categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True, )
	qty = fields.Float(string=u'Тоо хэмжээ', readonly=True, digits=(16,1))
	price_unit = fields.Float(string=u'Нэгж үнэ', readonly=True, digits=(16,1), operator='avg')
	amount = fields.Float(string=u'Дүн', readonly=True, digits=(16,1), )

	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], readonly=True, string='State')

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT
				pg.id as g_id,
				pgl.id as gl_id,
				pgll.id as id,
				pgl.date_plan as date,
				pgl.maintenance_type_id as maintenance_type_id,
				pgl.car_id as car_id,
				pgl.work_time/(select count(*) from car_forecast_generator_line where generator_id = pgll.generator_id) as work_time,
				pgl.man_hours/(select count(*) from car_forecast_generator_line where generator_id = pgll.generator_id) as man_hours,
				pg.planner_id as planner_id,
				pgl.pm_odometer as pm_odometer,
				pgll.material_id as product_id,
				pgll.categ_id as categ_id,
				pgll.price_unit as price_unit,
				pgll.qty as qty,
				pgll.amount as amount,
				pg.state
			FROM car_pm_material_line as pgll
			LEFT JOIN car_forecast_generator_line as pgl on (pgl.id = pgll.generator_id)
			LEFT JOIN car_forecast_generator as pg on (pg.id = pgl.parent_id)
		)""" % self._table)
