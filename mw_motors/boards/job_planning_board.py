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

class JobPlanningBoard(models.TransientModel):
	_name = 'job.planning.board'
	_description = 'Job Planning Board'

	# Columns
	branch_id = fields.Many2one('res.branch', string='Салбар', )
	date_required = fields.Date(string='Ажилласан өдөр', default=fields.Date.context_today, required=True,)

	# Өгсөн цаг дээр RO байгаа эсэхийг шалгах
	def _check_repair_order(self, line_type, dddd, start_time, stall_id):
		gaps = 4
		domains = [
		  # ('state','=','open'),
			('stall_id','=',stall_id),
			('scheduled_date','=',dddd),
			('scheduled_time','>=',start_time),
			('scheduled_time','<',start_time+1)]
		if line_type == 'performance':
			domains = [
			  # ('state','=','open'),
				('stall_id','=',stall_id),
				('performance_date_start','=',dddd),
				('performance_start_time','>=',start_time),
				('performance_start_time','<',start_time+1)]

		ro = self.env['car.repair.order'].search(domains, limit=1)
		if ro:
			scheduled_time = ro.scheduled_time if line_type=='plan' else ro.performance_start_time
			spend_time = ro.spend_time if line_type=='plan' else ro.performance_spend_time
			info = {
				'id': ro.id,
				'name': ro.name,
				'state_number': ro.car_id.state_number,
				'customer_name': ro.customer_id.name,
				'car_model': ro.car_model_id.name,
				'phone': ro.customer_phone,
				'spend_time': spend_time,
				'start_cell_number': self._get_start_cell_number(scheduled_time),
			}
			gaps = self._compute_gaps(spend_time)
			return gaps, info
		else:
			return gaps, False

	def _get_start_cell_number(self, scheduled_time):
		gaps = ((scheduled_time%1)//0.25)+1
		if gaps > 0:
			return int(gaps)
		else:
			return 1
	# Зарцуулах цагаас gaps-ийг олох
	def _compute_gaps(self, spend_time):
		if spend_time//0.25 > 0:
			return int(spend_time//0.25)
		else:
			return 4

	# ДАТА татах -----------------------------------------------
	def get_timetable_datas(self, dddd, context=None):
		datas = {}
		dddd = datetime.strptime(dddd, '%Y-%m-%d')
		dddd = dddd.date()
		day_name = dddd.strftime("%A").lower()
		print('=------get_timetable_datas--', dddd, day_name)
		# Эхлэх, дуусах цагийг зурах ============================
		settings = self.env['motors.stall.order.setting']._get_min_max_dates(dddd)
		times = []
		start_time = int(settings['min'])
		end_time = int(settings['max'])
		for tt in range(start_time, end_time+1):
			times.append('{0:02.0f}:{1:02.0f}'.format(*divmod(tt * 60, 60)))
		datas['times'] = times
		# =======================================================
		# Цагийн хүснэгт зурах
		lines = self.env['motors.stall.order.setting']._get_timetable_lines(dddd)
		cells_limit = (end_time-start_time+1)*4
		datas['cells_limit'] = cells_limit
		
		# Төлөвлөсөн LINES татах ============================================
		line_datas = []
		for ll in lines:
			cells = []
			total_work_time = end_time-start_time+1
			total_ordered_time = 0
			start_idx = 1
			end_idx = 4
			temp_idx = 0
			print('=========== STALL', ll.stall_id.name)
			for st in range(start_time, end_time+1):
				gaps, ro_info = self._check_repair_order('plan',dddd, st, ll.stall_id.id)
				# Ordered cell =========================
				if ro_info:
					cell = {}
					# Сул cell бөглөх
					if ro_info['start_cell_number'] > 1:
						merge = ro_info['start_cell_number']-1
						cells.append({'state':'empty', 'value_colspan': merge})
						temp_idx = merge 
					cell['ro_id'] = ro_info['id']
					cell['ro_name'] = ro_info['name']
					cell['state_number'] = ro_info['state_number']
					cell['description'] = ro_info['customer_name']+', '+ro_info['car_model']
					cell['state'] = 'ordered'
					cell['value_colspan'] = gaps
					end_idx += 1
					cells.append(cell)
					total_ordered_time += 1
					# Сул cell бөглөх
					start_idx += ro_info['start_cell_number']+gaps
					if start_idx <= end_idx:
						merge = end_idx-start_idx
						cells.append({'state':'empty', 'value_colspan': merge+1}) 
						start_idx += merge
						
				# Blank cell =============================
				elif ll._is_blank(day_name, st):
					total_work_time -= 1
					# Сул cell бөглөх
					cells.append({'state':'blank', 'value_colspan': end_idx+1-start_idx })
					start_idx = end_idx+1
					
				# Empty cell ===========================
				else:
					# Сул cell бөглөх
					if start_idx <= end_idx:
						cells.append({'state':'empty', 'value_colspan': end_idx+1-start_idx })
						start_idx = end_idx+1
					
				# Урт үргэлжилсэн бол дараагийн цаг руу орох
				if gaps < 4:
					end_idx += 4-temp_idx
				else:
					end_idx += 4
				if gaps//4 > 1:
					st += gaps//4-1
				temp_idx = 0

			stall_description = ""
			total_available_time = total_work_time - total_ordered_time
			total_work_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(total_work_time * 60, 60))
			total_ordered_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(total_ordered_time * 60, 60))
			total_available_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(total_available_time * 60, 60))
			temp = {
				'line_id': ll.id,
				'is_show': 'show',
				'line_name': ll.name,
				'description': stall_description,
				'total_time': total_work_time,
				'total_ordered_time': total_ordered_time,
				'total_available_time': total_available_time,
				'cells': cells,
			}
			line_datas.append(temp)
		
		# Гүйцэтгэлийн LINES татах ================================================
		line_datas_2 = []
		for ll in lines:
			cells = []
			total_work_time = end_time-start_time+1
			total_ordered_time = 0
			start_idx = 1
			end_idx = 4
			temp_idx = 0
			print('=========== STALL', ll.stall_id.name)
			for st in range(start_time, end_time+1):
				gaps, ro_info = self._check_repair_order('performance',dddd, st, ll.stall_id.id)
				# Ordered cell =========================
				if ro_info:
					cell = {}
					# Сул cell бөглөх
					if ro_info['start_cell_number'] > 1:
						merge = ro_info['start_cell_number']-1
						cells.append({'state':'empty', 'value_colspan': merge})
						temp_idx = merge 
					cell['ro_id'] = ro_info['id']
					cell['ro_name'] = ro_info['name']
					cell['state_number'] = ro_info['state_number']
					cell['description'] = ro_info['customer_name']+', '+ro_info['car_model']
					cell['state'] = 'ordered'
					cell['value_colspan'] = gaps
					end_idx += 1
					cells.append(cell)
					total_ordered_time += 1
					# Сул cell бөглөх
					start_idx += ro_info['start_cell_number']+gaps
					if start_idx <= end_idx:
						merge = end_idx-start_idx
						cells.append({'state':'empty', 'value_colspan': merge+1}) 
						start_idx += merge
						
				# Blank cell =============================
				elif ll._is_blank(day_name, st):
					total_work_time -= 1
					# Сул cell бөглөх
					cells.append({'state':'blank', 'value_colspan': end_idx+1-start_idx })
					start_idx = end_idx+1
					
				# Empty cell ===========================
				else:
					# Сул cell бөглөх
					if start_idx <= end_idx:
						cells.append({'state':'empty', 'value_colspan': end_idx+1-start_idx })
						start_idx = end_idx+1
					
				# Урт үргэлжилсэн бол дараагийн цаг руу орох
				if gaps < 4:
					end_idx += 4-temp_idx
				else:
					end_idx += 4
				if gaps//4 > 1:
					st += gaps//4-1
				temp_idx = 0

			stall_description = ""
			total_available_time = total_work_time - total_ordered_time
			total_work_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(total_work_time * 60, 60))
			total_ordered_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(total_ordered_time * 60, 60))
			total_available_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(total_available_time * 60, 60))
			temp = {
				'line_id': ll.id,
				'is_show': 'hide',
				'line_name': ll.name,
				'description': stall_description,
				'total_time': total_work_time,
				'total_ordered_time': total_ordered_time,
				'total_available_time': total_available_time,
				'cells': cells,
			}
			line_datas_2.append(temp)
		
		all_line_datas = []
		for i in range(0,len(line_datas)):
			all_line_datas.append(line_datas[i])
			all_line_datas.append(line_datas_2[i])
		datas['timetable_lines'] = all_line_datas

		# Өнөөдөр хийгдэх ажлуудыг бэлдэх ======================================
		ros = self._get_repair_orders(dddd)
		datas['all_repair_orders'] = ros

		return datas

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
			}
			data.append(temp)
		return data