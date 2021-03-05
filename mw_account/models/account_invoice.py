# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round


class account_invoice(models.Model):
	_inherit = 'account.move'

#	 category_id = fields.Many2many('res.partner.category','account_invoice_partner_categ_rel', 'invoice_id', 'categ_id',related='partner_id.category_id', store=True)
	sign_id = fields.Many2one('print.invoice.sign')


#	 language_ids = fields.Many2many(related='website_id.language_ids', relation='res.lang')


	@api.model
	def _get_bank_accounts(self):
		'''Хэвлэхэд банкны данс
		'''
		bank_vals = []
		company_id = self.company_id
		bank_data = self.env['res.partner.bank'].search([('partner_id', '=', company_id.partner_id.id),
														 ('is_print','=',True)])
		for data in bank_data:
			bank_vals.append({
				'name': data.bank_id.name,
				'acc_number': data.acc_number,
				'curr': data.currency_id and data.currency_id.name or 'MNT',
			})
		return bank_vals




	@api.constrains('name', 'journal_id', 'state')
	def _check_unique_sequence_number(self):
		moves = self.filtered(lambda move: move.state == 'posted')
		if not moves:
			return

		self.flush()

		# /!\ Computed stored fields are not yet inside the database.
		self._cr.execute('''
			SELECT move2.id
			FROM account_move move
			INNER JOIN account_move move2 ON
				move2.name = move.name
				AND move2.journal_id = move.journal_id
				AND move2.type = move.type
				AND move2.id != move.id
			WHERE move.id IN %s AND move2.state = 'posted'
		''', [tuple(moves.ids)])
		res = self._cr.fetchone()
		if res:
			raise ValidationError(_(u'Posted journal entry must have an unique sequence number per company.{0}'.format(res)))

class res_partner_bank(models.Model):
	_inherit = 'res.partner.bank'

	is_print = fields.Boolean('View on invoice?')



class print_invoice_sign(models.Model):
	_name = 'print.invoice.sign'
	_description = "print invoice sign"

	name = fields.Char('Name')
	desc = fields.Html('Desc')
