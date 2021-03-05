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

class partial_bank_confirm_line(models.TransientModel):

	_name = "partial.bank.confirm.line"
	_description = "partial bank confirm line"
	_rec_name = 'line_id'
	account_id=fields.Many2one('account.account', string="Account", required=True, ondelete='CASCADE',readonly=True)
	amount=fields.Float("Quantity", required=True,readonly=True)
	line_id=fields.Many2one('account.bank.statement.line', "Move", ondelete='CASCADE',readonly=True)
	wizard_id=fields.Many2one('partial.bank.confirm', string="Wizard", ondelete='CASCADE',readonly=True)
	currency=fields.Many2one('res.currency', string="Currency", help="Currency in which Unit cost is expressed", ondelete='CASCADE',readonly=True)
	date=fields.Date('Date', required=True,readonly=True)


class partial_bank_confirm(models.TransientModel):
	
	_name = "partial.bank.confirm"
	_rec_name = 'statement_id'
	_description = "Partial bank statement confirm Wizard"

	date=fields.Date('Date',)
	line_ids=fields.One2many('partial.bank.confirm.line', 'wizard_id', 'Product Moves')
	statement_id=fields.Many2one('account.bank.statement', 'Statement', required=True, ondelete='CASCADE')
	bank_lines=fields.Many2many('account.bank.statement.line', 'part_bank_rel','wizard_id', 'line_id','Product Moves')


	@api.model
	def default_get(self, fields):
		context = self._context
		res = super(partial_bank_confirm, self).default_get(fields)
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
		for wizard_line in partial.bank_lines:
			wizard_line.button_validate_line()
#			 line_uom = wizard_line.product_uom
#			 move_id = wizard_line.move_id.id

		return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
