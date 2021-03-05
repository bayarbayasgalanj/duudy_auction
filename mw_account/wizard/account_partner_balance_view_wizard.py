# -*- coding: utf-8 -*-

import time
from odoo.exceptions import UserError
from odoo import _, tools
from datetime import datetime, timedelta
from odoo import api, fields, models

class AccountPartnerBalanceReport(models.TransientModel):
	_name = "account.partner.balance.view.wizard"
	_description = "account partner balance view wizard"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	partner_id = fields.Many2one('res.partner', string=u'Харилцагч',required=True, )

	def _recursive(self, temp_ids, cat_id):
		cat = self.env['product.category'].sudo().search([('id','=',cat_id)], limit=1)
		temp_ids.append(cat.id)

		c_ids = [c.id for c in cat.child_id]
		if not c_ids: 
			return True
		for cid in c_ids:
			self._recursive(temp_ids, cid)
		return False

	def open_analyze_view(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		
			# INIT query
			# Орлого зарлага хамтдаа
			search_res = mod_obj.get_object_reference('mw_account', 'account_partner_balance_view_search')
			search_id = search_res and search_res[1] or False
			pivot_res = mod_obj.get_object_reference('mw_account', 'account_partner_balance_view_pivot2')
			pivot_id = pivot_res and pivot_res[1] or False

			return {
				'name': _('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'account.partner.balance.view',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('date','>=',self.date_start),
						   ('date','<=',self.date_end),
						   ('partner_id','=',self.partner_id.id),
						   ],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

