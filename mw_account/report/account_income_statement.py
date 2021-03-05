# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

class account_income_statement_view(models.Model):
	_name = "account.income.statement.view"
	_description = "Income statement report"
	_auto = False
	_order = 'account_id'

	account_id = fields.Many2one('account.account', u'Данс', readonly=True)
	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
# 	partner_id = fields.Many2one('res.partner', u'харилцагч', readonly=True)
	debit = fields.Float(u'Дебит', readonly=True)
	credit = fields.Float(u'Кредит', readonly=True)
	amount = fields.Float(u'Дүн', readonly=True)
# 	move_id = fields.Many2one('account.move', u'Гүйлгээ', readonly=True)
	type = fields.Char(u'Төрөл', readonly=True)
	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True)
	state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], default='posted', string='Status')
	move_id = fields.Many2one('account.move', u'Гүйлгээ', readonly=True)
	origin = fields.Char(u'Агуулах эх баримт', readonly=True)

	def init(self):
		tools.drop_view_if_exists(self.env.cr, 'account_income_statement_view')
# 		self.env.cr.execute("""CREATE or REPLACE VIEW account_income_statement_view as 
# 				select min(id) as id, sum(debit) as debit,sum(credit) as credit,
# 											account_id,date,move_id,partner_id 
# 				from account_move_line 
# 				group by account_id,date,move_id,partner_id
# 			""")
		self.env.cr.execute("""CREATE or REPLACE VIEW account_income_statement_view as 
				select min(l.id) as id,t.name as type,sum(debit) as debit,sum(credit) as credit,
								l.date,a.id as account_id, l.branch_id,m.state,
								(CASE WHEN t.type='income' then (sum(credit)-sum(debit)) ELSE -(sum(debit)-sum(credit)) end) as amount, 
								m.id as move_id, sp.origin as origin 
				 from account_move_line l 
				 	left join 
				 		account_move m on l.move_id=m.id 
				 	left join 
				 		account_account a on l.account_id=a.id 
				 	left join 
					 	account_account_type t on a.user_type_id=t.id 
					left join
						stock_move sm on sm.id=m.stock_move_id
					left join
						stock_picking sp on sm.picking_id=sp.id
				 where t.type in ('expense','income') 
				 group by t.name, l.date,t.name,a.id,t.type, l.branch_id,m.state,m.id, sp.origin
			""")


