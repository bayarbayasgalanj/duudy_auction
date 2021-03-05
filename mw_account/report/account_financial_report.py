# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields

# ---------------------------------------------------------
# Account Financial Report
# ---------------------------------------------------------

class account_financial_report_line(models.Model):
	_name = "account.financial.report.line"
	_description = "account financial report line"

	name = fields.Char(string='Reference',required=True)
	number = fields.Char(string='Number',required=True)
	seq = fields.Integer(string='Sequence',required=True)
	report_id = fields.Many2one('account.financial.html.report', string="Report")
#	 account_id = fields.Many2one('account.account', string="Account")
	account_ids = fields.Many2many('account.account', 'account_account_financial_line_report', 'report_id', 'account_id', 'Accounts')
	is_bold = fields.Boolean(string='Is bold')
	is_number = fields.Boolean(string='Is number')

	is_line = fields.Boolean(string='Is line')
	line_ids = fields.Many2many('account.financial.report.line', 'accountline_financial_line_report', 'report_id', 'line_id', 'Lines')
	
	
class account_financial_report(models.Model):
	_inherit = "account.financial.html.report"
	_description = "Account Report"

#	 type = fields.Selection([
#		 ('sum', 'View'),
#		 ('accounts', 'Accounts'),
#		 ('line_accounts', 'Accounts Lines'),
#		 ('account_type', 'Account Type'),
#		 ('account_report', 'Report Value'),
#		 ], 'Type', default='sum')

	is_mw = fields.Boolean('Is MW?')
	account_line_ids = fields.One2many('account.financial.report.line','report_id', 'Account lines')
	active = fields.Boolean('Active',default=True)
	branch_id = fields.Many2one('res.branch')
	report_type = fields.Selection([
		('other', 'Other'),
		('balance', 'Balance'),
		('is', 'Income statement'),
		], 'Report Type', default='is')
	

	def _build_contexts(self, data):
		result = {}
#		 print "data ",data
		if not data['date_from'] or not data['date_to']:
			raise UserError((u'Эхлэх дуусах огноо сонгоно уу.'))
		elif data['date_from'] > data['date_to']:
			raise UserError((u'Эхлэх огноо дуусах огнооноос бага байх ёстой.'))
#		 form = self.read()[0]
		result['journal_ids'] = 'journal_ids' in data and data['journal_ids'] or False
		result['state'] = 'target_move' in data and data['target_move'] or ''
		result['date_from'] = data['date_from'] or False
		result['date_to'] = data['date_to'] or False
		result['strict_range'] = True if result['date_from'] else False
#		 result['report_id'] = form['report_id'][0]
		result['company_id'] = data['company_id'][0]
		result['branch_ids'] = data['branch_ids']
		
#		 data['form'].update(self.read(['chart_account_ids'])[0])
#		 result.update(self.read(['check_balance_method'])[0])
#		 result.update(self.read(['chart_account_ids'])[0])
 
		return result
	
	def create_report_data(self, data):
		''' Мөрийн удгуудыг тайлангийн өгөгдөлөөр буцаана.
		'''
		initial_account_ids = []
		account_dict = {}
		account_ids = None
#		 reports=self.env['report.mn.account.report_financial']
#		 account_report = self.env['account.financial.report'].search([('id', '=', data['report_id'])])
		resu={}
		data=self._build_contexts(data)
		for line in self.account_line_ids.sorted(key=lambda r: r.seq):
			if not line.is_line:
				for account in line.account_ids:
					account_br=account.with_context(data)
					if resu.get(line.id,False):
						resu[line.id]['balance'] += account_br.balance
						resu[line.id]['balance_start'] += account_br.balance_start
						resu[line.id]['debit'] += account_br.debit
						resu[line.id]['credit'] += account_br.credit
					else:
						resu[line.id] = {'balance':account_br.balance,
										 'balance_start':account_br.balance_start,
										 'debit':account_br.debit,
										 'credit':account_br.credit,
										 'name':line.name,
										 'number':line.number,
										 'seq':line.seq,
										 'is_bold':line.is_bold,
										 'is_number':line.is_number
										 }
			else:
				for l in line.line_ids:
					if l.is_line:
						for ll in l.line_ids:
							if ll.is_line:
								for lll in ll.line_ids:
									for account in lll.account_ids:					
										account_br=account.with_context(data)
										if resu.get(line.id,False):
											resu[line.id]['balance'] += account_br.balance
											resu[line.id]['balance_start'] += account_br.balance_start
											resu[line.id]['debit'] += account_br.debit
											resu[line.id]['credit'] += account_br.credit
										else:
											resu[line.id] = {'balance':account_br.balance,
															 'balance_start':account_br.balance_start,
															 'debit':account_br.debit,
															 'credit':account_br.credit,
															 'name':line.name,
															 'number':line.number,
															 'seq':line.seq,
															 'is_bold':line.is_bold,
															 'is_number':line.is_number
															 }
							else:   
								for account in ll.account_ids:   
									account_br=account.with_context(data)
									if resu.get(line.id,False):
										resu[line.id]['balance'] += account_br.balance
										resu[line.id]['balance_start'] += account_br.balance_start
										resu[line.id]['debit'] += account_br.debit
										resu[line.id]['credit'] += account_br.credit
									else:
										resu[line.id] = {'balance':account_br.balance,
														 'balance_start':account_br.balance_start,
														 'debit':account_br.debit,
														 'credit':account_br.credit,
														 'name':line.name,
														 'number':line.number,
														 'seq':line.seq,
														 'is_bold':line.is_bold,
														 'is_number':line.is_number
														 }
					else:
						for account in l.account_ids:
							account_br=account.with_context(data)
							if resu.get(line.id,False):
								resu[line.id]['balance'] += account_br.balance
								resu[line.id]['balance_start'] += account_br.balance_start
								resu[line.id]['debit'] += account_br.debit
								resu[line.id]['credit'] += account_br.credit
							else:
								resu[line.id] = {'balance':account_br.balance,
												 'balance_start':account_br.balance_start,
												 'debit':account_br.debit,
												 'credit':account_br.credit,
												 'name':line.name,
												 'number':line.number,
												 'seq':line.seq,
												 'is_bold':line.is_bold,
												 'is_number':line.is_number
												 }
			if not resu.get(line.id,False):
					resu[line.id] = {'balance':0,
									 'balance_start':0,
									 'debit':0,
									 'credit':0,
									 'name':line.name,
									 'number':line.number,
									 'seq':line.seq,
									 'is_bold':line.is_bold,
									 'is_number':line.is_number
									 }							 
#		print 'resu ',resu					   
		return resu
	
	

	def create_report_detail_data(self, data):
		''' Мөрийн удгуудыг тайлангийн өгөгдөлөөр буцаана. Данстайгаар
		'''
		initial_account_ids = []
		account_dict = {}
		account_ids = None
#		 reports=self.env['report.mn.account.report_financial']
#		 account_report = self.env['account.financial.report'].search([('id', '=', data['report_id'])])
		resu={}
		
		data=self._build_contexts(data)
		for line in self.account_line_ids.sorted(key=lambda r: r.seq):
			if not line.is_line:
				balance=0
				balance_start=0
				debit=0
				credit=0
				accout_dict={}
				for account in line.account_ids:
					account_br=account.with_context(data)
					balance+=account_br.balance
					balance_start+=account_br.balance_start
					debit+=account_br.debit
					credit+=account_br.credit
					accout_dict[account.id]= {'balance':account_br.balance,
										 'balance_start':account_br.balance_start,
										 'debit':account_br.debit,
										 'credit':account_br.credit,
										 'name':account.name,
										 'number':account.code,
										 'seq':'',
										 'is_bold':False,
										 'is_number':False
										 }  
#					 accout_dict.append(tmp)			
#					 if resu.has_key(line.id):
#						 resu[line.id]['balance'] += account_br.balance
#						 resu[line.id]['balance_start'] += account_br.balance_start
#						 resu[line.id]['debit'] += account_br.debit
#						 resu[line.id]['credit'] += account_br.credit
#					 else:
#						 resu[line.id] = {'balance':account_br.balance,
#										  'balance_start':account_br.balance_start,
#										  'debit':account_br.debit,
#										  'credit':account_br.credit,
#										  'name':line.name,
#										  'number':line.number,
#										  'seq':line.seq,
#										  'is_bold':line.is_bold,
#										  'is_number':line.is_number
#										  }
				resu[line.id] = {'balance':balance,
										 'balance_start':balance_start,
										 'debit':debit,
										 'credit':credit,
										 'name':line.name,
										 'number':line.number,
										 'seq':line.seq,
										 'is_bold':line.is_bold,
										 'is_number':line.is_number,
										 'account_ids':accout_dict
										 }
			else:
				for l in line.line_ids:
					if l.is_line:
						for ll in l.line_ids:
							if ll.is_line:
								for lll in ll.line_ids:
									for account in lll.account_ids:					
										account_br=account.with_context(data)
										if resu.get(line.id,False):
											resu[line.id]['balance'] += account_br.balance
											resu[line.id]['balance_start'] += account_br.balance_start
											resu[line.id]['debit'] += account_br.debit
											resu[line.id]['credit'] += account_br.credit
										else:
											resu[line.id] = {'balance':account_br.balance,
															 'balance_start':account_br.balance_start,
															 'debit':account_br.debit,
															 'credit':account_br.credit,
															 'name':line.name,
															 'number':line.number,
															 'seq':line.seq,
															 'is_bold':line.is_bold,
															 'is_number':line.is_number
															 }
							else:   
								for account in ll.account_ids:   
									account_br=account.with_context(data)
									if resu.get(line.id,False):
										resu[line.id]['balance'] += account_br.balance
										resu[line.id]['balance_start'] += account_br.balance_start
										resu[line.id]['debit'] += account_br.debit
										resu[line.id]['credit'] += account_br.credit
									else:
										resu[line.id] = {'balance':account_br.balance,
														 'balance_start':account_br.balance_start,
														 'debit':account_br.debit,
														 'credit':account_br.credit,
														 'name':line.name,
														 'number':line.number,
														 'seq':line.seq,
														 'is_bold':line.is_bold,
														 'is_number':line.is_number
														 }
					else:
						for account in l.account_ids:
							account_br=account.with_context(data)
							if resu.get(line.id,False):
								
								resu[line.id]['balance'] += account_br.balance
								resu[line.id]['balance_start'] += account_br.balance_start
								resu[line.id]['debit'] += account_br.debit
								resu[line.id]['credit'] += account_br.credit
							else:
								resu[line.id] = {'balance':account_br.balance,
												 'balance_start':account_br.balance_start,
												 'debit':account_br.debit,
												 'credit':account_br.credit,
												 'name':line.name,
												 'number':line.number,
												 'seq':line.seq,
												 'is_bold':line.is_bold,
												 'is_number':line.is_number
												 }
			if resu.get(line.id,False):
				
					resu[line.id] = {'balance':0,
									 'balance_start':0,
									 'debit':0,
									 'credit':0,
									 'name':line.name,
									 'number':line.number,
									 'seq':line.seq,
									 'is_bold':line.is_bold,
									 'is_number':line.is_number
									 }							 
#		 print ('resu ',resu  )					 
		return resu	
		
	
