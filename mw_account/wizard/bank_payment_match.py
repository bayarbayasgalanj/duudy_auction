# -*- coding: utf-8 -*-
##############################################################################
#
#	ManageWall, Enterprise Management Solution	
#	Copyright (C) 2007-2014 ManageWall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#
#	Email : daramaa26@gmail.com
#	Phone : 976 + 99081691
#
##############################################################################
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime, time, timedelta
from datetime import date, datetime
	
import logging
_logger = logging.getLogger(__name__)

class bank_payment_match_line(models.TransientModel):

	_name = "bank.payment.match.line"
	_description = "partial bank confirm line"
# 	_rec_name = 'line_id'

	name=fields.Char("Name")
	account_id=fields.Many2one('account.account', string="Account", )
	amount=fields.Float("Amount", )
	line_id=fields.Many2one('account.bank.statement.line', "Move", )
	wizard_id=fields.Many2one('bank.payment.match', string="Wizard", ondelete='CASCADE',readonly=True)
	currency=fields.Many2one('res.currency', string="Currency", help="Currency in which Unit cost is expressed", ondelete='CASCADE',readonly=True)
	date=fields.Date('Date', )
	payment_id=fields.Many2one('account.move.line', 'Payment', )
	partner_id=fields.Many2one('res.partner', 'Partner', )

class bank_payment_match(models.TransientModel):
	
	_name = "bank.payment.match"
	_rec_name = 'statement_id'
	_description = "Partial bank statement confirm Wizard"
	
	def search_partner(self,key,value):
		partner_id=False
		self._cr.execute('''
			select id,regexp_matches('{0}',{1}) from res_partner
		'''.format(value,key))
		partners = self._cr.fetchone()
		if partners:						
			print ('partners' ,partners)
			partner_id=partners[0]		
		return partner_id
	

	def search_payment(self,partner_id,account_id,line):
		payment_id=False
		if account_id.internal_type =='receivable' and line.amount>0:
			payment_id=self.env['account.move.line'].search([('partner_id','=',partner_id),
															('account_id','=',account_id.id),
															('debit','>',0),
															('amount_residual','>',0),
															],limit=1)
			
# 		print ('payment_id ',payment_id)
		return payment_id	
	
	@api.model
	def _default_lines(self):
		context = self._context
		statement_ids = context.get('active_ids', [])
		active_model = context.get('active_model')
		statement_id = statement_ids[0]
		statement=self.env['account.bank.statement'].browse(statement_id)
		vals= []
		payment_id=False
		for line in statement.line_ids:
			if ((not line.journal_entry_ids) and (not line.account_id or not line.partner_id )):
				account_id=line.account_id and line.account_id
				partner_id=line.partner_id and line.partner_id.id 
				if not partner_id:
					if line.bank_account_id:
						partner_id=line.bank_account_id.partner_id.id
					elif line.partner_print:
# 						partners=self.env['res.partner'].search([('name','in',line.partner_print)])
						partner_id=self.search_partner('vat',line.partner_print)
						if not partner_id:
							partner_id=self.search_partner('vat_company',line.partner_print)
							if not partner_id:
								partner_id=self.search_partner('name',line.partner_print)
						if not partner_id:
							partner_id=self.search_partner('vat',line.name)
							if not partner_id:
								partner_id=self.search_partner('name',line.name)
					else:
						partner_id=self.search_partner('vat',line.name)
						if not partner_id:
							partner_id=self.search_partner('name',line.name)
				print ('line ',line)
				if not account_id and partner_id:
					account_id=self.env['res.partner'].browse(partner_id).property_account_receivable_id
				if partner_id and account_id:
					payment_id = self.search_payment(partner_id,account_id,line)
				vals.append((0,0,{
					'amount':line.amount,
					'account_id':account_id and account_id.id or False,
					'date':line.date,
					'name':line.name,
					'partner_id':partner_id,
					'line_id':line.id,
					'payment_id':payment_id
					}))
		return vals
#		 print ('statement_ids ',statement_ids)
	date=fields.Date('Date',)
	line_ids=fields.One2many('bank.payment.match.line', 'wizard_id', 'Lines',default=_default_lines)
	statement_id=fields.Many2one('account.bank.statement', 'Statement', required=True, ondelete='CASCADE')
# 	bank_lines=fields.Many2many('account.bank.statement.line', 'part_bank_rel','wizard_id', 'line_id','Product Moves')

	

	@api.model
	def default_get(self, fields):
		context = self._context
		res = super(bank_payment_match, self).default_get(fields)
		statement_ids = context.get('active_ids', [])
		active_model = context.get('active_model')
#		 print ('statement_ids ',statement_ids)
		if not statement_ids or len(statement_ids) != 1:
			# Partial statement Processing may only be done for one statement at a time
			return res
		assert active_model in ('account.bank.statement',), 'Bad context propagation'
		statement_id, = statement_ids
		if 'statement_id' in fields:
			res.update(statement_id=statement_id)
		if 'bank_lines' in fields:
			statement = self.env['account.bank.statement'].browse(statement_id)
			line_ids=[]
#			 moves = [self._partial_move_for(cr, uid, m) for m in statement.line_ids if m.state not in ('confirm')]
			for m in statement.line_ids:
				if not m.journal_entry_ids:
					line_ids.append(m.id)
		return res

	def confirm(self):
		account_statement = self.pool.get('account.bank.statement')
		account_statement_line = self.pool.get('account.bank.statement.line')
		partial = self
		amsl_vals = []
		for wizard_line in partial.line_ids:
			print ('wizard_line.line_id ',wizard_line.line_id)
			if wizard_line.line_id:
				if not wizard_line.line_id.account_id and wizard_line.account_id:
					wizard_line.line_id.write({'account_id':wizard_line.account_id.id})
				if not wizard_line.line_id.partner_id and wizard_line.partner_id:
					wizard_line.line_id.write({'partner_id':wizard_line.partner_id.id})
				
				if wizard_line.line_id.import_aml_ids:
					wizard_line.line_id.import_aml_ids.unlink()
				if wizard_line.payment_id:
					amsl_vals = [(0,0,{
#                                         'currency_amount':curr_amount,
                                        'import_aml_id':wizard_line.payment_id.id,
                                        'is_mnt':True,
#                                         'currency_id':currency_id,
                                            })]
					wizard_line.line_id.write({'import_aml_ids':amsl_vals})
                     
# 			wizard_line.button_validate_line()
#			 line_uom = wizard_line.product_uom
#			 move_id = wizard_line.move_id.id

		return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
