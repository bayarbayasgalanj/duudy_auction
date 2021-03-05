# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
from odoo import tools

class account_partner_balance_view(models.Model):
	_name = "account.partner.balance.view"
	_description = "Partner ledger report"
	_auto = False
	_order = 'account_id'

	account_id = fields.Many2one('account.account', u'Данс', readonly=True)
	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	partner_id = fields.Many2one('res.partner', u'харилцагч', readonly=True)
	name = fields.Char(u'Гүйлгээний утга', readonly=True)
	debit = fields.Float(u'Дебит', readonly=True)
	credit = fields.Float(u'Кредит', readonly=True)
	move_id = fields.Many2one('account.move', u'Гүйлгээ', readonly=True)
	ref = fields.Char(u'Холбогдол', readonly=True)
	ref_name = fields.Char(u'Утга холбогдол', readonly=True)

	def init(self):
		tools.drop_view_if_exists(self.env.cr, 'account_partner_balance_view')
		self.env.cr.execute("""CREATE or REPLACE VIEW account_partner_balance_view as 
				select l.id as id, debit,credit,
					   account_id,l.date,move_id,l.partner_id,l.name,
						(select ref from account_move where id=l.move_id) as ref,
						CASE
							WHEN m.from_ref='t' THEN l.name 
							WHEN l.debit >0 THEN (select ref from account_move where id=l.move_id)
							ELSE l.name 
						END AS ref_name
				from account_move_line l left join account_move m on l.move_id=m.id 
					left join account_account a on l.account_id=a.id 
					left join account_account_type t on a.user_type_id=t.id
				where t.type in ('receivable','payable') and state='posted'
			""")

