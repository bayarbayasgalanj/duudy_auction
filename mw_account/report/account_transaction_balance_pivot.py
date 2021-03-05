# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models


class TransferBalanceReportAccountPivot(models.TransientModel):

	_name = 'pivot.report.transfer.balance.account'
	_description = "pivot report transfer balance account"
	_order = 'code ASC'

	report_id = fields.Many2one(
		comodel_name='account.transaction.balance.report.new',
		ondelete='cascade',
		index=True
	)

	# Data fields, used to keep link with real object
	account_id = fields.Many2one(
		'account.account',
		index=True
	)
	branch_id = fields.Many2one(
		'res.branch',
		index=True
	)

	# Data fields, used for report display
#	 code = fields.Char()
#	 name = fields.Char()
	initial_debit = fields.Float(digits=(16, 2))
	initial_credit = fields.Float(digits=(16, 2))
	debit = fields.Float(digits=(16, 2))
	credit = fields.Float(digits=(16, 2))
	final_debit = fields.Float(digits=(16, 2))
	final_credit = fields.Float(digits=(16, 2))

class account_transaction_balance_pivot(models.Model):
	_name = "account.transaction.balance.pivot"
	_description = "Guilgee balance pivot"
	_auto = False
	_order = 'account_id'

	account_id = fields.Many2one('account.account', u'Данс', readonly=True)
# 	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
# 	partner_id = fields.Many2one('res.partner', u'харилцагч', readonly=True)
	initial_debit = fields.Float(u'Эхний дебит', readonly=True)
	initial_credit = fields.Float(u'Эхний кредит', readonly=True)
	debit = fields.Float(u'Дебит', readonly=True)
	credit = fields.Float(u'Кредит', readonly=True)
	final_debit = fields.Float(u'Эцсийн дебит', readonly=True)
	final_credit = fields.Float(u'Эцсийн кредит', readonly=True)
# 	move_id = fields.Many2one('account.move', u'Гүйлгээ', readonly=True)
# 	journal_id = fields.Many2one('account.journal', u'Журнал', readonly=True)
# 	net_move = fields.Float(u'Цэвэр гүйлгээ', readonly=True)
# 	branch_id = fields.Many2one('res.branch', u'Салбар', readonly=True)
# 	state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], default='posted', string='Status')
	report_id = fields.Many2one(
		comodel_name='account.transaction.balance.report.new',
		ondelete='cascade',
		index=True
	)
	def init(self):
		tools.drop_view_if_exists(self.env.cr, 'account_transaction_balance_pivot')
		self.env.cr.execute("""CREATE or REPLACE VIEW account_transaction_balance_pivot as 
				select min(id) as id, 
				sum(initial_debit) as initial_debit,
				sum(initial_credit) as initial_credit,
				sum(debit) as debit,
				sum(credit) as credit,
				sum(final_debit) as final_debit,
				sum(final_credit) as final_credit,
				account_id,report_id
				from pivot_report_transfer_balance_account group by account_id,report_id
			""")

