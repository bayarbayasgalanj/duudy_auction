# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
from odoo import _, tools
import base64
from datetime import datetime, timedelta
from odoo import api, fields, models

class AccountStatementReport(models.TransientModel):
	_name = "account.statement.report"
	_description = "account statement report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	journal_ids = fields.Many2many('account.journal', string=u'Журнал', )
	
	def see_pivot_report(self):
		# GET views ID		
		mod_obj = self.env['ir.model.data']		
		search_res = mod_obj.get_object_reference('mw_account', 'account_statement_pivot_search')
		search_id = search_res and search_res[1] or False
		pivot_res = mod_obj.get_object_reference('mw_account', 'account_statement_pivot_report')
		pivot_id = pivot_res and pivot_res[1] or False

		domain = [('date','>=',str(self.date_start)),('date','<=',str(self.date_end))]
		if self.journal_ids:
			domain += [('statement_journal_id','in',self.journal_ids.mapped('id'))]
		# if self.warehouse_ids:
		# 	domain += [('warehouse_id','in',self.warehouse_ids.mapped('id'))]
		# if self.expense_type != 'all':
		# 	domain += [('expense_type','=',self.expense_type)]
		return {
			'name': '('+str(self.date_start)+' => '+str(self.date_end)+')',
			'view_type': 'form',
			'view_mode': 'pivot',
			'res_model': 'account.statement.pivot',
			'view_id': False,
			'views': [(pivot_id, 'pivot')],
			'search_view_id': search_id,
			'domain': domain,
			'type': 'ir.actions.act_window',
			'target': 'current'
		}
