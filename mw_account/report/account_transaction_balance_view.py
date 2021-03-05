# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models

class account_transaction_balance_view(models.Model):
	_name = "account.transaction.balance.view"
	_description = "Product both income expense report"
	_auto = False
	_order = 'account_id'

	account_id = fields.Many2one('account.account', u'Данс', readonly=True)
	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	partner_id = fields.Many2one('res.partner', u'харилцагч', readonly=True)
	debit = fields.Float(u'Дебит', readonly=True)
	credit = fields.Float(u'Кредит', readonly=True)
	move_id = fields.Many2one('account.move', u'Гүйлгээ', readonly=True)
	journal_id = fields.Many2one('account.journal', u'Журнал', readonly=True)
	net_move = fields.Float(u'Цэвэр гүйлгээ', readonly=True)
	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True)
	state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], default='posted', string='Status')
	origin = fields.Char(u'Холбогдол', readonly=True)
	analytic_account_id = fields.Many2one('account.analytic.account', u'Шинжилгээний данс',readonly=True)

	def init(self):
		tools.drop_view_if_exists(self.env.cr, 'account_transaction_balance_view')
		self.env.cr.execute("""CREATE or REPLACE VIEW account_transaction_balance_view as 
				select min(l.id) as id, 
				sum(debit) as debit,
				sum(credit) as credit,
				sum(debit)-sum(credit) as net_move,
				l.account_id,
				l.date,
				l.move_id,
				l.partner_id,
				l.journal_id,
				l.branch_id,
				m.state,
				m.invoice_origin as origin ,
				l.analytic_account_id
				from account_move_line l left join account_move m on l.move_id=m.id
				group by account_id,l.date,l.move_id,l.partner_id,l.journal_id,l.branch_id,m.state,m.invoice_origin,l.analytic_account_id
			""")

