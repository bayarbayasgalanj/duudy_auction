# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import float_is_zero
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang
from odoo.exceptions import UserError, ValidationError

import time
import math
from odoo.addons.mw_base.report_helper import verbose_numeric, comma_me, convert_curr
from odoo.addons.mw_base.verbose_format import verbose_format

class AccountBankStatementLine(models.Model):
	_inherit = "account.bank.statement.line"
	_order = " date desc, id desc,sequence"

	bank_account_id = fields.Many2one('res.partner.bank', string='Bank account')
	import_line_id = fields.Many2one('account.move.line', 'Imported move', readonly=True)
	invoice_ids = fields.Many2many('account.move', 'account_invoice_bank_line_rel', 'line_id', 'invoice_id', string="Invoices", copy=False, readonly=True)
	import_line_ids = fields.One2many('account.invoice.bank.statement','bsl_id', string='Lines')
	analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')
	import_aml_ids = fields.One2many('account.aml.bank.statement','bsl_id', string='Lines')#Түр ашиглахгүй
#	 imported_aml_ids = fields.Many2many('account.move.line', 'account_move_line_bank_line_import_rel', 'line_id', 'aml_id',  string='Account AML', copy=False, readonly=True)

#	 move_color = fields.Boolean(string='Color',
#		 store=True, readonly=True, compute='_check_move_color')
#	 inv_color = fields.Boolean(string='Color2',
#		 store=True, readonly=True, compute='_check_move_color')

	move_color = fields.Boolean(string='Color',)
	inv_color = fields.Boolean(string='Color2',)

	cashbox_end_id = fields.Many2one('account.bank.statement.cashbox', string="Ending Cashbox")
	partner_print = fields.Char('Partner')
	transfer_line_id = fields.Many2one('account.bank.statement.line', string='Transfer statement')


	is_payable = fields.Boolean('type',compute='_compute_internal_type',store=True)

	@api.depends('account_id','account_id.internal_type')
	def _compute_internal_type(self):

		for item in self:
			if item.account_id and item.account_id.internal_type in ('receivable','payable'):
				item.is_payable=True
			else:
				item.is_payable=False



	def button_validate_line(self):
		moves = self.env['account.move']
		for st_line in self:
			#upon bank statement confirmation, look if some lines have the account_id set. It would trigger a journal entry
			#creation towards that account, with the wanted side-effect to skip that line in the bank reconciliation widget.
#			 journal_entries = line_journal_entries[st_line]
			st_line.fast_counterpart_creation()
			if not st_line.account_id and not st_line.statement_id.currency_id.is_zero(st_line.amount):
				raise UserError(_('All the account entries lines must be processed in order to close the statement.'))

		return True

	@api.depends('import_aml_ids','journal_entry_ids.payment_id','journal_entry_ids.payment_id.invoice_ids')
	def _check_move_color(self):
		for line in self:
			if line.invoice_ids or line.import_aml_ids:
				line.move_color=True
			else:
				line.move_color=False
			if line.journal_entry_ids and line.journal_entry_ids.payment_id and line.journal_entry_ids.payment_id.invoice_ids:
				line.inv_color=True
			else:
				line.inv_color=False
		return True


	def print_bank_order(self):
#	 def print_bank_order(self, cr, uid, ids, context=None):
		''' Төлбөрийн даалгаврын баримт хэвлэх, Касс зарлагын баримт хэвлэх
		'''
		# print '123'
#		 line = self.browse(cr, uid, ids[0], context=context)
#		 statement = line.statement_id
# #		 self.pool.get('payment.request').write(cr, 1, statement.id, {'is_bank': False}, context=context)
#		 print "statement ",statement
#		 if statement.journal_id.type == 'bank':
#			 return self.pool['report'].get_action(cr, uid, ids, 'mn_account.print_bank_order', context=context)
#		 return self.pool['report'].get_action(cr, uid, ids, 'mn_account.print_cash_order', context=context)
		model_id = self.env['ir.model'].sudo().search([('model','=','account.bank.statement.line')], limit=1)
		if self.journal_id.type=='bank':
			template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','tulburiin_daalgavar')], limit=1)
		else:
#			 return self.env['report'].get_action(self, 'mn_account.report_cash_income_receipt')
			if self.amount<0:
				template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','cash_expense')], limit=1)
			else:
				template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','cash_income')], limit=1)

		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))


	def amount_str(self,ids):
		line=self.browse(ids)
#		 list = verbose_numeric(abs(line.amount))[0]
		if line.statement_id.journal_id and line.statement_id.journal_id.currency_id:
			list=verbose_format(abs(line.amount),line.statement_id.journal_id.currency_id)
		else:
			list=verbose_format(abs(line.amount))
		return list



	def amount_abs(self,ids):
		line=self.browse(ids)
#		 list = verbose_numeric(abs(line.amount))[0]
#		 list="%.2f" % round(abs(line.amount),2)
		list= '{:0,.2f}'.format(round(abs(line.amount),2))
		return list


	def self_num(self,ids):
		line=self.browse(ids)
		account_num=''
		if line.statement_id.journal_id.bank_account_id:
			account_num = line.statement_id.journal_id.bank_account_id.acc_number
		else:
			raise UserError(_(u'Журнал дээр дансы тохиргоогоо хийнэ үү1!'))
		return account_num


	def report_self_name(self,ids):
		line=self.browse(ids)
		account_num=''
		if line.statement_id.journal_id.bank_account_id:
			if line.statement_id.journal_id.bank_account_id.bank_id:
				account_num = line.statement_id.journal_id.bank_account_id.bank_id.name
			else:
				raise UserError(_(u'Журнал дээрх дансы банк сонгож өгнө үү!'))
		else:
			raise UserError(_(u'Журнал дээр дансы тохиргоогоо хийнэ үү2!'))
		return account_num


	def account_num(self,ids):
		line=self.browse(ids)
		account_num=''
		if line.bank_account_id:
			account_num = line.bank_account_id.acc_number
		else:
			raise UserError(_(u'Харилцагчийн дансны дугаараа сонгоно уу!'))
		return account_num


	def report_account_name(self,ids):
		line=self.browse(ids)
		account_num=''
		if line.bank_account_id:
			if line.bank_account_id.bank_id:
				account_num = line.bank_account_id.bank_id.name
			else:
				raise UserError(_(u'Харилцагчийн дансны банк сонгоогүй байна!'))
		else:
			raise UserError(_(u'Харилцагчийн дансны дугаараа сонгоно уу!'))
		return account_num


	def report_partner(self,ids):
		line=self.browse(ids)
		name=''
		if line.partner_id:
			name = line.partner_id.name
		elif line.partner_print:
			name = line.partner_print
#		 else:
#			 raise UserError(_(u'Харилцагчаа сонгоно уу!'))
		return name


	def report_company(self,ids):
		line=self.browse(ids)
		name=''
		if line.statement_id.company_id:
			name = line.statement_id.company_id.name
		else:
			raise UserError(_(u'Компани олдсонгүй!'))
		return name


	def report_a(self,ids):
		line=self.browse(ids)
		return abs(line.amount)



	def button_validate_line(self):
		moves = self.env['account.move']
		for st_line in self:
#			 print 'st_linest_line111: ',st_line
#			 print 'st_line.journal_entry_ids1 ',st_line.journal_entry_ids
			if st_line.account_id and not st_line.journal_entry_ids.ids:
				st_line.fast_counterpart_creation()
			elif not st_line.journal_entry_ids.ids and not st_line.amount==0:
				raise UserError(_('All the account entries lines must be processed in order to close the statement.'))
#			 print 'st_line.journal_entry_ids ',st_line.journal_entry_ids
			for aml in st_line.journal_entry_ids:
				moves |= aml.move_id
			if moves:
				moves.filtered(lambda m: m.state != 'posted').post()
			st_line.link_bank_to_partner_line()
#		 statements.write({'state': 'confirm', 'date_done': time.strftime("%Y-%m-%d %H:%M:%S")})
		return True


	def link_bank_to_partner_line(self):
		for st_line in self:
			if st_line.bank_account_id and st_line.partner_id and not st_line.bank_account_id.partner_id:
				st_line.bank_account_id.partner_id = st_line.partner_id


	def print_mw_statement(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','account.bank.statement.line')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','cash_count')], limit=1)
		print ('template ',template)
		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

	def get_wh_name(self,ids):
		return self.browse(ids).statement_id.journal_id.name

	def get_user_name(self,ids):
#		 return self.browse(ids).statement_id.user_id.name
		if  self.browse(ids).statement_id.branch_id:
			owner=self.browse(ids).statement_id.branch_id#self.browse(ids).statement_id.owner_user_ids[0]
		else:
			raise UserError((u'Хэрэглэгчид сонгоогүй байна.'))
		print ('owner.name ',owner.name)
#		 return unicode(owner.name)
		return owner.name


	def amount_str_count(self,ids):
		line=self.browse(ids)
		list=verbose_format(abs(line.amount))
		return list

	def ctotal_amount(self,ids):
		line=self.browse(ids)
		list=(abs(line.amount))
		return list


	def get_cash_box_other(self,ids):
		self_br=self.browse(ids)
		cash_box = self_br.cashbox_end_id
		if cash_box and cash_box.desc:
			return cash_box.desc + ': '+str(cash_box.other)
		return ''

	def get_balance_end_real(self, ids):
#		 self_br=self.browse(ids)
#		 cash_box = self_br.cashbox_end_id
		other=0
#		 if cash_box:
#			 other=cash_box.other
		total = abs(self.browse(ids).amount)+abs(other)
		return total


	def get_cah_box(self, ids):
		headers = [
		u'Дэвсгэрт',
		u'Тоо',
		u'Дүн',
		]
		datas = []
		i = 1
		report_id = self.browse(ids)
		self_br=self.browse(ids)
		cash_box = self_br.cashbox_end_id
		if cash_box:
			total = 0.0
			other=0.0
			for item in cash_box.cashbox_lines_ids:
				temp = [
				str(int(item.coin_value)),
				str(item.number),
				format(int(item.subtotal),',d')
#				 "{0:,.2f}".format(line.credit)
				# '0' if line.debit==0 else str(line.debit),
				# '0' if line.credit==0 else str(line.credit)
				]
				datas.append(temp)
				total += item.subtotal
			if abs(self_br.amount)!=abs(total+cash_box.other):
				raise UserError((u'Мөнгөн дүн дэвсгэрт хоёр зөрүүтэй байна. Шалгана уу'))

			# i += 1
		res = {'header': headers, 'data':datas}
		return res


	def open_cashbox_id(self):
		context = dict(self.env.context or {})

		if context.get('cashbox_id'):
			context['active_id'] = self.id
			return {
				'name': _('Cash Control'),
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'account.bank.statement.cashbox',
				'view_id': self.env.ref('mw_account.view_account_bnk_stmt_wm_cashbox').id,
				'type': 'ir.actions.act_window',
				'res_id': self.env.context.get('cashbox_id'),
				'context': context,
				'target': 'new'
			}

	def get_cah_box_old(self, ids):
		self_br=self.browse(ids)
		cash_box = self_br.cashbox_end_id
		header = [u'Дэвсгэрт']
		number = [u'тоо/ш']
		subtotal = [u'дүн']
		if cash_box:
			total = 0.0
			other=0.0
			for item in cash_box.cashbox_lines_ids:
				header.append(str(int(item.coin_value)))
				number.append(str(item.number))
				subtotal.append(format(int(item.subtotal),',d'))
				total += item.subtotal
			header.append(u'Бүгд')
			number.append('')
			if abs(self_br.amount)!=abs(total+cash_box.other):
				raise UserError((u'Мөнгөн дүн дэвсгэрт хоёр зөрүүтэй байна. Шалгана уу'))
			subtotal.append(format(int(total),',d'))
		datas = {'header':header,'data':[number,subtotal]}
		return datas



	def show_details(self):
		data_obj = self.env['ir.model.data']
		view = data_obj.xmlid_to_res_id('mw_account.view_bank_statement_line_mw_form')
		line = self.browse()
		context = dict(self._context)
		return {
			 'name': (u'Хуулга'),
			 'type': 'ir.actions.act_window',
			 'view_type': 'form',
			 'view_mode': 'form',
			 'res_model': 'account.bank.statement.line',
			 'views': [(view, 'form')],
			 'view_id': view,
			 'target': 'new',
			 'res_id': self.id,
			'context': context,
		}


	@api.onchange('account_id')
	def onchange_account_id(self):
		if self.account_id:
			if self.account_id.cmtype_ids:
				self.cash_type_id = self.account_id.cmtype_ids[0].id


class AccountBankStatement(models.Model):
	_inherit = "account.bank.statement"
#
#
	@api.depends('line_ids','line_ids.amount')
	def _compute_amount(self):
		'''Орлого зарлага дүн тооцох
		'''

		for item in self:
			in_amount=0
			out_amount=0
			for line in item.line_ids:
				if line.amount<0:
					out_amount+= line.amount
				else:
					in_amount+= line.amount
			item.in_total=in_amount
			item.out_total=out_amount

	in_total = fields.Float('Amount in', compute='_compute_amount',store=True)
	out_total = fields.Float('Amount ex', compute='_compute_amount',store=True)

	def button_import(self):
		'''Ажил гүйлгээ банкны хуулга руу ИМПОРТ хийнэ
		'''
		obj = self
		st_line = self.env['account.bank.statement.line']
		j_id = obj.journal_id
		this_date = obj.date
		is_curr=False
		company_curr=self.env.user.company_id.currency_id
		if self.journal_id.currency_id and company_curr!=self.journal_id.currency_id:
			is_curr=True
		move_ids =  self.env['account.move.line'].search(
										[('move_id.journal_id','=',j_id.id),
										 ('move_id.date','=',this_date),
										 ('account_id','=',j_id.default_debit_account_id.id),
										 ('account_id','=',j_id.default_credit_account_id.id),
										 ('statement_line_id','=',False),
										 ('move_id.state','=','posted')
										 ])

		if not move_ids:
			raise UserError("Импортлогдох ажил гүйлгээ байхгүй байна")
		for line in move_ids:
			account_id=False
# 			print ('line ',line)
			amount = 0.0
			if line.debit > 0.0 and not is_curr:#line.amount_currency == 0.0:
				amount=line.debit
				line_ids =  self.env['account.move.line'].search(
												[('move_id','=',line.move_id.id),
												 ('account_id','!=',j_id.default_debit_account_id.id),
												 ('account_id','!=',j_id.default_credit_account_id.id),
												 ('credit','>',0),
												 ('move_id.state','=','posted')
												 ])
				if len(line_ids)==1:
					account_id=line_ids[0].account_id.id
			elif line.credit > 0.0 and not is_curr:# line.amount_currency == 0.0:
				amount=-line.credit
				line_ids =  self.env['account.move.line'].search(
												[('move_id','=',line.move_id.id),
												 ('account_id','!=',j_id.default_debit_account_id.id),
												 ('account_id','!=',j_id.default_credit_account_id.id),
												 ('debit','>',0),
												 ('move_id.state','=','posted')
												 ])
				if len(line_ids)==1:
					account_id=line_ids[0].account_id.id
			if is_curr:#(line.amount_currency < 0.0 and line.debit == 0.0) or (line.amount_currency > 0.0 and line.credit == 0.0):
				amount = line.amount_currency
			statement = st_line.create({
					'statement_id':obj.id,
#					 'account_move_line_id':line.id,
					'move_name':line.move_id.name,
#					 'account_id':line.account_id.id,
					'account_id':account_id,
					 'partner_id':line.partner_id.id,
					 'journal_id':line.move_id.journal_id.id,
					 'name':line.move_id.name,
					 'ref':line.move_id.ref,
					 'state':line.move_id.state,
					 'amount':amount,
					 'date':line.move_id.date,
										})
			if not line.payment_id.payment_reference:
				line.payment_id.write({'payment_reference': line.move_id.name})
			line.write({'statement_line_id':statement.id})

		return {}

class AccountInvoiceBankStatement(models.Model):
	_name = 'account.invoice.bank.statement'
	_description = "account invoice bank statement"

	import_inv_id = fields.Many2one('account.move', string='Account Invoice')
	bsl_id = fields.Many2one('account.bank.statement.line', 'Bank statement line', ondelete='cascade')
	date = fields.Date(string='Date')

	inv_amount = fields.Float(string='Amount', digits=(16, 2),)


class AccountAMLBankStatement(models.Model):
	_name = 'account.aml.bank.statement'
	_description = "account aml bank statement"

#	 import_aml_ids = fields.Many2many('account.move.line', 'account_move_line_aml_banks_rel', 'amlb_id', 'aml_id',  string='Account AML', copy=False, readonly=True)
	import_aml_id = fields.Many2one('account.move.line', string='Account aml', ondelete='cascade')

#	 import_aml_ids = fields.Many2many('account.move.line', string='Account AML')
	bsl_id = fields.Many2one('account.bank.statement.line', 'Bank statement line', ondelete='cascade')
	date = fields.Date(string='Date')

	aml_amount = fields.Float(string='Amount', digits=(16, 2),)
	currency_amount = fields.Float(string='Currency Amount', digits=(16, 2),)

	is_mnt = fields.Boolean(string='MNT',default=False)
	currency_id = fields.Many2one('res.currency', string='currency aml')



class AccountBankStmtCashWizard(models.Model):
	"""
	Account Bank Statement popup that allows entering cash details.
	"""
	_inherit = 'account.bank.statement.cashbox'

	@api.model
	def _get_cash_line_box_lines(self):
		#Search last bank statement and set current opening balance as closing balance of previous one
		res = []
		curr = [10, 20, 50, 100, 500, 1000, 5000, 10000, 20000]
		for rs in curr:
			dct = {
				'coin_value': rs,
				'number':0
			}
			res.append(dct)
		return res

	cashbox_lines_ids = fields.One2many('account.cashbox.line', 'cashbox_id', string='Cashbox Lines', default=_get_cash_line_box_lines)



	desc = fields.Char('Desc')
	other = fields.Float('Other')


	def validate(self):
		bnk_stmt_id = self.env.context.get('bank_statement_id', False) or self.env.context.get('active_id', False)
#		 if self.env.context['active_model']=='pos.bank.statement':
#			 bnk_stmt = self.env['pos.bank.statement'].browse(bnk_stmt_id)
		if self.env.context['active_model']=='account.bank.statement.line':
			stmt_line_id = self.env.context.get('active_id', False)
			bnk_stmt = self.env['account.bank.statement.line'].browse(stmt_line_id)
		else:
			bnk_stmt = self.env['account.bank.statement'].browse(bnk_stmt_id)
		total = 0.0
		for lines in self.cashbox_lines_ids:
			total += lines.subtotal
#		 print ('total ',total)
		bnk_stmt.write({'cashbox_end_id': self.id})

#		 if self.env.context.get('balance', False) == 'start':
#			 #starting balance
#			 bnk_stmt.write({'balance_start': total, 'cashbox_start_id': self.id})
#		 else:
#			 #closing balance
#			 print ('total balance_end_real ',total)
#			 bnk_stmt.write({'balance_end_real': total, 'cashbox_end_id': self.id})
		return {'type': 'ir.actions.act_window_close'}



class AccountBankStatementCopy(models.Model):
	_name='account.bank.statement.copy'
	_description = u'Касс хуулбарлах'

	date = fields.Date(string='Огноо', required=True, default=fields.Datetime.now)


	def action_done(self):
		obj = self.env['account.bank.statement'].browse(self._context['active_ids'])
#		 print ('-------------',obj)
		if [x.id for x in obj if x.state!='open']:
			raise UserError((u'Validated төлөвтэй касс орсон байна'))
		elif obj:
			for m in obj:
				branch_id = self.env['account.bank.statement'].search([('journal_id','=',m.journal_id.id),('branch_id','!=',False)],limit=1).branch_id
				if not branch_id:
					raise UserError((u'тухайн журналд ядаж нэг салбар сонгосон хуулга анх үүссэн байх ёстой'))
				if m.journal_id.type=='cash':
					m.create({
					'journal_id': m.journal_id.id,
					'date': self.date,
#					 'owner_user_ids': [(6,0,m.journal_id.sale_user_ids.ids)],
					'branch_id':branch_id.id,
					'balance_start':m.balance_end
					})


		return True
