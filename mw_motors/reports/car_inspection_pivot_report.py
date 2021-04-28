# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class CarInspectionPivotReport(models.Model):
	_name = "car.inspection.pivot.report"
	_description = "car_inspection_pivot_report"
	_auto = False
	_order = 'car_id'

	inpection_id = fields.Many2one('car.inspection', 'Inspection', readonly=True,  )
	date_inspection = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	car_id = fields.Many2one('motors.car', string='Машин', readonly=True,  )

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
		('tire','Tire')], string='Ангилал', readonly=True)
	name = fields.Char("Үзлэг", readonly=True, )
	is_check = fields.Selection([
		('no',u'Асуудалтай'),
		('yes',u'Хэвийн')], string=u'Хэвийн эсэх', readonly=True, )

	description = fields.Text(string="Засварын тэмдэглэл", readonly=True, )
	is_important = fields.Selection([
		('no',u'Үгүй'),
		('yes',u'Тийм')], string=u'Чухал үзлэг', readonly=True, )

	user_id = fields.Many2one('res.users', string='Ажилтан', readonly=True,  )
	customer_id = fields.Many2one('res.partner', string=u'Харилцагч', copy=False,  )

	customer_note = fields.Text(string="Харилцагчийн өмнөх тэмдэглэл", readonly=True, )
	maintenance_note = fields.Char("Maintenance's note", readonly=True, )
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				til.id as id,
				ti.id as inpection_id,
				ti.date_inspection as date_inspection,
				ti.car_id as car_id,

				til.category as category,
				item.name as name,
				(CASE WHEN til.is_check='t' THEN 'yes' ELSE 'no' END) as is_check,
				til.description as description,
				(CASE WHEN item.is_important='t' THEN 'yes' ELSE 'no' END) as is_important,
				
				ti.user_id as user_id,
				ti.customer_id as customer_id,
				ti.customer_note as customer_note,
				ti.maintenance_note as maintenance_note
			FROM car_inspection_line as til
			LEFT JOIN car_inspection as ti on (til.parent_id = ti.id)
			LEFT JOIN car_inspection_item as item on item.id = til.item_id
			WHERE ti.state = 'done'
		)""" % self._table)
