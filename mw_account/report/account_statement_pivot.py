# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class account_statement_pivot(models.Model):
	_name = "account.statement.pivot"
	_description = "Account cash pivot"
	_auto = False
	_order = 'date'

	id = fields.Many2one('account.bank.statement.line', u'ID', readonly=True)
	balance_start = fields.Float(u'Нээлтийн үлдэгдэл', readonly=True, group_operator='avg')
	balance_end = fields.Float(u'Тооцоолсон баланс', readonly=True, group_operator='avg')
	balance_end_real = fields.Float(u'Төгсгөлийн баланс', readonly=True, group_operator='avg')
	amount_expense = fields.Float(u'Зарлага', readonly=True,)
	amount_income = fields.Float(u'Орлого', readonly=True,)
	date = fields.Date(u'Огноо', readonly=True, help=u"Хөдөлгөөн хийсэн огноо")
	account_id = fields.Many2one('account.account', u'Харьцах данс', readonly=True)
	statement_id = fields.Many2one('account.bank.statement', u'Кассын дугаар', readonly=True)
	statement_journal_id = fields.Many2one('account.journal', u'Кассын журнал', readonly=True,)
	ref = fields.Char( u'Дугаар', readonly=True)
	name = fields.Char(u'Утга', readonly=True,)
	journal_id = fields.Many2one('account.journal', u'Журнал', readonly=True,)
	partner_id = fields.Many2one('res.partner', u'Харилцагч', readonly=True,)
	statement_name = fields.Char(u'Касс/Харилцах дугаар', readonly=True,)
	# 'difference = fields.float(u'Зөрүү', readonly=True,),
	state = fields.Selection([
		('draft', u'Ноорог'),
		('confirm', u'Баталсан'),], 
		string=u'Төлөв', readonly=True, 
	)
		


	def init(self):
		
		tools.drop_view_if_exists(self.env.cr, 'account_statement_pivot')
		self.env.cr.execute("""CREATE or REPLACE VIEW account_statement_pivot as
		SELECT  
				coalesce(id) as id,
				amount_expense,amount_income, date, name, ref,
				journal_id, partner_id, account_id, state,statement_id, balance_start,
				balance_end, balance_end_real, statement_name, statement_journal_id 
				from 
                    (SELECT 
                    bsl.id as id,
                    bsl.amount as amount_expense,
                    0 as amount_income,
                    --bsl.amount_untaxed as amount_untaxed,
                    --bsl.amount_tax as amount_tax,
                    bsl.date as date,
                    bsl.name as name,
                    bsl.ref as ref,
                    bsl.journal_id as journal_id,
                    bsl.partner_id as partner_id,
                    bsl.account_id as account_id,
                    bs.state as state,
                    bsl.statement_id as statement_id,
                    bs.balance_start as balance_start,
                    bs.balance_end as balance_end,
                    bs.balance_end_real as balance_end_real,
                    bs.name as statement_name,
                    --bs.difference as difference,
                    bs.journal_id as statement_journal_id
                    --bs.total_entry_encoding as total_entry_encoding
                    FROM account_bank_statement_line bsl
                    LEFT JOIN account_bank_statement bs ON bsl.statement_id=bs.id
                    where bsl.amount::text ilike '-%'
                    
                    UNION ALL
                    SELECT 
                    bsl.id as id,
                    0 as amount_expense,
                    bsl.amount as amount_income,
                    --bsl.amount_untaxed as amount_untaxed,
                    --bsl.amount_tax as amount_tax,
                    bsl.date as date,
                    bsl.name as name,
                    bsl.ref as ref,
                    bsl.journal_id as journal_id,
                    bsl.partner_id as partner_id,
                    bsl.account_id as account_id,
                    bs.state as state,
                    bsl.statement_id as statement_id,
                    bs.balance_start as balance_start,
                    bs.balance_end as balance_end,
                    bs.balance_end_real as balance_end_real,
                    bs.name as statement_name,
                    --bs.difference as difference,
                    bs.journal_id as statement_journal_id
                    --bs.total_entry_encoding as total_entry_encoding
                    FROM account_bank_statement_line bsl
                    LEFT JOIN account_bank_statement bs ON bsl.statement_id=bs.id
                    where bsl.amount::text not ilike '-%'
                    ) 
                    as tt
                    order by date 
		""")
