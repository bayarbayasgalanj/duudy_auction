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

import xlwt
import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

from io import BytesIO
import xlsxwriter
from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles

# _logger = logging.getLogger('odoo')

class account_transaction_balance_report(models.TransientModel):
	"""
		Монголын Сангийн Яамнаас баталсан Гүйлгээ Баланс тайлан.
	"""
	
	_inherit = "account.common.report"
	_name = "account.transaction.balance.report.new"
	_description = "Account Transaction Balance Report"
	
#		 'company_id': fields.many2one('res.company', 'Company'),
#		 'filter': fields.selection([('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True),
#		 'save': fields.boolean('Save to document storage'),
	check_balance_method = fields.Boolean('Check balance method',default=True)
#		 'is_excel': fields.boolean('Is excel'),
#	 chart_account_ids = fields.Many2many('account.account', 'account_report_tb_rel2','report_id','account_id','Accounts', help='Select accounts to general ledger',domain=[('type','not in',['view','consolidation'])],),		
	chart_account_ids = fields.Many2many('account.account', string='Accounts')
	date_from = fields.Date(string='Start Date',default=time.strftime('%Y-01-01'))
	date_to = fields.Date(string='End Date',default=fields.Date.context_today)
	
	report_id = fields.Many2one('account.financial.report', string='Report type', domain=[('type','=','accounts')])

	is_categ = fields.Boolean('Is category',default=False)
	is_parent = fields.Boolean('Is parent',default=False)
	is_report = fields.Boolean('Is report',default=False)

	is_currency = fields.Boolean('Is currency',default=False)

	data = fields.Binary('Data')
	name = fields.Char('Name')

#		 'company_type':	fields.selection(COMPANY_SELECTION, 'Company', required=True),
#		 'journal_ids': fields.many2many('account.journal', 'account_tr_journal_rel', 'account_id', 'journal_id', 'Journals'),
#	 }
	def _build_contexts(self, data):
		result = {}
#		 print "data ",data
		if not data['form']['date_from'] or not data['form']['date_to']:
			raise UserError((u'Эхлэх дуусах огноо сонгоно уу.'))
		elif data['form']['date_from'] > data['form']['date_to']:
			raise UserError((u'Эхлэх огноо дуусах огнооноос бага байх ёстой.'))
			
		result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
		result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
		result['date_from'] = data['form']['date_from'] or False
		result['date_to'] = data['form']['date_to'] or False
		result['strict_range'] = True if result['date_from'] else False
#		 data['form'].update(self.read(['chart_account_ids'])[0])
		result.update(self.read(['check_balance_method'])[0])
		result.update(self.read(['chart_account_ids'])[0])
		result.update(self.read(['is_categ'])[0])
		result.update(self.read(['is_parent'])[0])
		result.update(self.read(['report_id'])[0])
		
		
 
		return result
	
#	 @api.model
	def create_report_data(self, data):
		''' Гүйлгээ баланс тайлангийн мэдээллийг боловсруулж
			тайлангийн форматад тохируулан python [{},{},{}...]
			загвараар хүснэгтийн мөр багануудын өгөгдлийг боловсруулна.
			
		'''
		account_obj = self.pool.get('account.account')
		currency_obj = self.pool.get('res.currency')
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		journal_obj = self.pool.get('account.journal')
		initial_account_ids = []
#		 
		account_dict = {}
		account_ids = None
		if data['chart_account_ids']:
#			 account_ids = account_obj.search(cr, uid, [
#														('parent_id', 'child_of', [data['chart_account_id']]),
#							 ('type','not in', ['view','consolidation']),
#							 ('id','not in', initial_account_ids),
#							 ('id','in',data['account_ids']),
#							 ])
			account_ids = self.env['account.account'].browse(data['chart_account_ids'])
#			 account_ids=self.env['account.account'].search([('id','in',data['chart_account_ids']),('child_parent_ids', '=', False)])
		elif data['report_id']:
			accounts=[]
			query = """
				select account_id from account_account_financial_report where report_line_id={0}			
				""" .format(data['report_id'][0])
			self.env.cr.execute(query)
			query_result = self.env.cr.fetchall()
			for i in query_result:
				accounts.append(i[0])
			account_ids=self.env['account.account'].search([('id', 'in', accounts),('id', 'not in', [8093,8094,16252])],order="parent_left")
		else:
#			 if data['company_type']=='all':
			account_ids=self.env['account.account'].search([('company_id','=',self.company_id.id)])
		lines = []
#		 include_initial_balance Түр данс бол эхнйи үлдэгдэлгүй
#		 context=data['used_context']
		number = 1
		sum_debit = sum_credit = sum_sdebit = sum_scredit = sum_edebit = sum_ecredit = 0.0
		currency_dict={}
# 		if self.is_currency:		
# 			query = """
# (select 'start' as name, sum(amount_currency) as debit, 0 as credit,aml.currency_id,account_id 
# 					from account_move_line aml 
# 							left join account_move m on aml.move_id=m.id 
# 					where aml.date<'{0}' 
# 						and m.state='posted' 
# 						and amount_currency <>0 
# 						and account_id in ({2})
# 					group by aml.currency_id,account_id
#  )
#  union all
#  (select 'debit' as name, sum(amount_currency) as debit, 0 as credit,aml.currency_id,account_id 
# 					from account_move_line aml 
# 							left join account_move m on aml.move_id=m.id 
# 					where aml.date between '{0}' and '{1}'
# 						and m.state='posted' 
# 						and amount_currency >0 
# 						and account_id in ({2})
# 					group by aml.currency_id,account_id
#  )
#   union all
#  (select 'credit' as name, 0 as debit, sum(amount_currency) as credit,aml.currency_id,account_id 
# 					from account_move_line aml 
# 							left join account_move m on aml.move_id=m.id 
# 					where aml.date between '{0}' and '{1}'
# 						and m.state='posted' 
# 						and amount_currency <0 
# 						and account_id in ({2})
# 					group by aml.currency_id,account_id
#  )
# 			    """.format(self.date_from,self.date_to,','.join(map(str,account_ids.ids)))
# 			print ('query11 ',query)
# 			self.env.cr.execute(query)
# 			query_result = self.env.cr.dictfetchall()      
# 			print ('query_result ',query_result)  
			                
# 			for r in query_result:
# 			    users.append(r['user_id'])  
                		
		for account_id in account_ids:
			data['used_context']['company_id']=data['company_id']
			account=account_id.with_context(data.get('used_context',{})) 
			has_move = False
			has_balance = False
# #			print "accountaccountaccount ",account
#			 # Тайлант хугацааны дүн
#			 print "account_data ",account_data
#			 debit = account_data['debit']
#			 credit = account_data['credit']
			debit=account.debit
			credit=account.credit
			currency_list=[]
			is_curr=False
			if data['check_balance_method']:
				start_credit = start_debit =0
				if account.balance_start:
#					 if account.balance_start>0:
#						 start_credit = 0
#						 start_debit = account.balance_start
#					 else:
#						 start_credit = account.balance_start
#						 start_debit = 0
#					 if account.user_type_id.name in ('Payable','Current Liabilities','Non-current Liabilities','Equity',
#											   'Current Year Earnings','Other Income','Income'):
					if account.user_type_id.balance_type =='passive':
#						 if account.user_type_id.include_initial_balance:
						start_credit = -account.balance_start
						start_debit = 0
					else:
						start_credit = 0
#						 if account.user_type_id.include_initial_balance:
						start_debit = account.balance_start
				else:
					start_credit=0
					start_debit=0
				if account.user_type_id.balance_type =='passive':
					if credit==0 and debit==0:
						end_credit = start_credit
						end_debit=0
#					 elif debit>credit:
					else:
						end_credit = start_credit + credit - debit
						end_debit=0
						
				else:
					if credit==0 and debit==0:
						end_debit = start_debit
						end_credit = 0
					else:
						end_debit = start_debit + debit - credit
						end_credit = 0
				if self.is_currency:
					query = """
							(select 'start' as name, sum(amount_currency) as debit, 0 as credit,aml.currency_id,account_id 
												from account_move_line aml 
														left join account_move m on aml.move_id=m.id 
												where aml.date<'{0}' 
													and m.state='posted' 
													and amount_currency <>0 
													and account_id ={2}
												group by aml.currency_id,account_id
							 )
							 union all
							 (select 'debit' as name, sum(amount_currency) as debit, 0 as credit,aml.currency_id,account_id 
												from account_move_line aml 
														left join account_move m on aml.move_id=m.id 
												where aml.date between '{0}' and '{1}'
													and m.state='posted' 
													and amount_currency >0 
													and account_id ={2}
												group by aml.currency_id,account_id
							 )
							  union all
							 (select 'credit' as name, 0 as debit, sum(amount_currency) as credit,aml.currency_id,account_id 
												from account_move_line aml 
														left join account_move m on aml.move_id=m.id 
												where aml.date between '{0}' and '{1}'
													and m.state='posted' 
													and amount_currency <0 
													and account_id ={2}
												group by aml.currency_id,account_id
							 )
					    """.format(self.date_from,self.date_to,account.id)
# 					print ('query22 ',query)
					self.env.cr.execute(query)
					query_result = self.env.cr.dictfetchall()  					
# 					print ('query_result22',query_result)
					cstart=0
					cdebit=0
					ccredit=0
					currency_id=False
					currname=account.currency_id.name
					for i in query_result:
						if not currname and i['currency_id']:
							currname=self.env['res.currency'].browse(i['currency_id']).name
						if currency_id!=i['currency_id']:
							print ('==========================================')
						currency_id=i['currency_id']
						if i['name']=='start' and i.get('debit',0):
							cstart+=i['debit']
						elif i['name']=='debit' and i.get('debit',0):
							cdebit+=i['debit']
						if i['name']=='credit' and i.get('credit',0):
							ccredit+=i['credit']
						is_curr=True
					
					currency_list.append
					cend=cstart+cdebit+ccredit
					currency_list=[ '', account.code+'', currname, cstart>0 and cstart or 0, cstart<0 and cstart or 0,cdebit, ccredit, cend>0 and cend or 0, cend<0 and cend or 0, False ]
#				 if end_credit<>0:
#					 end_debit=0
#				 elif end_debit<>0:
#					 end_credit=0

#				 end_credit = abs(start_credit)-abs(start_debit) + abs(credit) - abs(debit)
#				 end_debit = abs(start_debit)-abs(start_credit) + abs(debit) - abs(credit)

#				 if end_credit<0:
#					 end_credit=0
#				 if end_debit<0:
#					 end_debit=0
#				 end_credit=abs(end_credit)

				if debit != 0 or credit != 0 or start_credit !=0 or start_debit !=0:
					has_move = True # Тухайн тайлант хугацаанд гүйлгээ хийсэн байвал тайланд тусгана.
				
#				 if end_credit > end_debit:
#					 end_debit = 0.0
#				 else :
#					 end_credit = 0.0
#				 if start_credit > start_debit:
#					 start_debit = 0.0
#				 else :
#					 start_credit = 0.0
#				 if end_credit <0:
#					 end_debit = 0.0
#					 end_credit=abs(end_credit)
#				 else :
#					 end_credit = 0.0
#					 end_debit=abs(end_debit)
#				 if start_credit < 0:
#					 start_debit = 0.0
#					 start_credit=abs(start_credit)
#				 else :
#					 start_credit = 0.0
#					 start_debit=abs(start_debit)

			else:
				acc=self.env['account.account'].browse(account.id)
# 				if account.user_type_id.balance_type =='passive':
				if account.balance_start<0:
					if account.balance_start!=0:
						start_credit =  abs(account.balance_start)
						start_debit = 0.0
						end_debit = 0.0
					else:
						start_credit=0
						start_debit=0
					end_credit = start_credit + credit - debit
				else :
					if account.balance_start!=0:
						start_debit = abs(account.balance_start)
						start_credit = 0.0
					else:
						start_credit=0
						start_debit=0
					end_debit = start_debit + debit - credit
					end_credit = 0.0
				if end_debit<0:
					end_credit = abs(end_debit)
					end_debit=0
				elif end_credit<0:
					end_debit = abs(end_credit)
					end_credit=0
				if end_debit != 0 or end_credit != 0 or start_debit != 0 or start_credit != 0 :
					has_balance = True # Тухайн тайлант хугацаанд үлдэгдэлтэй байвал тайланд тусгана.
			if not has_balance and not has_move :
				continue
#			 
			sum_debit += debit
			sum_credit += credit
			sum_sdebit += start_debit
			sum_scredit += start_credit
			sum_edebit += end_debit
			sum_ecredit += end_credit
#			 lines.append([ str(number), account_data['code'], account_data['name'], start_debit, start_credit,
#				 credit, credit, end_debit, end_credit ])
			lines.append([ str(number), account.code, account.name, start_debit, start_credit,
				debit, credit, end_debit, end_credit, False ])
			if is_curr:
				lines.append(currency_list)
#			 lines.append([ str(number), account.code, account.name, start_debit, start_credit,
#				 debit, credit, end_debit, end_credit ])
			number += 1
		sums =[sum_sdebit, sum_scredit, sum_debit, sum_credit, sum_edebit, sum_ecredit]
#		 sum_line = [['', u'Нийт дүн', '', sum_sdebit, sum_scredit, sum_debit, sum_credit, sum_edebit, sum_ecredit,True]]
		lines.sort(key=lambda x:x[1])
#		 return sum_line + lines	
		return lines,sums

	def _print_report(self, data):
#		 print ("guilgee balancee   23165465464654654654",data)
		data['form'].update(self._build_contexts(data))
		form = self.read()[0]
#		 data = self.pre_print_report(data)
		data['form']['company_id'] = form['company_id'][0]
		data['form']['account_ids'] = data['form']['chart_account_ids']
#		 data['form']['company_type'] = data['form']['company_type']
		data['form']['check_balance_method'] = form['check_balance_method']
		data['form']['is_categ'] = form['is_categ']
		data['form']['is_parent'] = form['is_parent']
		
		return self._make_excel(data)
	
	def _make_excel(self, data):
		''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
			тооцоолж байрлуулна.
		'''
		datas = data
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		account_obj = self.pool.get('account.account')
#		report_service = atbr.transaction_balance('report.transaction.balance.report')
#		 
		report_datas,sums = self.create_report_data(data['form'])
#		 form = self.browse(cr, uid, ids[0], context=context)
		
		#context.update({'state':form.target_move})
#		 styledict = self.pool.get('abstract.report.excel').get_easyxf_styles()
		
#		 book = xlwt.Workbook(encoding='utf8')
#		 sheet = book.add_sheet('Transfer Balance')
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'Transfer Balance')

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)
		
		h2 = workbook.add_format()
		h2.set_font_size(9)

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#6495ED')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_bg_color('#6495ED')

		footer = workbook.add_format({'bold': 1})
		footer.set_text_wrap()
		footer.set_font_size(9)
		footer.set_align('right')
		footer.set_align('vcenter')
		footer.set_border(style=1)
		footer.set_bg_color('#F0FFFF')
		footer.set_num_format('#,##0.00')
		

		content_color_float = workbook.add_format()
		content_color_float.set_text_wrap()
		content_color_float.set_font_size(9)
		content_color_float.set_align('right')
		content_color_float.set_align('vcenter')
		content_color_float.set_border(style=1)
		content_color_float.set_bg_color('#87CEFA')
		content_color_float.set_num_format('#,##0.00')		

		format_name = {
			'font_name': 'Times New Roman',
			'font_size': 14,
			'bold': True,
			'align': 'center',
			'valign': 'vcenter'
		}
		# create formats
		format_content_text_footer = {
		'font_name': 'Times New Roman',
		'font_size': 10,
		'align': 'vcenter',
		'valign': 'vcenter',
		}
		format_content_right = {
		'font_name': 'Times New Roman',
		'font_size': 9,
		'align': 'right',
		'valign': 'vcenter',
		'border': 1,
		'num_format': '#,##0.00'
		}
		format_group_center = {
		'font_name': 'Times New Roman',
		'font_size': 10,
		'align': 'center',
		'valign': 'vcenter',
		'border': 1,
		}
		format_group = {
		'font_name': 'Times New Roman',
		'font_size': 10,
		'bold': True,
		'align': 'center',
		'valign': 'vcenter',
		'border': 1,
		'bg_color': '#CFE7F5',
		'num_format': '#,##0.00'
		}
		
		format_group_center = workbook.add_format(format_group_center)
		format_name = workbook.add_format(format_name)
		format_content_text_footer = workbook.add_format(format_content_text_footer)
		format_filter = workbook.add_format(ReportExcelCellStyles.format_filter)
		format_title = workbook.add_format(ReportExcelCellStyles.format_title)
		format_group_right = workbook.add_format(ReportExcelCellStyles.format_group_right)
		format_group_float = workbook.add_format(ReportExcelCellStyles.format_group_float)
		format_group_left = workbook.add_format(ReportExcelCellStyles.format_group_left)
		format_content_text = workbook.add_format(ReportExcelCellStyles.format_content_text)
		format_content_number = workbook.add_format(ReportExcelCellStyles.format_content_number)
		format_content_float = workbook.add_format(ReportExcelCellStyles.format_content_float)
		format_content_center = workbook.add_format(ReportExcelCellStyles.format_content_center)
		format_group = workbook.add_format(format_group)

		format_content_right = workbook.add_format(format_content_right)			 
#		 duration = self.get_period(cr, uid, form)
		
		worksheet.write(0, 1, u'Маягт ГБ', h2)
		worksheet.write(0, 5, u'Байгууллагын нэр: %s' %(self.company_id.name), h2)
		
		worksheet.write(2, 3, u'ГҮЙЛГЭЭ БАЛАНС', h1)
#		 worksheet.row(1).height = 400
		worksheet.write(3, 1, u'Дугаар:', h2)
		worksheet.write(3, 6, u'Огноо: %s' %(time.strftime('%Y-%m-%d'),), h2)
		worksheet.write(5, 5, u'Тайлан хугацаа: %s - %s'%
#				 (datetime.strptime(data['form']['date_from'][0],'%Y-%m-%d').strftime('%Y.%m.%d'),
#				  datetime.strptime(data['form']['date_to'][0],'%Y-%m-%d').strftime('%Y.%m.%d')
				(data['form']['date_from'],
				 data['form']['date_to']
				 ),h2)
#		date_str = '%s-%s' % (
#			datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
#			datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
#		)
#		 worksheet.merge_range(row, 0, row, last_col, item_cat.name, contest_left_bold)

		rowx = 7
		worksheet.merge_range(rowx, 0,rowx+1,  0, u'Д/д', format_title)
		worksheet.merge_range(rowx, 1,rowx+1,  1, u'Дансны дугаар', format_title)
		worksheet.merge_range(rowx, 2, rowx+1, 2, u'Дансны нэр', format_title)
		worksheet.merge_range(rowx, 3, rowx, 4, u'Эхний үлдэгдэл', format_title)
		worksheet.merge_range(rowx, 5, rowx+1, 5, u'Дебет гүйлгээ', format_title)
		worksheet.merge_range(rowx, 6, rowx+1, 6, u'Кредит гүйлгээ', format_title)
		worksheet.merge_range(rowx, 7, rowx, 8, u'Эцсийн үлдэгдэл', format_title)
		rowx += 1
		worksheet.write(rowx, 3, u'Дебет', format_title)
		worksheet.write(rowx, 4, u'Кредит', format_title)
		worksheet.write(rowx, 7, u'Дебет', format_title)
		worksheet.write(rowx, 8, u'Кредит', format_title)
		rowx += 1
		
		worksheet.set_column('A:A', 5)
		worksheet.set_column('B:B', 10)
		worksheet.set_column('C:C', 22)
		worksheet.set_column('D:I', 16)
			  
		if data['form']['is_categ']:
			worksheet.merge_range(rowx, rowx, 0, 0, u'', format_title)
#			 worksheet.merge_range(rowx, rowx, 1, 2, u'ДҮН', format_title)
	#		 worksheet.merge_range(rowx, rowx+1, 2, 2, u'Дансны нэр', format_title)
#			 worksheet.write(rowx, 3, sums[0], format_content_float)
#			 worksheet.write(rowx, 4, sums[1], format_content_float)
#			 worksheet.write(rowx, 5, sums[2], format_content_float)
#			 worksheet.write(rowx, 6, sums[3], format_content_float)
#			 worksheet.write(rowx, 7, sums[4], format_content_float)
#			 worksheet.write(rowx, 8, sums[5], format_content_float)
#			 rowx += 1
				
		if not data['form']['is_categ']:
			rowx += 1
			worksheet.write(rowx, 0, u'', footer)
			worksheet.merge_range(rowx, 1,rowx, 2, u'НИЙТ ДҮН', footer)
#			 worksheet.write(rowx, 3, report_datas[0][3], format_content_float)
#			 worksheet.write(rowx, 4, report_datas[0][4], format_content_float)
#			 worksheet.write(rowx, 5, report_datas[0][5], format_content_float)
#			 worksheet.write(rowx, 6, report_datas[0][6], format_content_float)
#			 worksheet.write(rowx, 7, report_datas[0][7], format_content_float)
#			 worksheet.write(rowx, 8, report_datas[0][8], format_content_float)
			worksheet.write(rowx, 3, sums[0], footer)
			worksheet.write(rowx, 4, sums[1], footer)
			worksheet.write(rowx, 5, sums[2], footer)
			worksheet.write(rowx, 6, sums[3], footer)
			worksheet.write(rowx, 7, sums[4], footer)
			worksheet.write(rowx, 8, sums[5], footer)
 
#		pdf ийн нийбэр дүн мөрийг хасах
#		 if len(report_datas)>0:
#			 report_datas.pop(0)
		for line in report_datas:
			rowx += 1
			if  line[9]:
				worksheet.write(rowx, 0, line[0], format_title)
				worksheet.write(rowx, 1, line[1], format_title)
				worksheet.write(rowx, 2, line[2], format_title)
				worksheet.write(rowx, 3, line[3], format_title)
				worksheet.write(rowx, 4, line[4], format_title)
				worksheet.write(rowx, 5, line[5], format_title)
				worksheet.write(rowx, 6, line[6], format_title)
				worksheet.write(rowx, 7, line[7], format_title)
				worksheet.write(rowx, 8, line[8], format_title)
			else:
				if line[0]=='':
# 					format_content_float=format_title
					worksheet.write(rowx, 0, line[0], format_content_text)
					worksheet.write(rowx, 1, line[1], content_color_float)
					worksheet.write(rowx, 2, line[2], content_color_float)
					worksheet.write(rowx, 3, line[3], content_color_float)
					worksheet.write(rowx, 4, line[4], content_color_float)
					worksheet.write(rowx, 5, line[5], content_color_float)
					worksheet.write(rowx, 6, line[6], content_color_float)
					worksheet.write(rowx, 7, line[7], content_color_float)
					worksheet.write(rowx, 8, line[8], content_color_float)	
				else:
					worksheet.write(rowx, 0, line[0], format_content_text)
					worksheet.write(rowx, 1, line[1], format_content_text)
					worksheet.write(rowx, 2, line[2], format_content_text)
					worksheet.write(rowx, 3, line[3], format_content_float)
					worksheet.write(rowx, 4, line[4], format_content_float)
					worksheet.write(rowx, 5, line[5], format_content_float)
					worksheet.write(rowx, 6, line[6], format_content_float)
					worksheet.write(rowx, 7, line[7], format_content_float)
					worksheet.write(rowx, 8, line[8], format_content_float)									
		#sheet.set_panes_frozen(True) # frozen headings instead of split panes
		#sheet.set_horz_split_pos(2) # in general, freeze after last heading row
		#sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
		#sheet.set_col_default_width(True)
		inch = 3000
		 
		worksheet.write(rowx+2, 2, u'Боловсруулсан нягтлан бодогч.........................................../\
												 /',h2)
		worksheet.write(rowx+4, 2, u'Хянасан ерөнхий нягтлан бодогч....................................../\
												 /', h2)
#		 from StringIO import StringIO
		from io import StringIO
#		 output = BytesIO()
		
		file_name = "transfer_balance_%s.xlsx" % (time.strftime('%Y%m%d_%H%M'),)
		workbook.close()
		out = base64.encodestring(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		# print '-----------------done------------------'
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}
		
	def create_report_data_pivot(self, data):
		account_obj = self.pool.get('account.account')
		currency_obj = self.pool.get('res.currency')
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		journal_obj = self.pool.get('account.journal')
		initial_account_ids = []
#		 
		account_dict = {}
		account_ids = None
		if data['chart_account_ids']:
#			 account_ids = account_obj.search(cr, uid, [
#														('parent_id', 'child_of', [data['chart_account_id']]),
#							 ('type','not in', ['view','consolidation']),
#							 ('id','not in', initial_account_ids),
#							 ('id','in',data['account_ids']),
#							 ])
			account_ids = data['chart_account_ids']
#			 account_ids=self.env['account.account'].search([('id','in',data['chart_account_ids']),('child_parent_ids', '=', False)])
		elif data['report_id']:
			accounts=[]
			query = """
				select account_id from account_account_financial_report where report_line_id={0}			
				""" .format(data['report_id'][0])
			self.env.cr.execute(query)
			query_result = self.env.cr.fetchall()
			for i in query_result:
				accounts.append(i[0])
			account_ids=self.env['account.account'].search([('id', 'in', accounts),('id', 'not in', [8093,8094,16252])],order="parent_left")
		else:
#			 if data['company_type']=='all':
			account_ids=self.env['account.account'].search([('company_id','=',self.company_id.id)])
		lines = []
#		 include_initial_balance Түр данс бол эхнйи үлдэгдэлгүй
#		 context=data['used_context']
		number = 1
		sum_debit = sum_credit = sum_sdebit = sum_scredit = sum_edebit = sum_ecredit = 0.0
		for account_id in account_ids:
			data['used_context']['company_id']=data['company_id']
			account=account_id.with_context(data.get('used_context',{})) 
			has_move = False
			has_balance = False
# #			print "accountaccountaccount ",account
#			 # Тайлант хугацааны дүн
#			 print "account_data ",account_data
#			 debit = account_data['debit']
#			 credit = account_data['credit']
			debit=account.debit
			credit=account.credit
			if data['check_balance_method']:
				if account.balance_start:
#					 if account.balance_start>0:
#						 start_credit = 0
#						 start_debit = account.balance_start
#					 else:
#						 start_credit = account.balance_start
#						 start_debit = 0
#					 if account.user_type_id.name in ('Payable','Current Liabilities','Non-current Liabilities','Equity',
#											   'Current Year Earnings','Other Income','Income'):
					if account.user_type_id.balance_type =='passive':
#						 if account.user_type_id.include_initial_balance:
						start_credit = -account.balance_start
						start_debit = 0
					else:
						start_credit = 0
#						 if account.user_type_id.include_initial_balance:
						start_debit = account.balance_start
				else:
					start_credit=0
					start_debit=0
				if account.user_type_id.balance_type =='passive':
					if credit==0 and debit==0:
						end_credit = start_credit
						end_debit=0
#					 elif debit>credit:
					else:
						end_credit = start_credit + credit - debit
						end_debit=0
						
				else:
					if credit==0 and debit==0:
						end_debit = start_debit
						end_credit = 0
					else:
						end_debit = start_debit + debit - credit
						end_credit = 0

			if debit != 0 or credit != 0 or start_credit !=0 or start_debit !=0:
				has_move = True # Тухайн тайлант хугацаанд гүйлгээ хийсэн байвал тайланд тусгана.
				

			else:
				acc=self.env['account.account'].browse(account.id)
#				 if acc.user_type_id.name in ('Payable','Current Liabilities','Non-current Liabilities','Equity',
#										   'Current Year Earnings','Other Income','Income'):
				if account.user_type_id.balance_type =='passive':
					if account.balance_start:
#						 start_credit =  initial_bals[account_data['id']][0]['credit'] - initial_bals[account_data['id']][0]['debit']
#						 if account.user_type_id.include_initial_balance:
						start_credit =  abs(account.balance_start)
						start_debit = 0.0
						end_debit = 0.0
					else:
						start_credit=0
						start_debit=0
					end_credit = start_credit + credit - debit
				else :
					if account.balance_start:
#						 start_debit = initial_bals[account_data['id']][0]['debit'] - initial_bals[account_data['id']][0]['credit']
#						 if account.user_type_id.include_initial_balance:
						start_debit = abs(account.balance_start)
						start_credit = 0.0
					else:
						start_credit=0
						start_debit=0
					end_debit = start_debit + debit - credit
					end_credit = 0.0
			 
			if end_debit != 0 or end_credit != 0 or start_debit != 0 or start_credit != 0 :
				has_balance = True # Тухайн тайлант хугацаанд үлдэгдэлтэй байвал тайланд тусгана.
			if not has_balance and not has_move :
				continue
#			 
#			 lines.append([ str(number), account_data['code'], account_data['name'], start_debit, start_credit,
#				 credit, credit, end_debit, end_credit ])
			lines.append([ account, start_debit, start_credit,
				debit, credit, end_debit, end_credit ])

#			 lines.append([ str(number), account.code, account.name, start_debit, start_credit,
#				 debit, credit, end_debit, end_credit ])
			number += 1
# 
#		 print "lines:::::::::::::::::::::::::::::",lines
		lines.sort(key=lambda x:x[1])
		return lines	
	
	def view_report(self, data):
		''' Pivot 
		'''
		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
		used_context = self._build_contexts(data)
		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
		 
		data['form'].update(self._build_contexts(data))
		form = self.read()[0]
#		 data = self.pre_print_report(data)
		data['form']['company_id'] = form['company_id'][0]
		data['form']['account_ids'] = data['form']['chart_account_ids']
#		 data['form']['company_type'] = data['form']['company_type']
		data['form']['check_balance_method'] = form['check_balance_method']
		data['form']['is_categ'] = form['is_categ']
		data['form']['is_parent'] = form['is_parent']
	 
		datas = data
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		account_obj = self.pool.get('account.account')
#		report_service = atbr.transaction_balance('report.transaction.balance.report')
#		 
		report_datas = self.create_report_data_pivot(data['form'])
#		 form = self.browse(cr, uid, ids[0], context=context)
		
		for line in report_datas:
			self.env.cr.execute("insert into pivot_report_transfer_balance_account(\
										report_id,account_id,initial_debit,initial_credit,\
										debit,credit,final_debit,final_credit)\
										 values({0},{1},{2},{3},{4},{5},{6},{7})".format(self.id,line[0].id,line[1],line[2],
																						 line[3],line[4],line[5],line[6]))  

		context = dict(self._context)
		# GET views ID		
		mod_obj = self.env['ir.model.data']		

		# INIT query
		# Орлого зарлага хамтдаа
		search_res = mod_obj.get_object_reference('mn_account', 'account_transaction_balance_pivot_search')
		search_id = search_res and search_res[1] or False
		pivot_res = mod_obj.get_object_reference('mn_account', 'account_transaction_balance_pivot_pivot')
		pivot_id = pivot_res and pivot_res[1] or False

		return {
				'name': _('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'account.transaction.balance.pivot',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('report_id','=',self.id),
#							('date','<=',self.date_end),
#							('account_id.company_id','=',self.company_id.id),
#							('state','=',self.state),
						   ],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}							  
#		 return {
#			 'name': _('Account Transaction Balance Report'),
#			 'view_type': 'form',
#			 'view_mode': 'form',
#			 'res_model': 'account.transaction.balance.report.new',
#			 'res_id': self.id,
#			 'view_id': False,
#			 'views': [(False, 'form')],
#			 'type': 'ir.actions.act_window',
#			 'target':'new'
#		 } 


	def print_report_html(self):
		self.ensure_one()
		result_context=dict(self._context or {})
		
# 		data['form'].update(self._build_contexts(data))
		data = {}
		data['ids'] = self.env.context.get('active_ids', [])
		data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
		data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
		used_context = self._build_contexts(data)
		data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
		 
		data['form'].update(self._build_contexts(data))
		form = self.read()[0]
#		 data = self.pre_print_report(data)
		data['form']['company_id'] = form['company_id'][0]
		data['form']['account_ids'] = data['form']['chart_account_ids']
#		 data['form']['company_type'] = data['form']['company_type']
		data['form']['check_balance_method'] = form['check_balance_method']
		data['form']['is_categ'] = form['is_categ']
		data['form']['is_parent'] = form['is_parent']
	 
		datas = data
		fiscalyear_obj = self.pool.get('account.fiscalyear')
		account_obj = self.pool.get('account.account')
		
		report_datas,sums = self.create_report_data(data['form'])
		
		ir_model_obj = self.env['ir.model.data']
		report_id = self.env['mw.account.report'].with_context(data=report_datas).create({'name':'report1',
# 		                                                            'account_id':self.account_id.id,
		                                                            'date_from':self.date_from,
		                                                            'date_to':self.date_to
		                                                            })
		result_context.update({'data':report_datas})
		model, action_id = ir_model_obj.get_object_reference('mw_account', 'action_mw_account_tran_balance_report')
		[action] = self.env[model].browse(action_id).read()
# 		print ('result_context ',result_context)
		action['context'] = result_context
		action['res_id'] = report_id.id
# 		print ('action ',action)
		return action



class AccountReportReport(models.TransientModel):
    _inherit = 'mw.account.report'
    _description = 'Account test report'
    
    name = fields.Char("Name")
#     wizard_id = fields.Many2one('account.test.report')
    account_id = fields.Many2one('account.account', 'Account')
    date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))

    def get_tran_balance_js(self):
    	#context eer avah
        context=dict(self._context or {})
        
        result=[]
        return result
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

