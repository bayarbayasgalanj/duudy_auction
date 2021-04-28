# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections
import calendar
import pytz

import logging
_logger = logging.getLogger(__name__)

class JobProgressContralBoard(models.TransientModel):
	_name = 'job.progress.contral.board'
	_description = 'Job Progress Contral Board'

	# Columns
	branch_id = fields.Many2one('res.branch', string='Салбар', )
	date_required = fields.Date(string='Ажилласан өдөр', default=fields.Date.context_today, required=True,)

	# ДАТА татах -----------------------------------------------
	def get_timetable_datas(self, dddd, context=None):
		datas = {}
		print('=------get_timetable_datas--', dddd)
		# Waiting for Service ==================================
		ros = self.env['car.repair.order'].search([
			('state','=','waiting_for_service')])
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
					'color_class': self._get_ro_color_class(ro.maintenance_type),
				}
				ro_data.append(temp)
			datas['waiting_service_ros'] = ro_data
		# Being Serviced ==================================
		ros = self.env['car.repair.order'].search([
			('state','=','being_serviced')])
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
					'color_class': self._get_ro_color_class(ro.maintenance_type),
				}
				ro_data.append(temp)
			datas['being_serviced_ros'] = ro_data
		# Paused ==================================
		ros = self.env['car.repair.order'].search([
			('state','=','paused')])
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
					'color_class': self._get_ro_color_class(ro.maintenance_type),
				}
				ro_data.append(temp)
			datas['paused_ros'] = ro_data
		# Waiting for Inspection ==================================
		ros = self.env['car.repair.order'].search([
			('state','=','waiting_for_inspection')])
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
					'color_class': self._get_ro_color_class(ro.maintenance_type),
				}
				ro_data.append(temp)
			datas['waiting_inspection_ros'] = ro_data
		# Waiting for Washing ==================================
		ros = self.env['car.repair.order'].search([
			('state','=','waiting_for_washing')])
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
					'color_class': self._get_ro_color_class(ro.maintenance_type),
				}
				ro_data.append(temp)
			datas['waiting_washing_ros'] = ro_data
		# Waiting for Invoicing ==================================
		ros = self.env['car.repair.order'].search([
			('state','=','waiting_for_invoicing')])
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
					'color_class': self._get_ro_color_class(ro.maintenance_type),
				}
				ro_data.append(temp)
			datas['waiting_invoicing_ros'] = ro_data
		# Waiting for Delivery ==================================
		ros = self.env['car.repair.order'].search([
			('state','=','waiting_for_delivery')])
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
					'color_class': self._get_ro_color_class(ro.maintenance_type),
				}
				ro_data.append(temp)
			datas['waiting_settlement_ros'] = ro_data

		return datas

	def _get_ro_color_class(self, maintenance_type):
		if maintenance_type == 'express_maintenance':
			return 'ro_express_maintenance_color repair_order_card cell_clickable'
		elif maintenance_type == 'general_repair':
			return 'ro_general_repair_color repair_order_card cell_clickable'
		elif maintenance_type == 'body_and_paint':
			return 'ro_body_and_paint_color repair_order_card cell_clickable'
		elif maintenance_type == 'tuning_and_upgrade':
			return 'ro_tuning_and_upgrade_color repair_order_card cell_clickable'
		elif maintenance_type == 'diagnostic':
			return 'ro_diagnosis_color repair_order_card cell_clickable'
		else:
			return 'ro_general_repair_color repair_order_card cell_clickable'
