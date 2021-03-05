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

# _logger = logging.getLogger('odoo')

class account_income_statement_report(models.TransientModel):
	"""
		Монголын Сангийн Яамнаас орлогын тайлан.
	"""
	
	_name = "account.income.statement.report.new"
	_description = "Account income statement Report"
	
	@api.model
	def _default_report(self):
		domain = [
			('name', '=', u'Орлогын тайлан'),
		]
		return self.env['account.financial.html.report'].search(domain, limit=1)
		
#	 check_balance_method = fields.Boolean('Check balance method',default=True)
#	 chart_account_ids = fields.Many2many('account.account', string='Accounts')
	report_id = fields.Many2one('account.financial.html.report',required=True,
		default=_default_report,domain=[('report_type','=','is')],
								string='Report')
	date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
	date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))

#	 period_ids = fields.Many2many('account.period', string='Periods')
#	 fy_ids = fields.Many2many('account.fiscalyear', string='Fiscalyear')
#	 season_ids = fields.Many2many('account.season', string='Улирал')
	target_move = fields.Selection([('posted', 'All Posted Entries'),
									('all', 'All Entries'),
									], string='Target Moves', required=True, default='posted')
	journal_ids = fields.Many2many('account.journal', string='Journals', required=True, default=lambda self: self.env['account.journal'].search([]))
	company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
	branch_ids = fields.Many2many('res.branch', string='Branches')

	is_detail = fields.Boolean('Detail?')
	is_split_branch = fields.Boolean('Split branch?')

	def _print_report(self, data):
		data['form'].update(self._build_contexts(data))
#		 if  form['is_excel']:
		return self._make_excel(data)
#		 else:
#			 return {
#				 'type': 'ir.actions.report.xml',
#				 'report_name': 'account.income.statement.report2',
#				 'datas': data,
#				 'nodestroy': True,
#			 }
		#else : #excel
	
	def check_report(self):
		''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
			тооцоолж байрлуулна.
		'''
		report_obj = self.env['account.financial.html.report'].browse(self.report_id.id)
		
#		 company_obj = self.env['res.company']
#		 report_datas = self.create_report_data(data['form'])
		
		
		ezxf = xlwt.easyxf
		heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
		text_xf = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
		text_right_xf = ezxf('font: bold off; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;')
		text_bold_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
		text_bold_right_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;')
		text_center_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
		number_xf = ezxf('font: bold off; align: horz right; borders: top thin, left thin, bottom thin, right thin;', num_format_str='#,##0.00')
		number_bold_xf = ezxf('font: bold on; align: horz right; borders: top thin, left thin, bottom thin, right thin;', num_format_str='#,##0.00')
		number_green_xf = ezxf('font: italic on; align: horz right; borders: top thin, left thin, bottom thin, right thin;pattern: pattern solid, fore_colour gray25;', num_format_str='#,##0.00')
		text_green_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;pattern: pattern solid, fore_colour gray25;')
		
		book = xlwt.Workbook(encoding='utf8')
		sheet = book.add_sheet('income statement')

#		 if data['form']['period_ids']:
#			 sheet.write(2, 1, u'ОРЛОГЫН ДЭЛГЭРЭНГҮЙ ТАЙЛАН /саруудаар/', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
#			 sheet.write_merge(3, 3, 0, 2,  u'Тайлангийн нэр: %s' %(self.report_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#			 sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(self.company_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#			 sheet.row(1).height = 400
#			 sheet.write(4, 3, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
# #			 sheet.write(5, 3, u'Тайлан хугацаа: %s - %s'%
# #					  (data['form']['date_from'],
# #					   data['form']['date_to']
# #					   ),ezxf('font:bold off;align:wrap off,vert centre,horiz right;'))
#	 #		 date_str = '%s-%s' % (
#	 #			 datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
#	 #			 datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
#	 #		 )
#	 
#			 rowx = 5
#			 sheet.write_merge(rowx, rowx+1, 0, 0, u'Мөрийн дугаар', heading_xf)
#			 sheet.write_merge(rowx, rowx+1, 1, 1, u'Үзүүлэлт', heading_xf)
#	 #		 sheet.write_merge(rowx, rowx, 2, 3, u'Үлдэгдэл', heading_xf)
#			 col=2
#			 rowx_c=rowx
#			 for p_id in data['form']['period_ids']:
#				 rowx=rowx_c
#				 period=self.env['account.period'].browse(p_id)
#				 sheet.write_merge(rowx, rowx+1, col, col,period.date_stop, heading_xf)
# #				 sheet.write_merge(rowx, rowx+1, 3, 3, u'Өссөн дүн', heading_xf)
#				 val=data['form'].get('used_context',{})
#				 val['date_from']=period.date_start
#				 val['date_to']=period.date_stop
#				 report_datas = self.create_report_data(val)
# #				 print 'report_datas ',report_datas
#				 keylist=report_datas.keys()
#				 keylist.sort()
#				 rowx += 1
#		 #		 for line in report_datas:
#				 for line in keylist:
#					 rowx += 1
#					 text=text_xf
#					 number=number_xf
#		 #			 print 'report_datas[line] ',report_datas[line]
#		 #			 balance=abs(report_datas[line]['balance'])
#		 #			 balance_start=abs(report_datas[line]['balance_start'])
#					 balance=abs(report_datas[line]['debit'])-abs(report_datas[line]['credit'])
# #					 balance_month=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
#					 if report_datas[line]['is_bold']:
#						 text=text_bold_xf
#						 number=number_bold_xf
#					 if not report_datas[line]['is_number']:
#						 report_datas[line]['number']=''
# #						 balance_month=''
#					 if col==2:
#						 sheet.write(rowx, 0, report_datas[line]['number'],text)
#						 sheet.write(rowx, 1, report_datas[line]['name'], text)
# #					 sheet.write(rowx, 2, -balance_month, number)
#					 sheet.write(rowx, col, -balance, number)	 
#				 col+=1
#		 elif data['form']['fy_ids']:
#			 sheet.write(2, 1, u'ОРЛОГЫН ДЭЛГЭРЭНГҮЙ ТАЙЛАН /Жилээр/', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
#			 sheet.write_merge(3, 3, 0, 2,  u'Тайлангийн нэр: %s' %(report_obj.browse(data['form']['report_id']).name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#			 sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(company_obj.browse(data['form']['company_id']).name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#			 sheet.row(1).height = 400
#			 sheet.write(4, 3, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
# #			 sheet.write(5, 3, u'Тайлан хугацаа: %s - %s'%
# #					  (data['form']['date_from'],
# #					   data['form']['date_to']
# #					   ),ezxf('font:bold off;align:wrap off,vert centre,horiz right;'))
#	 #		 date_str = '%s-%s' % (
#	 #			 datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
#	 #			 datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
#	 #		 )
#	 
#			 rowx = 5
#			 sheet.write_merge(rowx, rowx+1, 0, 0, u'Мөрийн дугаар', heading_xf)
#			 sheet.write_merge(rowx, rowx+1, 1, 1, u'Үзүүлэлт', heading_xf)
#	 #		 sheet.write_merge(rowx, rowx, 2, 3, u'Үлдэгдэл', heading_xf)
#			 col=2
#			 rowx_c=rowx
#			 for p_id in data['form']['fy_ids']:
#				 rowx=rowx_c
#				 fy=self.env['account.fiscalyear'].browse(p_id)
#				 sheet.write_merge(rowx, rowx+1, col, col,fy.date_stop, heading_xf)
# #				 sheet.write_merge(rowx, rowx+1, 3, 3, u'Өссөн дүн', heading_xf)
#				 val=data['form'].get('used_context',{})
#				 val['date_from']=fy.date_start
#				 val['date_to']=fy.date_stop
#				 report_datas = self.create_report_data(val)
# #				 print 'report_datas ',report_datas
#				 keylist=report_datas.keys()
#				 keylist.sort()
#				 rowx += 1
#		 #		 for line in report_datas:
#				 for line in keylist:
#					 rowx += 1
#					 text=text_xf
#					 number=number_xf
#		 #			 print 'report_datas[line] ',report_datas[line]
#		 #			 balance=abs(report_datas[line]['balance'])
#		 #			 balance_start=abs(report_datas[line]['balance_start'])
#					 balance=abs(report_datas[line]['debit'])-abs(report_datas[line]['credit'])
# #					 balance_month=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
#					 if report_datas[line]['is_bold']:
#						 text=text_bold_xf
#						 number=number_bold_xf
#					 if not report_datas[line]['is_number']:
#						 balance=''
#						 balance_month=''
#					 if col==2:
#						 sheet.write(rowx, 0, report_datas[line]['number'],text)
#						 sheet.write(rowx, 1, report_datas[line]['name'], text)
# #					 sheet.write(rowx, 2, -balance_month, number)
#					 sheet.write(rowx, col, -balance, number)	 
#				 col+=1	
#		 elif data['form']['season_ids']:
#			 sheet.write(2, 1, u'ОРЛОГЫН ДЭЛГЭРЭНГҮЙ ТАЙЛАН /Улиралаар/', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
#			 sheet.write_merge(3, 3, 0, 2,  u'Тайлангийн нэр: %s' %(report_obj.browse(data['form']['report_id']).name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#			 sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(company_obj.browse(data['form']['company_id']).name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#			 sheet.row(1).height = 400
#			 sheet.write(4, 3, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
# #			 sheet.write(5, 3, u'Тайлан хугацаа: %s - %s'%
# #					  (data['form']['date_from'],
# #					   data['form']['date_to']
# #					   ),ezxf('font:bold off;align:wrap off,vert centre,horiz right;'))
#	 #		 date_str = '%s-%s' % (
#	 #			 datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
#	 #			 datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
#	 #		 )
#	 
#			 rowx = 5
#			 sheet.write_merge(rowx, rowx+1, 0, 0, u'Мөрийн дугаар', heading_xf)
#			 sheet.write_merge(rowx, rowx+1, 1, 1, u'Үзүүлэлт', heading_xf)
#	 #		 sheet.write_merge(rowx, rowx, 2, 3, u'Үлдэгдэл', heading_xf)
#			 col=2
#			 rowx_c=rowx
#			 for p_id in data['form']['season_ids']:
#				 rowx=rowx_c
#				 fy=self.env['account.season'].browse(p_id)
#				 sheet.write_merge(rowx, rowx+1, col, col,fy.date_stop, heading_xf)
# #				 sheet.write_merge(rowx, rowx+1, 3, 3, u'Өссөн дүн', heading_xf)
#				 val=data['form'].get('used_context',{})
#				 val['date_from']=fy.date_start
#				 val['date_to']=fy.date_stop
#				 report_datas = self.create_report_data(val)
# #				 print 'report_datas ',report_datas
#				 keylist=report_datas.keys()
#				 keylist.sort()
#				 rowx += 1
#		 #		 for line in report_datas:
#				 for line in keylist:
#					 rowx += 1
#					 text=text_xf
#					 number=number_xf
#		 #			 print 'report_datas[line] ',report_datas[line]
#		 #			 balance=abs(report_datas[line]['balance'])
#		 #			 balance_start=abs(report_datas[line]['balance_start'])
#					 balance=abs(report_datas[line]['debit'])-abs(report_datas[line]['credit'])
# #					 balance_month=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
#					 if report_datas[line]['is_bold']:
#						 text=text_bold_xf
#						 number=number_bold_xf
#					 if not report_datas[line]['is_number']:
#						 balance=''
#						 balance_month=''
#					 if col==2:
#						 sheet.write(rowx, 0, report_datas[line]['number'],text)
#						 sheet.write(rowx, 1, report_datas[line]['name'], text)
# #					 sheet.write(rowx, 2, -balance_month, number)
#					 sheet.write(rowx, col, -balance, number)	 
#				 col+=1	
								
#		 else:
		if self.is_split_branch and self.branch_ids:
			branches = ''
			col=2
			sheet.write(2, 1, u'ОРЛОГЫН ДЭЛГЭРЭНГҮЙ ТАЙЛАН', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
			sheet.write_merge(3, 3, 0, 2,  u'Тайлангийн нэр: %s' %(self.report_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(self.company_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.write_merge(5, 5, 0, 1,  u'Салбарууд: %s' %(branches), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.row(1).height = 400
			sheet.write(4, 3, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.write(5, 3, u'Тайлан хугацаа: %s - %s'%
					 (self.date_from,
					  self.date_to
					  ),ezxf('font:bold off;align:wrap off,vert centre,horiz right;'))
			rowx = 6
			rowx_c=rowx			
			sheet.write_merge(rowx, rowx+1, 0, 0, u'Мөрийн дугаар', heading_xf)
			sheet.write_merge(rowx, rowx+1, 1, 1, u'Үзүүлэлт', heading_xf)
			for branch in self.branch_ids:
				rowx=rowx_c				
		#		 date_str = '%s-%s' % (
		#			 datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
		#			 datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
		#		 )
		
#				 sheet.write_merge(rowx, rowx+1, 2, 2, u'Тайлант үеийн дүн', heading_xf)
#				 sheet.write_merge(rowx, rowx+1, 3, 3, u'Өссөн дүн', heading_xf)
				sheet.write_merge(rowx, rowx+1, col, col, branch.name, heading_xf)
		
				d=self.read()
				d[0]['branch_ids']=[branch.id]
				if self.is_detail:
					report_month_datas = report_obj.create_report_detail_data(d[0])
				else:
					report_month_datas = report_obj.create_report_data(d[0])
#				 val=d[0]
#				 val['date_from']=datetime(val['date_from'].year,1,1)
#				 val['date_to']=datetime(val['date_to'].year,val['date_to'].month,val['date_to'].day)
		#		 report_obj2 = self.env['account.financial.html.report'].browse(self.report_id.id)
				for account in self.env['account.account'].search([]):
					self.env.cache.remove(account, account._fields['balance'])
					self.env.cache.remove(account, account._fields['credit'])
					self.env.cache.remove(account, account._fields['debit'])
		
				
#				 if self.is_detail:
#					 report_datas = report_obj.create_report_detail_data(val)
#				 else:
#					 report_datas = report_obj.create_report_data(val)
				keylist=sorted(report_month_datas)
				rowx += 1
		#		 for line in report_datas:
				if self.is_detail:
					for line in keylist:
						rowx += 1
						text=text_xf
						number=number_xf
			#			 print 'report_datas[line] ',report_datas[line]
			#			 balance=abs(report_datas[line]['balance'])
			#			 balance_start=abs(report_datas[line]['balance_start'])
#						 balance=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
						balance_month=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
						if report_month_datas[line]['is_bold']:
							text=text_bold_xf
							number=number_bold_xf
						if not report_month_datas[line]['is_number']:
							balance=0
							balance_month=0
						if col==2:		
								
							sheet.write(rowx, 0, report_month_datas[line]['number'],text)
							sheet.write(rowx, 1, report_month_datas[line]['name'], text)
						sheet.write(rowx, col, -balance_month, number)
						if report_month_datas[line].get('account_ids',False):
							acc_month_data=report_month_datas[line]['account_ids']
							acc_data=report_month_datas[line]['account_ids']
							for acc in acc_data:
		#						 print 'acc ',acc_data[acc]
								rowx += 1
								balance=abs(acc_data[acc]['debit'])-abs(acc_data[acc]['credit'])
								balance_month=abs(acc_month_data[acc]['debit'])-abs(acc_month_data[acc]['credit'])
		#						 if acc_data[acc]['is_bold']:
		#							 text=text_bold_xf
		#							 number=number_bold_xf
								text=text_xf
								number=number_xf
		#						 if not acc_data[acc]['is_number']:
		#							 balance=0
		#							 balance_month=0
#								 if col==2:		
#									 sheet.write(rowx, 0, acc_data[acc]['number'],text)
#									 sheet.write(rowx, 1, acc_data[acc]['name'], text)
								sheet.write(rowx, col, -balance_month, number)
#								 sheet.write(rowx, 3, -balance, number)					 
				else: 
					for line in keylist:
						rowx += 1
						text=text_xf
						number=number_xf
			#			 print 'report_datas[line] ',report_datas[line]
			#			 balance=abs(report_datas[line]['balance'])
			#			 balance_start=abs(report_datas[line]['balance_start'])
						balance_month=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
						if report_month_datas[line]['is_bold']:
							text=text_bold_xf
							number=number_bold_xf
						if not report_month_datas[line]['is_number']:
							balance=0
							balance_month=0
						if col==2:						
							sheet.write(rowx, 0, report_month_datas[line]['number'],text)
							sheet.write(rowx, 1, report_month_datas[line]['name'], text)
						sheet.write(rowx, col, -balance_month, number)
				col+=1
															  
			inch = 3000
			sheet.col(0).width = int(0.7*inch)
			sheet.col(1).width = int(4.5*inch)
			sheet.col(2).width = int(2*inch)
			sheet.col(3).width = int(2*inch)
			sheet.col(4).width = int(2*inch)
			sheet.col(5).width = int(2*inch)
			sheet.col(6).width = int(2*inch)
			sheet.col(7).width = int(2*inch)
			sheet.col(8).width = int(2*inch)
			sheet.row(7).height = 500
			rowx+=1			
		else:
			branches = ''
			if self.branch_ids:
				for branch in self.branch_ids:
					branches+=branch.name+', '
			sheet.write(2, 1, u'ОРЛОГЫН ДЭЛГЭРЭНГҮЙ ТАЙЛАН', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
			sheet.write_merge(3, 3, 0, 2,  u'Тайлангийн нэр: %s' %(self.report_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(self.company_id.name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.write_merge(5, 5, 0, 1,  u'Салбарууд: %s' %(branches), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.row(1).height = 400
			sheet.write(4, 3, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
			sheet.write(5, 3, u'Тайлан хугацаа: %s - %s'%
					 (self.date_from,
					  self.date_to
					  ),ezxf('font:bold off;align:wrap off,vert centre,horiz right;'))
	#		 date_str = '%s-%s' % (
	#			 datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
	#			 datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
	#		 )
	
			rowx = 6
			sheet.write_merge(rowx, rowx+1, 0, 0, u'Мөрийн дугаар', heading_xf)
			sheet.write_merge(rowx, rowx+1, 1, 1, u'Үзүүлэлт', heading_xf)
	#		 sheet.write_merge(rowx, rowx, 2, 3, u'Үлдэгдэл', heading_xf)
			sheet.write_merge(rowx, rowx+1, 2, 2, u'Тайлант үеийн дүн', heading_xf)
			sheet.write_merge(rowx, rowx+1, 3, 3, u'Өссөн дүн', heading_xf)
	#		
	
			d=self.read()
			if self.is_detail:
				report_month_datas = report_obj.create_report_detail_data(d[0])
			else:
				report_month_datas = report_obj.create_report_data(d[0])
			val=d[0]
	#		 val['date_from']=str(val['date_from'].year)+'-01-01'
	#		 val['date_to']=str(val['date_to'].year)+'-'+str(val['date_to'].month)+'-'+str(val['date_to'].day)
			val['date_from']=datetime(val['date_from'].year,1,1)
			val['date_to']=datetime(val['date_to'].year,val['date_to'].month,val['date_to'].day)
	#		 report_obj2 = self.env['account.financial.html.report'].browse(self.report_id.id)
			for account in self.env['account.account'].search([]):
				self.env.cache.remove(account, account._fields['balance'])
				self.env.cache.remove(account, account._fields['credit'])
				self.env.cache.remove(account, account._fields['debit'])
	
			
			if self.is_detail:
				report_datas = report_obj.create_report_detail_data(val)
			else:
	#			 print ('val ',val)
				report_datas = report_obj.create_report_data(val)
	#		 print ('report_datas ',report_datas)
	#		 print ('report_month_datas ',report_month_datas)
	#		 keylist=report_datas.keys()
	#		 keylist.sort()
			keylist=sorted(report_datas)
			rowx += 1
	#		 for line in report_datas:
			if self.is_detail:
				for line in keylist:
					rowx += 1
					text=text_xf
					number=number_xf
		#			 print 'report_datas[line] ',report_datas[line]
		#			 balance=abs(report_datas[line]['balance'])
		#			 balance_start=abs(report_datas[line]['balance_start'])
					balance=abs(report_datas[line]['debit'])-abs(report_datas[line]['credit'])
					balance_month=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
					if report_datas[line]['is_bold']:
						text=text_bold_xf
						number=number_bold_xf
					if not report_datas[line]['is_number']:
						balance=0
						balance_month=0
					sheet.write(rowx, 0, report_datas[line]['number'],text)
					sheet.write(rowx, 1, report_datas[line]['name'], text)
					sheet.write(rowx, 2, -balance_month, number)
					sheet.write(rowx, 3, -balance, number) 
					if report_month_datas[line].get('account_ids',False):
						acc_month_data=report_month_datas[line]['account_ids']
						acc_data=report_datas[line]['account_ids']
						for acc in acc_data:
	#						 print 'acc ',acc_data[acc]
							rowx += 1
							balance=abs(acc_data[acc]['debit'])-abs(acc_data[acc]['credit'])
							balance_month=abs(acc_month_data[acc]['debit'])-abs(acc_month_data[acc]['credit'])
	#						 if acc_data[acc]['is_bold']:
	#							 text=text_bold_xf
	#							 number=number_bold_xf
							text=text_xf
							number=number_xf
	#						 if not acc_data[acc]['is_number']:
	#							 balance=0
	#							 balance_month=0
							sheet.write(rowx, 0, acc_data[acc]['number'],text)
							sheet.write(rowx, 1, acc_data[acc]['name'], text)
							sheet.write(rowx, 2, -balance_month, number)
							sheet.write(rowx, 3, -balance, number)					 
			else: 
				for line in keylist:
					rowx += 1
					text=text_xf
					number=number_xf
		#			 print 'report_datas[line] ',report_datas[line]
		#			 balance=abs(report_datas[line]['balance'])
		#			 balance_start=abs(report_datas[line]['balance_start'])
					balance=abs(report_datas[line]['debit'])-abs(report_datas[line]['credit'])
					balance_month=abs(report_month_datas[line]['debit'])-abs(report_month_datas[line]['credit'])
					if report_datas[line]['is_bold']:
						text=text_bold_xf
						number=number_bold_xf
					if not report_datas[line]['is_number']:
						balance=0
						balance_month=0
					sheet.write(rowx, 0, report_datas[line]['number'],text)
					sheet.write(rowx, 1, report_datas[line]['name'], text)
					sheet.write(rowx, 2, -balance_month, number)
					sheet.write(rowx, 3, -balance, number)  
														  
			inch = 3000
			sheet.col(0).width = int(0.7*inch)
			sheet.col(1).width = int(4.5*inch)
			sheet.col(2).width = int(2*inch)
			sheet.col(3).width = int(2*inch)
			sheet.col(4).width = int(2*inch)
			sheet.col(5).width = int(2*inch)
			sheet.col(6).width = int(2*inch)
			sheet.col(7).width = int(2*inch)
			sheet.col(8).width = int(2*inch)
			sheet.row(7).height = 500
			rowx+=1
		sheet.write(rowx+2, 1, u'Боловсруулсан нягтлан бодогч.........................................../\
												 /',ezxf('font: bold off; align: wrap off, vert centre, horiz left;'))
		sheet.write(rowx+4, 1, u'Хянасан ерөнхий нягтлан бодогч....................................../\
												 /', ezxf('font: bold off; align: wrap off, vert centre, horiz left;'))
#		 from StringIO import StringIO
#		 buffer = StringIO()
#		 book.save(buffer)
#		 buffer.seek(0)
#		 
#		 filename = "Income_statement_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
#		 out = base64.encodestring(buffer.getvalue())
#		 buffer.close()
#		 
#		 excel_id = self.env['report.excel.output'].create({
#								 'data':out,
#								 'name':filename
#		 })
#		 return {
#			  'type' : 'ir.actions.act_url',
#			  'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
#			  'target': 'new',
#		 }
		from io import BytesIO
		buffer = BytesIO()
		book.save(buffer)
		buffer.seek(0)
		
		filename = "Income_statement_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
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
			  

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
