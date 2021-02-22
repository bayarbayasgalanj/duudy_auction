# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models


class AccountPaymentPivot(models.TransientModel):

	_name = 'pivot.report.payment.account'
	_description = "pivot report payment account"
	_order = 'user_id ASC'

	report_id = fields.Many2one(
		comodel_name='account.sale.payment.report',
		ondelete='cascade',
		index=True
	)

	# Data fields, used to keep link with real object
	partner_id = fields.Many2one(
		'res.partner',
		index=True
	)

	state = fields.Char(u'төлөв')
	type = fields.Char(u'төлсөн хэлбэр')
	padaan = fields.Char(u'Падааны дугаар')
	created_id = fields.Many2one(u'Оруулсан',
		'res.users',
		index=True
	)
	user_id = fields.Many2one(u'Борлуулагч',
		'res.users',
		index=True
	)
	date = fields.Date(u'Огноо')
	choose_type = fields.Char(u'Сонгосон хэлбэр')
	amount = fields.Float(u'дүн')
	get_amount = fields.Float(u'Авах дүн')
	payd_amount = fields.Float(u'Авсан дүн')
	zuruu = fields.Float(u'Зөрүү')
	prec = fields.Float(u'%')

class account_payment_report_pivot(models.Model):
	_name = "report.payment.account.pivot"
	_description = "Payment pivot"
	_auto = False
	_order = 'partner_id'

	
	report_id = fields.Many2one(
		comodel_name='account.sale.payment.report',
		ondelete='cascade',
		index=True
	)
	partner_id = fields.Many2one(
		'res.partner',
		index=True
	)
	
	state = fields.Char(u'төлөв')
	type = fields.Char(u'төлсөн хэлбэр')
	padaan = fields.Char(u'Падааны дугаар')
	created_id = fields.Many2one(u'Оруулсан',
		'res.users',
		index=True
	)
	user_id = fields.Many2one(u'Борлуулагч',
		'res.users',
		index=True
	)
	date = fields.Date(u'Огноо')
	choose_type = fields.Char(u'Сонгосон хэлбэр')
	amount = fields.Float(u'дүн')
	get_amount = fields.Float(u'Авах дүн')
	payd_amount = fields.Float(u'Авсан дүн')
	zuruu = fields.Float(u'Зөрүү')
	prec = fields.Float(u'%')
	
	def init(self):
		tools.drop_view_if_exists(self.env.cr, 'report_payment_account_pivot')
		self.env.cr.execute("""CREATE or REPLACE VIEW report_payment_account_pivot as 
				select min(id) as id, 
				sum(amount) as amount,
				sum(get_amount) as get_amount,
				sum(payd_amount) as payd_amount,
				sum(zuruu) as zuruu,
				sum(prec) as prec,
				partner_id,report_id,
				state,type,padaan,
				created_id,user_id
				from pivot_report_payment_account group by partner_id,report_id,
				state,type,padaan,
				created_id,user_id
			""")

