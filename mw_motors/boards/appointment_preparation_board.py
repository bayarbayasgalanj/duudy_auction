# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import calendar
import pytz
from datetime import datetime, time
import logging
_logger = logging.getLogger(__name__)

class AppointmentPreparationBoard(models.TransientModel):
	_name = 'appointment.preparation.board'
	_description = 'Appointment Preparation Board'

	# Columns
	branch_id = fields.Many2one('res.branch', string='Салбар', )
	date_required = fields.Date(string='Ажилласан өдөр', default=fields.Date.context_today, required=True,)

	# ДАТА татах -----------------------------------------------
	def get_timetable_datas(self, dddd, context=None):
		datas = {}
		print('=------get_timetable_datas--', dddd)
		# Өнөөдөр хийгдэх ажлуудыг бэлдэх
		ros = self._get_repair_orders_2()
		datas['all_repair_orders'] = ros

		# 3-days
		ros = self.env['car.repair.order'].search([
			('days_state','=','3days'),
			('state','!=','draft')])
		if ros:
			ro_data = []
			for ro in ros:
				temp = {
					'id': ro.id,
					'name': ro.name,
					'state_number': ro.car_id.state_number,
					'customer_name': ro.customer_id.name,
					'car_model': ro.car_model_id.name,
					'phone': ro.customer_phone,
					'spend_time': ro.spend_time,
					'color_class': self._get_ro_color_class(ro.maintenance_type, ro.is_warning),
				}
				ro_data.append(temp)
			datas['days3_repair_orders'] = ro_data
		# 2-days
		ros = self.env['car.repair.order'].search([
			('days_state','=','2days'),
			('state','!=','draft')])
		if ros:
			ro_data = []
			for ro in ros:
				temp = {
					'id': ro.id,
					'name': ro.name,
					'state_number': ro.car_id.state_number,
					'customer_name': ro.customer_id.name,
					'car_model': ro.car_model_id.name,
					'phone': ro.customer_phone,
					'spend_time': ro.spend_time,
					'color_class': self._get_ro_color_class(ro.maintenance_type, ro.is_warning),
				}
				ro_data.append(temp)
			datas['days2_repair_orders'] = ro_data
		# 1-days
		ros = self.env['car.repair.order'].search([
			('days_state','=','1days'),
			('state','!=','draft')])
		if ros:
			ro_data = []
			for ro in ros:
				temp = {
					'id': ro.id,
					'name': ro.name,
					'state_number': ro.car_id.state_number,
					'customer_name': ro.customer_id.name,
					'car_model': ro.car_model_id.name,
					'phone': ro.customer_phone,
					'spend_time': ro.spend_time,
					'color_class': self._get_ro_color_class(ro.maintenance_type, ro.is_warning),
				}
				ro_data.append(temp)
			datas['days1_repair_orders'] = ro_data
		# Ordered parts
		ros = self.env['car.repair.order'].search([
			('is_ordered','=',True),
			('state','!=','draft')])
		if ros:
			ro_data = []
			for ro in ros:
				temp = {
					'id': ro.id,
					'name': ro.name,
					'state_number': ro.car_id.state_number,
					'customer_name': ro.customer_id.name,
					'car_model': ro.car_model_id.name,
					'phone': ro.customer_phone,
					'spend_time': ro.spend_time,
					'color_class': self._get_ro_color_class(ro.maintenance_type, ro.is_warning),
				}
				ro_data.append(temp)
			datas['ordered_repair_orders'] = ro_data
		# Delivered parts
		ros = self.env['car.repair.order'].search([
			('is_ordered','=',True),
			('state','!=','draft')])
		if ros:
			ro_data = []
			for ro in ros:
				temp = {
					'id': ro.id,
					'name': ro.name,
					'state_number': ro.car_id.state_number,
					'customer_name': ro.customer_id.name,
					'car_model': ro.car_model_id.name,
					'phone': ro.customer_phone,
					'spend_time': ro.spend_time,
					'color_class': self._get_ro_color_class(ro.maintenance_type, ro.is_warning),
				}
				ro_data.append(temp)
			datas['delivered_repair_orders'] = ro_data
			# Today
			datas['today_repair_orders'] = self._get_repair_orders(dddd)
		
		datas['today_psfu'] = self._get_psfu(dddd)
		return datas

	def _get_psfu(self, dddd):
		ros = self.env['car.repair.order'].search([
			# ('state','=','open'),
			# ('scheduled_date','=',dddd),
			('state','=','psfu'),
			], order='stall_id, scheduled_time, name')
		data = []
		for ro in ros:
			is_warning = ro.is_warning
			try:
				dddd = datetime.strptime(dddd, '%Y-%m-%d')
			except:
				dddd = datetime.now()
			
			if ro.date_psfu_plan and ro.date_psfu_plan<dddd:
				is_warning = True
			temp = {
				'id': ro.id,
				'name': ro.name,
				'description': 'Цаг: %s, Ажил: %s' % ('{0:02.0f}:{1:02.0f}'.format(*divmod(ro.scheduled_time * 60, 60)), ro.job_details),
				'color_class': self._get_ro_color_class(ro.maintenance_type, is_warning) +' warning_ro ' if is_warning else '',
			}
			data.append(temp)
		return data

	# Get Cabinet
	def _get_repair_orders_2(self):
		ros = self.env['car.repair.order'].search([
			('days_state','=','normal'),
			('state','in',['draft','open'])], order='stall_id, scheduled_time, name')
		data = []
		for ro in ros:
			temp = {
				'id': ro.id,
				'name': ro.name,
				'description': 'Өдөр/цаг: %s %s, Ажил: %s' % (ro.scheduled_date.strftime("%m/%d"),'{0:02.0f}:{1:02.0f}'.format(*divmod(ro.scheduled_time * 60, 60)), ro.job_details),
				'color_class': self._get_ro_color_class(ro.maintenance_type, ro.is_warning),
			}
			data.append(temp)
		return data

	def _get_repair_orders(self, dddd):
		ros = self.env['car.repair.order'].search([
			# ('state','=','open'),
			('scheduled_date','=',dddd)], order='stall_id, scheduled_time, name')
		data = []
		for ro in ros:
			temp = {
				'id': ro.id,
				'name': ro.name,
				'description': 'Цаг: %s, Ажил: %s' % ('{0:02.0f}:{1:02.0f}'.format(*divmod(ro.scheduled_time * 60, 60)), ro.job_details),
				'color_class': self._get_ro_color_class(ro.maintenance_type, ro.is_warning),
			}
			data.append(temp)
		return data

	def _get_ro_color_class(self, maintenance_type, warning):
		csss = ""
		if warning:
			csss = 'warning_ro'
		if maintenance_type == 'express_maintenance':
			csss += ' ro_express_maintenance_color repair_order_card cell_clickable'
		elif maintenance_type == 'general_repair':
			csss += ' ro_general_repair_color repair_order_card cell_clickable'
		elif maintenance_type == 'body_and_paint':
			csss += ' ro_body_and_paint_color repair_order_card cell_clickable'
		elif maintenance_type == 'tuning_and_upgrade':
			csss += ' ro_tuning_and_upgrade_color repair_order_card cell_clickable'
		elif maintenance_type == 'diagnostic':
			return 'ro_diagnosis_color repair_order_card cell_clickable'
		else:
			csss += ' ro_general_repair_color repair_order_card cell_clickable'
		return csss