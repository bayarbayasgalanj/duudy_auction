# -*- coding: utf-8 -*-

import time
from odoo.exceptions import UserError
from odoo import _, tools
from datetime import datetime, timedelta
from odoo import api, fields, models

class AccountISReport(models.TransientModel):
	_name = "account.income.statement.view.wizard"
	_description = "account income statement view wizard"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
	state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], default='posted', string='Status')

	
	def open_analyze_view(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		

			# INIT query
			search_res = mod_obj.get_object_reference('mw_account', 'account_income_statement_view_search')
			search_id = search_res and search_res[1] or False
			pivot_res = mod_obj.get_object_reference('mw_account', 'account_income_statement_view_pivot2')
			pivot_id = pivot_res and pivot_res[1] or False
			return {
				'name': _('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'account.income.statement.view',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('date','>=',self.date_start),
						   ('date','<=',self.date_end),
 						 ('account_id.company_id','=',self.company_id.id),
 						 ('state','=',self.state),
						   ],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

