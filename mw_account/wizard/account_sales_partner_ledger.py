# -*- encoding: utf-8 -*-
############################################################################################
#
#	Managewall-ERP, Enterprise Management Solution	
#	Copyright (C) 2007-2017 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#	$Id:  $
#
#	Менежволл-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#	Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
#
#
############################################################################################

from datetime import timedelta
from lxml import etree

import base64
import time
import datetime
from datetime import datetime

import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

import time
import datetime
from datetime import timedelta
from lxml import etree

from odoo.tools.translate import _

import xlwt
from xlwt import *
# from odoo.addons.c2c_reporting_tools.c2c_helper import *
from operator import itemgetter
# from odoo.addons.mn_base import report_helper
# logger = netsvc.Logger()
logger = logging.getLogger('odoo')

class account_partner_sales_ledger(models.TransientModel):
	"""
		Өглөгийн дансны товчоо
	"""
	
#	 _inherit = "abstract.report.excel"
	_inherit = "account.common.report"
	_name = "account.partner.sales.ledger"
	_description = "Payable Account Sales Ledger"
	
	CONDITION_SELECTION = [('all', 'All Partner'),('non-balance', 'Non balanced'), ('balance', 'Balanced')]
	
	company_id = fields.Many2one('res.company', 'Company')
#	 account_id = fields.Many2one('account.account', 'Account', domain=[('type','in',['payable','receivable'])])
	account_id = fields.Many2one('account.account', 'Account', domain=[('user_type_id.type','in',['payable','receivable'])])
#	 fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal year', required=True),
#	 filter = fields.Selection([('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True),
#	 period_from = fields.Many2one('account.period', 'Start period'),
#	 period_to = fields.Many2one('account.period', 'End period'),
	date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
	date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))
	target_move = fields.Selection([('all', 'All Entries'),
									('posted', 'All Posted Entries')], 'Target Moves', required=True,default='posted')
	partner_id = fields.Many2one('res.partner', 'Partner', help="If empty, display all partners")
	condition = fields.Selection(CONDITION_SELECTION, 'Condition', required=True,default='all')
	type = fields.Selection([('all', 'All'),('payable', 'Payable'),
									('receivable', 'Receivable')], 'Type',default='receivable')
	is_currency = fields.Boolean('Is currency')
	warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
		
	
	def _build_contexts(self, data):
		result = {}
#		 print "data ",data
		if not data['form']['date_from'] or not data['form']['date_to']:
			raise UserError((u'Эхлэх дуусах огноо сонгоно уу.'))
		elif data['form']['date_from'] > data['form']['date_to']:
			raise UserError((u'Эхлэх огноо дуусах огнооноос бага байх ёстой.'))
			
#		 result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
		result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
		result['date_from'] = data['form']['date_from'] or False
		result['date_to'] = data['form']['date_to'] or False
		result['strict_range'] = True if result['date_from'] else False
#		 data['form'].update(self.read(['chart_account_ids'])[0])
#		 result.update(self.read(['check_balance_method'])[0])
#		 result.update(self.read(['chart_account_ids'])[0])
 
		return result
		
	def prepare_data(self, context=None):
		
		data = {}
		data['form'].update(self._build_contexts(data))
		form = self.read()[0]
#		 data = self.pre_print_report(data)
		data['form']['company_id'] = form['company_id'][0]
#		 data['form']['account_ids'] = data['form']['chart_account_ids']
#		 data['form']['company_type'] = data['form']['company_type']
#		 data['form']['check_balance_method'] = form['check_balance_method']
		
		return data
	
	def print_report(self, context=None):
		if context is None:
			context = {}
		
		data = self.prepare_data()
		
		if context['report_type'] == 'payable' :
			report_name = u'Өглөгийн дансны товчоо'
		elif context['report_type'] == 'receivable' :
			report_name = u'Авлагын дансны товчоо'
		else : # both
			report_name = u'Авлага, өглөгийн дансны товчоо '
		
		context.update({'report_type':'payable'})
		return {
			'type': 'ir.actions.report.xml',
			'report_name': 'account.partner.ledger2',
			'datas': data,
			'context': context,
			'nodestroy': True,
		}
		
	def create_report_data(self, data):
		cr=self._cr
		def characteristic_key(r):
			p = 'none'
			if r['partner_id']:
				p = str(r['partner_id'])
			a = 'none'
			if r['account_id']:
				a = str(r['account_id'])
			f = 'none'
			if r['ref']:
				f = r['ref']
			return (p + ':' + a + ':' + f)
		
		account_obj = self.env['account.account']
		partner_obj = self.pool.get('res.partner')
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		move_line_obj = self.pool.get('account.move.line')
		
		account_where = ""
		if data.get('account_id',False):
			account_where = " AND l.account_id = %s " % data['account_id'][0]
#		 if data['type'] in ['receivable','payable']:
#			 account_where += " AND ac.type = '%s' " % data['type']
#		 else:
#			 account_where += " AND ac.type in ('receivable','payable') "
		partner_where = ""
		if data.get('partner_id', False):
			partner_ids = [data['partner_id'][0]]
			child_ids = self.env['res.partner'].search([('parent_id','=',data['partner_id'][0])])
			if child_ids :
				partner_ids = child_ids
			if data['partner_id'][0] not in partner_ids:
				partner_ids += [data['partner_id'][0]]
			partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
		elif data.get('warehouse_id', False):
			warehouse_id = [data['warehouse_id'][0]]
			partner_ids = self.env['res.partner'].search([('depend_warehouse_id','=',warehouse_id)]).ids
			partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
		

		company_where = ""
		if data.get('company_id', False):
			company_where = " AND l.company_id = %s " % data['company_id'][0]
		
#		 initial_context, initial_bal_journal = self.get_initial_balance_context(cr, uid, data, context=context)
#		 
#		 initial_query = move_line_obj._query_get(cr, uid, obj='l', context=initial_context)
#		 fiscalyear = fiscalyear_obj.browse(cr, uid, data['fiscalyear_id'][0])
#		 if initial_bal_journal :
#			 initial_query += " AND l.journal_id = %s " % initial_bal_journal
#		 elif data['date_from'] == fiscalyear.date_start:
#			 initial_query += " AND l.journal_id = -1 "

#Эхний  
		
#		 where=account_obj.get_initial_balance_partner([],data)
		cr = self.env.cr
		MoveLine = self.env['account.move.line']
#		 move_lines = dict(map(lambda x: (x, []), accounts.ids))
#		 print "data context ",data
		init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
														state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
		init_wheres = [""]
		
		if init_where_clause.strip():
			init_wheres.append(init_where_clause.strip())
		init_filters = " AND ".join(init_wheres)
		filters = init_filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
#		 print 'filters=======: ',filters
#		 print 'where ',where
		initw=filters
		move_state = ['draft','posted']
		if data['target_move'] != 'all':
			move_state = ['posted']
		initial_query=''
#		 fil=filters,tuple(init_where_params)
#		 print 'initial_query ',str(fil)
		report_types = '\'' + data['type'] + '\''
		if data['type'] == 'all':
			report_types = "'receivable','payable'"
		# Тайлант хугацааны эхний үлдэгдлийг тооцоолно
		cr.execute(
			"SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,acct.type AS account_type, "
					"p.name as partner_name, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
					"CASE WHEN l.amount_currency > 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS debit_cur,"
					"CASE WHEN l.amount_currency < 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS credit_cur,"
					"CASE WHEN acct.balance_type = 'active' "
						"THEN sum(debit) - sum(credit) "
						"ELSE SUM(credit) - sum(debit) "
					"END AS ibalance, "
					"acct.balance_type "
			"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
			"JOIN account_account ac ON (l.account_id = ac.id) "
			"JOIN account_move am ON (am.id = l.move_id) "
			"JOIN account_account_type acct ON (acct.id=ac.user_type_id) "
			"WHERE acct.type IN (" + report_types + ") "
			" " + initial_query + " "+ account_where + " "+ partner_where +" "+ company_where+" " + filters + " "
			"GROUP BY p.id, p.ref, p.name,l.account_id,ac.name,ac.code,acct.balance_type, l.currency_id,l.amount_currency, acct.type "
			"ORDER BY ac.name ",tuple(init_where_params))
#		 cr.execute(sql, params)
		res = cr.dictfetchall()
#		 print 'res ',res
		partner_data = {}
		for r in res:
			if r['ibalance'] != 0 :
				key = characteristic_key(r)
				if key not in partner_data:
					partner_data[key] = {
						'partner_id':r['partner_id'],
						'currency_id':r['currency_id'],
						'date':'',
						'partner_ref': r['ref'] or '',
						'name': r['partner_name'] or u'Харилцагчгүй',
						'account_code': r['code'],
						'account': '%s %s' % (r['code'],r['account_name']),
						'account_name': r['account_name'],
						'account_type':r['account_type'],
						'initial_cur': 0,
						'initial': 0,
						'debit_cur': 0,
						'debit': 0,
						'credit_cur': 0,
						'credit': 0,
						'balance_cur': 0,
						'balance': 0,
						'refund_credit':0
					}
				if r['balance_type'] == 'passive':
					partner_data[key]['initial'] += (r['credit'] or 0) - (r['debit'] or 0)
					partner_data[key]['initial_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
				else :
					partner_data[key]['initial'] += (r['debit'] or 0) - (r['credit'] or 0)
					partner_data[key]['initial_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
		
		for key, value in partner_data.items():
			partner_data[key]['balance_cur'] = partner_data[key]['initial_cur']
			partner_data[key]['balance'] = partner_data[key]['initial']
			
#-------------------------------------------------------------------------------
#		 Тайлант хугацааны гүйлгээг тооцоолж эцсийн үлдэгдлийг тодорхойлно
#		 current_context = context.copy()
#		 current_context.update({
#			 'fiscalyear': data['fiscalyear_id'][0],
#			 'date_from': data['date_from'],
#			 'date_to': data['date_to']
#		 })
#		 query = move_line_obj._query_get(cr, uid, obj='l', context=current_context)
#		 if initial_bal_journal:
#			 query += " AND l.journal_id <> %s " % initial_bal_journal

#		 cr = self.env.cr
		MoveLine = self.env['account.move.line']
#		 print 'data.get(,{}) ',data.get('used_context',{})
#		 init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
#														 state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
		tables, where_clause, where_params = MoveLine.with_context(date_from=data['date_from'],
														state=data['target_move'],date_to=data['date_to'],strict_range=True, )._query_get()
		query=''
		wheres = [""]
#		 print 'where_params============================ ',where_params
#		 print 'where_clause---------------------------- ',where_clause
		if where_clause.strip():
			wheres.append(where_clause.strip())
		filters = " AND ".join(wheres)
		filters = filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
		
#		 fil=filters,tuple(init_where_params)
#		 print 'initial_query ',str(fil)
		report_types = '\'' + data['type'] + '\''
		if data['type'] == 'all':
			report_types = "'receivable','payable'"
		cr.execute(
			"SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,acct.type AS account_type, "
					"p.name as partner_name, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
					"CASE WHEN l.amount_currency > 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS debit_cur,"
					"CASE WHEN l.amount_currency < 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS credit_cur,"
					"acct.balance_type, "
					"am.id as move_id "
			"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
			"JOIN account_account ac ON (l.account_id = ac.id) "
			"JOIN account_move am ON (am.id = l.move_id) "
			"JOIN account_account_type acct ON (acct.id=ac.user_type_id) "
			"WHERE acct.type IN (" + report_types + ") "
			" " + query + " "+ account_where + " " + partner_where + " "+ company_where+" " + filters +" "
			"GROUP BY p.id, p.ref, p.name,l.account_id,ac.name,ac.code,acct.balance_type, l.currency_id, l.amount_currency, acct.type, am.id "
			"ORDER BY ac.name ",tuple(where_params))
			#"ORDER BY p.name,l.account_id ")
		 
		res = cr.dictfetchall()
#		 print 'res ',res
		for r in res:
#			 print ('rrrrr ',r)
			if r['debit'] > 0 or r['credit'] > 0 :
				key = characteristic_key(r)
				move = self.env['account.move'].browse(r['move_id'])
#				 print ('move ',move)
				if key not in partner_data:
					partner_data[key] = {
						'partner_id':r['partner_id'],
						'currency_id':r['currency_id'],
						'date':'',
						'partner_ref': r['ref'] or '',
						'name': r['partner_name'] or u'Харилцагчгүй',
						'account': '%s %s' % (r['code'],r['account_name']),
						'account_code': r['code'],
						'account_name': r['account_name'],
						'account_type':r['account_type'],
						'initial_cur': 0,
						'initial': 0,
						'debit_cur': 0,
						'debit': 0,
						'credit_cur': 0,
						'credit': 0,
						'balance': 0,
						'balance_cur': 0,
						'refund_credit':0
					}
				credit=0
				refund_credit=0
				if move.sale_return_id:
					refund_credit=abs(r['credit'])
				else:
					credit = abs(r['credit'])
					
				partner_data[key]['debit_cur'] += (r['debit_cur'] or 0)
				partner_data[key]['debit'] += (r['debit'] or 0)
				partner_data[key]['credit_cur'] += (abs(r['credit_cur']) or 0)
				partner_data[key]['credit'] += credit 
				partner_data[key]['refund_credit'] += refund_credit 
				if r['balance_type'] == 'passive':
					partner_data[key]['balance'] += (r['credit'] or 0) - (r['debit'] or 0)
					partner_data[key]['balance_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
				else :
					partner_data[key]['balance'] += (r['debit'] or 0) - (r['credit'] or 0)
					partner_data[key]['balance_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
#		 print 'partner_data: ', partner_data
		if not data.get('partner_id', False) and data['condition'] != 'all':
			if data['condition'] == 'non-balance':
				for key in partner_data.keys():
					if abs(partner_data[key]['balance']) >= 1:
						del partner_data[key]
			else :
				for key in partner_data.keys():
					if abs(partner_data[key]['balance']) < 1:
						del partner_data[key]
#						 
		#return sorted(partner_data.values(), key=itemgetter('name'))
		return sorted(partner_data.values(), key=itemgetter('account_type'))	

	def create_report_data_account(self, data):
		''' Гүйлгээ баланс тайлангийн мэдээллийг боловсруулж
			тайлангийн форматад тохируулан python [{},{},{}...]
			загвараар хүснэгтийн мөр багануудын өгөгдлийг боловсруулна.
			
		'''
		cr=self._cr
		def characteristic_key(r):
#			 print 'rrrrr ',r
			p = 'none'
			if r['partner_id']:
				p = str(r['partner_id'])
			a = 'none'
			if r['account_id']:
				a = str(r['account_id'])
			f = 'none'
			if r['ref']:
				f = r['ref']
			return (p + ':' + a + ':' + f)
		
		account_obj = self.env['account.account']
		partner_obj = self.pool.get('res.partner')
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		move_line_obj = self.pool.get('account.move.line')
		
		account_where = ""
		if data.get('account_id',False):
			account_where = " AND l.account_id = %s " % data['account_id'][0]
		partner_where = ""
		if data.get('partner_id', False):
			partner_ids = [data['partner_id'][0]]
#			 child_ids = self.env['res.partner'].search([('parent_id','=',data['partner_id'][0])])
#			 if child_ids :
#				 partner_ids = child_ids
			if data['partner_id'][0] not in partner_ids:
				partner_ids += [data['partner_id'][0]]
			partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
		elif data.get('warehouse_id', False):
			warehouse_id = [data['warehouse_id'][0]]
			partner_ids = self.env['res.partner'].search([('depend_warehouse_id','=',warehouse_id)]).ids
			partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "

		company_where = ""
		if data.get('company_id', False):
			company_where = " AND l.company_id = %s " % data['company_id'][0]
		
#Эхний  
		
#		 where=account_obj.get_initial_balance_partner([],data)
		cr = self.env.cr
		MoveLine = self.env['account.move.line']
#		 move_lines = dict(map(lambda x: (x, []), accounts.ids))
#		 print "data context ",data
		init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
														state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
		init_wheres = [""]
		
		if init_where_clause.strip():
			init_wheres.append(init_where_clause.strip())
		init_filters = " AND ".join(init_wheres)
		filters = init_filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
#		 print 'where ',where
		initw=filters
		move_state = ['draft','posted']
		if data['target_move'] != 'all':
			move_state = ['posted']
		initial_query=''
#		 fil=filters,tuple(init_where_params)
#		 print 'initial_query ',str(fil)
		report_types = '\'' + data['type'] + '\''
		if data['type'] == 'all':
			report_types = "'receivable','payable'"
		# Тайлант хугацааны эхний үлдэгдлийг тооцоолно
		cr.execute(
			"SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,acct.type AS account_type, "
					"p.name as partner_name, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
					"CASE WHEN l.amount_currency > 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS debit_cur,"
					"CASE WHEN l.amount_currency < 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS credit_cur,"
					"CASE WHEN acct.balance_type = 'active' "
						"THEN sum(debit) - sum(credit) "
						"ELSE SUM(credit) - sum(debit) "
					"END AS ibalance, "
					"acct.balance_type, "
					"(select category_id from res_partner_res_partner_category_rel where partner_id=p.id limit 1) as category_id "
			"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
			"JOIN account_account ac ON (l.account_id = ac.id) "
			"JOIN account_move am ON (am.id = l.move_id) "
			"JOIN account_account_type acct ON (acct.id=ac.user_type_id) "
			"WHERE acct.type IN (" + report_types + ") "
			" " + initial_query + " "+ account_where + " "+ partner_where +" "+ company_where +" " + filters + " "
			"GROUP BY p.id, p.ref, p.name,l.account_id,ac.name,ac.code,acct.balance_type, l.currency_id,l.amount_currency, acct.type "
			"ORDER BY ac.name ",tuple(init_where_params))
#		 cr.execute(sql, params)
		res = cr.dictfetchall()
#		 print 'res ',res
		partner_data = {}
		for r in res:
			if r['ibalance'] != 0 :
				key = characteristic_key(r)
				if key not in partner_data:
					partner_data[key] = {
						'partner_id':r['partner_id'],
						'currency_id':r['currency_id'],
						'date':'',
						'partner_ref': r['ref'] or '',
						'name': r['partner_name'] or u'Харилцагчгүй',
						'account_code': r['code'],
						'account': '%s %s' % (r['code'],r['account_name']),
						'account_name': r['account_name'],
						'account_type':r['account_type'],
						'initial_cur': 0,
						'initial': 0,
						'debit_cur': 0,
						'debit': 0,
						'credit_cur': 0,
						'credit': 0,
						'balance_cur': 0,
						'balance': 0,
						'category_id':r['category_id'],
					}
				if r['balance_type'] == 'passive':
					partner_data[key]['initial'] += (r['credit'] or 0) - (r['debit'] or 0)
					partner_data[key]['initial_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
				else :
					partner_data[key]['initial'] += (r['debit'] or 0) - (r['credit'] or 0)
					partner_data[key]['initial_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
		
		for key, value in partner_data.items():
			partner_data[key]['balance_cur'] = partner_data[key]['initial_cur']
			partner_data[key]['balance'] = partner_data[key]['initial']
			
#-------------------------------------------------------------------------------
		MoveLine = self.env['account.move.line']
#		 init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
#														 state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
		tables, where_clause, where_params = MoveLine.with_context(date_from=data['date_from'],
														state=data['target_move'],date_to=data['date_to'],strict_range=True, )._query_get()
		query=''
		wheres = [""]
#		 print 'where_params============================ ',where_params
#		 print 'where_clause---------------------------- ',where_clause
		if where_clause.strip():
			wheres.append(where_clause.strip())
		filters = " AND ".join(wheres)
		filters = filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
		
#		 fil=filters,tuple(init_where_params)
#		 print 'initial_query ',str(fil)
		report_types = '\'' + data['type'] + '\''
		if data['type'] == 'all':
			report_types = "'receivable','payable'"
		cr.execute(
			"SELECT p.id as partner_id, p.ref as ref,l.account_id as account_id, ac.name AS account_name,ac.code AS code,acct.type AS account_type, "
					"p.name as partner_name, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
					"CASE WHEN l.amount_currency > 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS debit_cur,"
					"CASE WHEN l.amount_currency < 0 "
						"THEN sum(l.amount_currency) "
						"ELSE 0 "
					"END AS credit_cur,"
					"acct.balance_type, "
					"(select category_id from res_partner_res_partner_category_rel where partner_id=p.id limit 1) as category_id "
			"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
			"JOIN account_account ac ON (l.account_id = ac.id) "
			"JOIN account_move am ON (am.id = l.move_id) "
			"JOIN account_account_type acct ON (acct.id=ac.user_type_id) "
			"WHERE acct.type IN (" + report_types + ") "
			" " + query + " "+ account_where + " " + partner_where + " "+ company_where+ " " + filters +" "
			"GROUP BY p.id, p.ref, p.name,l.account_id,ac.name,ac.code,acct.balance_type, l.currency_id, l.amount_currency, acct.type "
			"ORDER BY ac.name ",tuple(where_params))
			#"ORDER BY p.name,l.account_id ")
		 
		res = cr.dictfetchall()
#		 print 'res ',res
		for r in res:
			if r['debit'] > 0 or r['credit'] > 0 :
				key = characteristic_key(r)
				if key not in partner_data:
					partner_data[key] = {
						'partner_id':r['partner_id'],
						'currency_id':r['currency_id'],
						'date':'',
						'partner_ref': r['ref'] or '',
						'name': r['partner_name'] or u'Харилцагчгүй',
						'account': '%s %s' % (r['code'],r['account_name']),
						'account_code': r['code'],
						'account_name': r['account_name'],
						'account_type':r['account_type'],
						'initial_cur': 0,
						'initial': 0,
						'debit_cur': 0,
						'debit': 0,
						'credit_cur': 0,
						'credit': 0,
						'balance': 0,
						'balance_cur': 0,
						'category_id':r['category_id'],
					}
				partner_data[key]['debit_cur'] += (r['debit_cur'] or 0)
				partner_data[key]['debit'] += (r['debit'] or 0)
				partner_data[key]['credit_cur'] += (abs(r['credit_cur']) or 0)
				partner_data[key]['credit'] += (abs(r['credit']) or 0)
				if r['balance_type'] == 'passive':
					partner_data[key]['balance'] += (r['credit'] or 0) - (r['debit'] or 0)
					partner_data[key]['balance_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
				else :
					partner_data[key]['balance'] += (r['debit'] or 0) - (r['credit'] or 0)
					partner_data[key]['balance_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
#		 print 'partner_data: ', partner_data
		if not data.get('partner_id', False) and data['condition'] != 'all':
			if data['condition'] == 'non-balance':
				for key in partner_data.keys():
					if abs(partner_data[key]['balance']) >= 1:
						del partner_data[key]
			else :
				for key in partner_data.keys():
					if abs(partner_data[key]['balance']) < 1:
						del partner_data[key]
#						 
		#return sorted(partner_data.values(), key=itemgetter('name'))
		return sorted(partner_data.values(), key=itemgetter('account_type'))   
	
	def _print_report(self, data):
#		print "guilgee balancee   23165465464654654654",data
		form = self.read()[0]
		data['form'] = form
		data['form'].update(self._build_contexts(data))
#		 data = self.pre_print_report(data)
#		 if  form['is_excel']:
		return self._make_excel(data)
		
	def _make_excel(self, data):
#		 data = self.prepare_data(cr, uid, ids, context=context)
#		 user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
		company = self.company_id
		
#		 pretty = c2c_helper.comma_me # Тоог мянгатын нарийвчлалтай болгодог method
		styledict = self.env['abstract.report.excel'].get_easyxf_styles()
		
		ezxf = xlwt.easyxf
		book = xlwt.Workbook(encoding='utf8')
		sheet = book.add_sheet(u'Payable Receivable Ledger')
		sheet_act = book.add_sheet(u'Төлбөр тогтоосон акт')
		sheet.portrait = False
		data_wz = data['form']
		date_str = '%s-%s' % (
#			 datetime.datetime.strptime(data_wz['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
#			 datetime.datetime.strptime(data_wz['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
				data['form']['date_from'],
				 data['form']['date_to']
		)
		title = u'Маягт АӨ-1'
		report_name = u'Харилцагчийн тайлан '
		
#		 sheet.write(0, 6, title, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
		sheet.write(0, 0, u'Байгууллагын нэр: %s' % company.name, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
		sheet.write(2, 2, report_name, xlwt.easyxf('font:bold on, height 200;align:wrap off,vert centre,horiz left;'))
		
		sheet_act.write_merge(2, 2, 2, 5, u'ЭД ХАРИУЦАГЧИЙН ТӨЛБӨР ТОГТООСОН АКТ', xlwt.easyxf('font:bold on, height 200;align:wrap off,vert centre,horiz left;'))
#		 sheet_act.write(5, 0, u'"Жүр үр" ХХК-ийн '+unicode(self.warehouse_id.code)+u' агуулахын эд хариуцагчид өдрөөс өдрийг хүртэлх хугацаанд хариуцаж байсан бараа материалын', xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
		sheet_act.write(6, 0, u"	  тооцоог нягтлан бодох бүртгэлийн анхан шатны баримтуудаар нэг бүрчлэн шалгаж үзэхэд %s" % u'('+'			'+u') төгрөгний', xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
		sheet_act.write(7, 3, u"%s" % u'зөрүүтэй гарсан болно.', xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
		# sheet_act.write(9, 2, u'Тооцооны дэлгэрэнгүй хүснэгт', xlwt.easyxf('font:bold on, height 200;align:wrap off,vert centre,horiz left;'))
		sheet_act.write(3, 7,  u'%s' % (time.strftime('%Y-%m-%d'),), ezxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 160'))
		sheet_act.write(10, 1, u'Код', styledict['heading_xf'])
		sheet_act.write(10, 2, u'Нэрс', styledict['heading_xf'])
		sheet_act.write_merge(10, 10, 3, 4, u'Тооцоо хийсэн өдрүүд', styledict['heading_xf'])
		sheet_act.write_merge(11, 17, 3, 4, u'', styledict['text_xf'])
		sheet_act.write(10, 5, u'Дүн', styledict['heading_xf'])
		sheet_act.write(10, 6, u'Гарын үсэг', styledict['heading_xf'])
		sheet_act.write(17, 1, u'Дүн', styledict['text_xf'])
		sheet_act.write(11, 1, u'', styledict['text_xf'])
		sheet_act.write(11, 2, u'', styledict['text_xf'])
		sheet_act.write(11, 5, u'', styledict['text_xf'])
		sheet_act.write(11, 6, u'', styledict['text_xf'])
		sheet_act.write(12, 1, u'', styledict['text_xf'])
		sheet_act.write(12, 2, u'', styledict['text_xf'])
		sheet_act.write(12, 5, u'', styledict['text_xf'])
		sheet_act.write(12, 6, u'', styledict['text_xf'])
		sheet_act.write(13, 1, u'', styledict['text_xf'])
		sheet_act.write(13, 2, u'', styledict['text_xf'])
		sheet_act.write(13, 5, u'', styledict['text_xf'])
		sheet_act.write(13, 6, u'', styledict['text_xf'])
		sheet_act.write(14, 1, u'', styledict['text_xf'])
		sheet_act.write(14, 2, u'', styledict['text_xf'])
		sheet_act.write(14, 5, u'', styledict['text_xf'])
		sheet_act.write(14, 6, u'', styledict['text_xf'])
		sheet_act.write(15, 1, u'', styledict['text_xf'])
		sheet_act.write(15, 2, u'', styledict['text_xf'])
		sheet_act.write(15, 5, u'', styledict['text_xf'])
		sheet_act.write(15, 6, u'', styledict['text_xf'])
		sheet_act.write(16, 1, u'', styledict['text_xf'])
		sheet_act.write(16, 2, u'', styledict['text_xf'])
		sheet_act.write(16, 5, u'', styledict['text_xf'])
		sheet_act.write(16, 6, u'', styledict['text_xf'])
		sheet_act.write(17, 2, u'', styledict['text_xf'])
		sheet_act.write(17, 5, u'', styledict['text_xf'])
		sheet_act.write(17, 6, u'', styledict['text_xf'])
		sheet_act.write(20, 2, u'Тайлан гаргасан: Нягтлан бодогч ............................... /						  /', xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
		sheet_act.write(22, 2, u'Танилцсан: Салбарын менежер ............................... /						  /', xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))


		if data_wz.get('account_id', False):
			a = self.env['account.account'].browse(data_wz['account_id'][0])
			sheet.write(3, 0, u'Дансны дугаар: %s' % a.code, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
			sheet.write(3, 6, u'Дансны нэр: %s' % a.name, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
			
		sheet.write(5, 6, u'Тайлант хугацаа: %s' % date_str, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
		if data_wz.get('partner_id', False):
			partner = self.env['res.partner'].browse(data_wz['partner_id'][0])
			sheet.write(4, 0, u"Харилцагчийн код: %s" % (partner.ref or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
			sheet.write(4, 6, u"Харилцагчийн нэр: %s" % partner.name, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
		rowx = 7
		if data_wz.get('account_id', False):
			lines = self.create_report_data_account(data['form'])
		else:
			lines = self.create_report_data(data['form'])
		if not data_wz['is_currency']:
			sheet.write_merge(rowx, rowx+2, 0, 0, u'Код', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 1, 1, u'Бизнесийн хамтрагчийн нэр', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 2, 2, u'Дансны код', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 3, 3, u'Дансны нэр', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 4, 4, u'Payment type /Төлбөрийн хэлбэр', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 5, 5, u'Эхний үлдэгдэл', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 6, 6, u'Борлуулалт', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 7, 7, u'Борлуулалтын буцаалт', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 8, 8, u'Орлого/Төлбөр', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 9, 9, u'Дебит мемо', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 10, 10, u'Кредит мемо', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 11, 11, u'Эцсийн үлдэгдэл', styledict['heading_xf'])
			
			
			rowx += 3
			
#			 lines = report_service.get_report_data(cr, uid, data, context=context)
			data = {}
			sums = {}
			cur_data = {}
			if data_wz.get('account_id', False):
				for line in lines:
					
					if line['category_id'] not in data.keys():
						data[line['category_id']] = [{'partner_ref' : line['partner_ref'],
																   'name' : line['name'],
																   'account_type' : line['account_type'],
		#															'currency_id' : currency,
																   'initial_cur' : line['initial_cur'],
																   'initial' : line['initial'],
																   'debit_cur' : line['debit_cur'],
																   'debit' : line['debit'],
																   'credit_cur' : line['credit_cur'],
																   'credit' : line['credit'],
		#															'balance_cur' : line['balance_cur'],
																   'balance' : line['balance'],
		#															'account' : line['account'],
																	'account_code': line['account_code'],
																	'account_name': line['account_name'],
																	'partner_id': line['partner_id'],
																   }]
						sums[line['category_id']] = {'sum_initial_cur': line['initial_cur'],
												 'sum_initial': line['initial'],
												 'sum_debit_cur': line['debit_cur'],
												 'sum_debit': line['debit'],
												 'sum_credit_cur': line['credit_cur'],
												 'sum_credit': line['credit'],
												 'sum_balance_cur': line['balance_cur'],
												 'sum_balance': line['balance']
												 }
					else:
						data[line['category_id']].append({'partner_ref' : line['partner_ref'],
																   'name' : line['name'],
																   'account_type' : line['account_type'],
		#															'currency_id' : currency,
																   'initial_cur' : line['initial_cur'],
																   'initial' : line['initial'],
																   'debit_cur' : line['debit_cur'],
																   'debit' : line['debit'],
																   'credit_cur' : line['credit_cur'],
																   'credit' : line['credit'],
		#															'balance_cur' : line['balance_cur'],
																   'balance' : line['balance'],
		#															'account' : line['account'],
																	'account_code': line['account_code'],
																	'account_name': line['account_name'],
																	'partner_id': line['partner_id'],
																   })	  
					
			else: 
				for line in lines:
					
					if line['partner_id'] not in data.keys():
						data[line['partner_id']] = [{'partner_ref' : line['partner_ref'],
																   'name' : line['name'],
																   'account_type' : line['account_type'],
		#															'currency_id' : currency,
																   'initial_cur' : line['initial_cur'],
																   'initial' : line['initial'],
																   'debit_cur' : line['debit_cur'],
																   'debit' : line['debit'],
																   'credit_cur' : line['credit_cur'],
																   'credit' : line['credit'],
																   'credit_refund' : line['refund_credit'],
		#															'balance_cur' : line['balance_cur'],
																   'balance' : line['balance'],
		#															'account' : line['account'],
																	'account_code': line['account_code'],
																	'account_name': line['account_name'],
																   }]
						sums[line['partner_id']] = {'sum_initial_cur': line['initial_cur'],
												 'sum_initial': line['initial'],
												 'sum_debit_cur': line['debit_cur'],
												 'sum_debit': line['debit'],
												 'sum_credit_cur': line['credit_cur'],
												 'sum_credit': line['credit'],
												 'sum_balance_cur': line['balance_cur'],
												 'sum_balance': line['balance']
												 }
					else:
						data[line['partner_id']].append({'partner_ref' : line['partner_ref'],
																   'name' : line['name'],
																   'account_type' : line['account_type'],
		#															'currency_id' : currency,
																   'initial_cur' : line['initial_cur'],
																   'initial' : line['initial'],
																   'debit_cur' : line['debit_cur'],
																   'debit' : line['debit'],
																   'credit_cur' : line['credit_cur'],
																   'credit' : line['credit'],
																   'credit_refund' : line['refund_credit'],
		#															'balance_cur' : line['balance_cur'],
																   'balance' : line['balance'],
		#															'account' : line['account'],
																	'account_code': line['account_code'],
																	'account_name': line['account_name'],
																   })				
											 
				
			number = 1
			
			totals = [0,0,0,0,0,0,0,0]
			
			a = {}
#			 for key in sorted(data.keys()):
#				 a[key] = data[key]
			
			for k in data.keys():
				if data_wz.get('account_id', False):
					partner_cat = self.env['res.partner.category'].browse(k)
					if partner_cat:
						sheet.write(rowx, 0, u'Ангилал:', styledict['text_bold_xf_no_wrap'])
						sheet.write(rowx, 1, partner_cat.name, styledict['text_bold_xf_no_wrap'])
					else:
						sheet.write(rowx, 0, u'Ангилал:', styledict['text_bold_xf_no_wrap'])
						sheet.write(rowx, 1, u'Ангилалгүй', styledict['text_bold_xf_no_wrap'])
#					 sheet.write(rowx, 2, partner.name, styledict['text_bold_xf_no_wrap'])
					rowx += 1
#					 print "k",k
#					 print "data[k] ",data[k]
					totals2 = [0,0,0,0,0,0,0,0]
					sort_data=[]
					for l in data[k]:
						partner = self.env['res.partner'].browse(l['partner_id'])
						if partner.name:
							l['partner_name']=partner.name
						else:
							l['partner_name']='null'
						sort_data.append(l)
#					 for line in data[k]:
					result = sorted(sort_data, key=itemgetter('partner_name'))
					for line in result:
						partner = self.env['res.partner'].browse(line['partner_id'])
#						 print 'partner ',partner
					#for key, lines in a:
#						 print "lines ",line
		#				 if key == u'Ангилалгүй':
		#					 sheet.write(rowx, 1, key, styledict['text_bold_xf_no_wrap'])
		#				 else:
		#				 sheet.write(rowx, 0, '', styledict['text_center_xf'])
						sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
						sheet.write(rowx, 1, partner.ref, styledict['text_xf'])
						sheet.write(rowx, 2, partner.name, styledict['text_xf'])
		#				 sheet.write(rowx, 5, line['initial_cur'], styledict['number_xf'])
						sheet.write(rowx, 3, line['initial'], styledict['number_xf'])
		#				 sheet.write(rowx, 7, line['debit_cur'], styledict['number_xf'])
						sheet.write(rowx, 4, line['debit'], styledict['number_xf'])
		#				 sheet.write(rowx, 9, line['credit_cur'], styledict['number_xf'])
						sheet.write(rowx, 5, line['credit'], styledict['number_xf'])
		#				 sheet.write(rowx, 11, line['balance_cur'], styledict['number_xf'])
						sheet.write(rowx, 6, line['balance'], styledict['number_xf'])
		
						
						totals[0] += line['initial_cur']
						totals[1] += line['initial']
						totals[2] += line['debit_cur']
						totals[3] += line['debit']
						totals[4] += line['credit_cur']
						totals[5] += line['credit']
		#				 totals[6] += line['balance_cur']
						totals[7] += line['balance']
		
						totals2[0] += line['initial_cur']
						totals2[1] += line['initial']
						totals2[2] += line['debit_cur']
						totals2[3] += line['debit']
						totals2[4] += line['credit_cur']
						totals2[5] += line['credit']
		#				 totals[6] += line['balance_cur']
						totals2[7] += line['balance']
						
						number += 1
						rowx += 1
		
					sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
					sheet.write(rowx, 3, totals2[1], styledict['number_bold_xf'])
					sheet.write(rowx, 4, totals2[3], styledict['number_bold_xf'])
					sheet.write(rowx, 5, totals2[5], styledict['number_bold_xf'])
					sheet.write(rowx, 6, totals2[7], styledict['number_bold_xf'])
					rowx+=1
				else:
					partner = self.env['res.partner'].browse(k)
#					 sheet.write(rowx, 0, u'харилцагч:', styledict['text_bold_xf_no_wrap'])
#					 sheet.write(rowx, 1, partner.ref, styledict['text_bold_xf_no_wrap'])
#					 sheet.write(rowx, 2, partner.name, styledict['text_bold_xf_no_wrap'])
#					 rowx += 1
#					 print "k-------------",k
#					 print "data[k] ",data[k]
					totals2 = [0,0,0,0,0,0,0,0]
					for line in data[k]:
					#for key, lines in a:
		#				 if key == u'Ангилалгүй':
		#					 sheet.write(rowx, 1, key, styledict['text_bold_xf_no_wrap'])
		#				 else:

		#				 sheet.write(rowx, 0, '', styledict['text_center_xf'])
#						 sheet.write(rowx, 0, u'харилцагч:', styledict['text_bold_xf_no_wrap'])
#						 sheet.write(rowx, 1, partner.ref, styledict['text_bold_xf_no_wrap'])
#						 sheet.write(rowx, 2, partner.name, styledict['text_bold_xf_no_wrap'])
		
#						 sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
						if partner.payment_type=='loan':
							ptype=u'зээлээр'
						elif partner.payment_type=='cash':
							ptype=u'Бэлнээр'
						else:
							ptype=u'Банкаар'
						sheet.write(rowx, 0, partner.ref, styledict['text_center_xf'])
						sheet.write(rowx, 1, partner.name, styledict['text_xf'])
						sheet.write(rowx, 2, line['account_code'], styledict['text_center_xf'])
						sheet.write(rowx, 3, line['account_name'], styledict['text_xf'])
						sheet.write(rowx, 4, ptype, styledict['number_xf'])
						sheet.write(rowx, 5, line['initial'], styledict['number_xf'])
		#				 sheet.write(rowx, 7, line['debit_cur'], styledict['number_xf'])
						sheet.write(rowx, 6, line['debit'], styledict['number_xf'])
		#				 sheet.write(rowx, 9, line['credit_cur'], styledict['number_xf'])
						sheet.write(rowx, 7, line['credit_refund'], styledict['number_xf'])
						sheet.write(rowx, 8, line['credit'], styledict['number_xf'])
						sheet.write(rowx, 9, 0, styledict['number_xf'])
						sheet.write(rowx, 10, 0, styledict['number_xf'])
						sheet.write(rowx, 11, line['balance'], styledict['number_xf'])
		
						
						totals[0] += line['initial_cur']
						totals[1] += line['initial']
						totals[2] += line['debit_cur']
						totals[3] += line['debit']
						totals[4] += line['credit_refund']
						totals[5] += line['credit']
		#				 totals[6] += line['balance_cur']
						totals[7] += line['balance']
		
						totals2[0] += line['initial_cur']
						totals2[1] += line['initial']
						totals2[2] += line['debit_cur']
						totals2[3] += line['debit']
						totals2[4] += line['credit_cur']
						totals2[5] += line['credit']
		#				 totals[6] += line['balance_cur']
						totals2[7] += line['balance']
						
						number += 1
						rowx += 1
		
#					 sheet.write(rowx, 2, u'Дүн', styledict['text_bold_xf_no_wrap'])
#					 sheet.write(rowx, 3, totals2[1], styledict['number_bold_xf'])
#					 sheet.write(rowx, 4, totals2[3], styledict['number_bold_xf'])
#					 sheet.write(rowx, 5, totals2[5], styledict['number_bold_xf'])
#					 sheet.write(rowx, 6, totals2[7], styledict['number_bold_xf'])
#					 rowx+=1
			
			if number < 10:
				while number <= 10:
					sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
					sheet.write(rowx, 1, '', styledict['text_xf'])
					sheet.write(rowx, 2, '', styledict['text_xf'])
					sheet.write(rowx, 3, '', styledict['text_xf'])
					sheet.write(rowx, 4, '', styledict['number_xf'])
					sheet.write(rowx, 5, '', styledict['number_xf'])
					sheet.write(rowx, 6, '', styledict['number_xf'])
					number += 1
					rowx += 1
			
			sheet.write_merge(rowx,rowx, 0,2, u'Нийт дүн', styledict['heading_xf'])
			sheet.write(rowx, 3, '', styledict['heading_xf'])
			sheet.write(rowx, 4, '', styledict['heading_xf'])
			sheet.write(rowx, 5, totals[1], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 6, totals[3], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 7, totals[4], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 8, totals[5], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 9, 0, styledict['gold_number_bold_xf'])
			sheet.write(rowx, 10, 0, styledict['gold_number_bold_xf'])
			sheet.write(rowx, 11, totals[7], styledict['gold_number_bold_xf'])
			
			rowx += 1
			for key, value in cur_data.items():
				sheet.write(rowx, 0, '', styledict['text_xf'])
				sheet.write(rowx, 1, '', styledict['text_xf'])
				sheet.write(rowx, 2, '', styledict['text_xf_grey'])
				sheet.write(rowx, 3, key, styledict['text_xf_grey'])
				sheet.write(rowx, 4, '', styledict['text_xf_grey'])
				sheet.write(rowx, 5, value['initial_cur'], styledict['number_xf_grey'])
				sheet.write(rowx, 6, value['initial'], styledict['number_xf_grey'])
				sheet.write(rowx, 7, value['debit_cur'], styledict['number_xf_grey'])
				sheet.write(rowx, 8, value['debit'], styledict['number_xf_grey'])
				sheet.write(rowx, 9, value['credit_cur'], styledict['number_xf_grey'])
				sheet.write(rowx, 10, value['credit'], styledict['number_xf_grey'])
				sheet.write(rowx, 11, value['balance_cur'], styledict['number_xf_grey'])
				sheet.write(rowx, 12, value['balance'], styledict['number_xf_grey'])
				rowx += 1
			inch = 1200
			sheet.col(0).width = int(2*inch)
			sheet.col(1).width = int(5*inch)
			sheet.col(2).width = int(2*inch)
			sheet.col(3).width = int(4*inch)
			sheet.col(4).width = int(2*inch)
			sheet.col(5).width = int(3*inch)
			sheet.col(6).width = int(3*inch)
		else:
			sheet.write_merge(rowx, rowx+2, 0, 0, u'', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 1, 1, u'', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 2, 2, u'Код', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 3, 3, u'Нэр', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+2, 4, 4, u'Валютын төрөл', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+1, 5, 6, u'Эхний үлдэгдэл', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 5, 5, u'Валют', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 6, 6, u'Төгрөг', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx, 7, 10, u'Гүйлгээний дүн', styledict['heading_xf'])
			sheet.write_merge(rowx+1, rowx+1, 7, 8, u'Дебит', styledict['heading_xf'])
			sheet.write_merge(rowx+1, rowx+1, 9, 10, u'Кредит', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 7, 7, u'Валют', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 8, 8, u'Төгрөг', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 9, 9, u'Валют', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 10, 10, u'Төгрөг', styledict['heading_xf'])
			sheet.write_merge(rowx, rowx+1, 11, 12, u'Эцсийн үлдэгдэл', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 11, 11, u'Валют', styledict['heading_xf'])
			sheet.write_merge(rowx+2, rowx+2, 12, 12, u'Төгрөг', styledict['heading_xf'])
			
			rowx += 3
#			 
			
			if number < 10:
				while number <= 10:
					sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
					sheet.write(rowx, 1, '', styledict['text_xf'])
					sheet.write(rowx, 2, '', styledict['text_xf'])
					sheet.write(rowx, 3, '', styledict['text_xf'])
					sheet.write(rowx, 4, '', styledict['number_xf'])
					sheet.write(rowx, 5, '', styledict['number_xf'])
					sheet.write(rowx, 6, '', styledict['number_xf'])
					number += 1
					rowx += 1
			
			sheet.write_merge(rowx,rowx, 0,2, u'Нийт дүн', styledict['heading_xf'])
			sheet.write(rowx, 4, totals[1], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 5, totals[3], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 6, totals[5], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 7, totals[7], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 8, totals[1], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 9, totals[3], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 10, totals[5], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 11, totals[7], styledict['gold_number_bold_xf'])
			sheet.write(rowx, 12, totals[7], styledict['gold_number_bold_xf'])
			
			rowx += 1
				
			inch = 1200
			sheet.col(0).width = int(1.6*inch)
			sheet.col(1).width = int(0.6*inch)
			sheet.col(2).width = int(3*inch)
			sheet.col(3).width = int(5*inch)
			sheet.col(4).width = int(1*inch)
			sheet.col(5).width = int(2*inch)
			sheet.col(6).width = int(3*inch)
			sheet.col(7).width = int(2*inch)
			sheet.col(8).width = int(3*inch)
			sheet.col(9).width = int(2*inch)
			sheet.col(10).width = int(3*inch)
			sheet.col(11).width = int(2*inch)
			sheet.col(12).width = int(3*inch)

		sheet.write(rowx, 0, u'Хэвлэсэн огноо: %s' % (time.strftime('%Y-%m-%d'),), ezxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 160'))
		
		sheet.write(rowx+4, 2, u"Боловсруулсан: Нягтлан бодогч ......................................... /										 /",
					xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
		sheet.write(rowx+6, 2, u"Хянасан: Ерөнхий нягтлан бодогч .............................................../										 /", 
					xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
		
#		 return {'data':book, 'attache_name':report_service.attache_name}
	
#		 from io import StringIO
		from io import BytesIO
		buffer = BytesIO()
		book.save(buffer)
		buffer.seek(0)
		
		filename = "partner_balance_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
		out = base64.encodestring(buffer.getvalue())
		buffer.close()
		
		excel_id = self.env['report.excel.output'].create({
								'data':out,
								'name':filename
		})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}	
		
#		 mod_obj = self.env['ir.model.data']
#		 form_res = mod_obj.get_object_reference('mw_base', 'action_excel_output_view')
#		 form_id = form_res and form_res[1] or False
#		 return {
#			 'name': _('Account Transaction Balance Report'),
#			 'view_type': 'form',
#			 'view_mode': 'form',
#			 'res_model': 'report.excel.output',
#			 'res_id': excel_id.id,
#			 'view_id': False,
#			 'views': [(form_id, 'form')],
#			 'type': 'ir.actions.act_window',
#			 'target':'new'
#		 }	 
		
account_partner_sales_ledger()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
