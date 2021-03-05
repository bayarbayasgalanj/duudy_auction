# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountCashDetails(models.TransientModel):
	_name = 'cash.details.wizard'
	_description = 'Open Cash Details Report'

	start_date = fields.Date(required=True, default=fields.Date.today())
	end_date = fields.Date(required=True, default=fields.Date.today())
# 	branch_id = fields.Many2one('res.branch', 'Салбар')
	journal_ids = fields.Many2many('account.journal', 'cash_journal_detail',
		default=lambda s: s.env['account.journal'].search([('type','=','cash')]))

	@api.onchange('start_date')
	def _onchange_start_date(self):
		if self.start_date and self.end_date and self.end_date < self.start_date:
			self.end_date = self.start_date

	@api.onchange('end_date')
	def _onchange_end_date(self):
		if self.end_date and self.end_date < self.start_date:
			self.start_date = self.end_date

	
	def get_move_line(self, ids):
		headers = [
		u'Огноо',
		u'ЖРНЛ',
		u'Partner',
		u'Дугаар',
		u'Хөдөлгөөн',
		u'Гүйлгээний нэр',
		u'Дебит',
		u'Кредит']
		datas = []
		i = 1
		report_id = self.browse(ids)

		account_ids = self.journal_ids.mapped('default_debit_account_id').ids +report_id.journal_ids.mapped('default_credit_account_id').ids
		# print 'report_id.journal_ids.ids',report_id.journal_ids.ids
		line_ids = self.env['account.move.line'].search([
			('journal_id','in',report_id.journal_ids.ids),
			('date','>=',report_id.start_date),
			('date','<=',report_id.end_date)
			])
		# print '\n\nline_ids\n\n',report_id.start_date,report_id.end_date,line_ids
		for line in line_ids:
			temp = [
			line.date or '', 
			line.journal_id.name or '', 
			line.partner_id.name or '', 
			line.ref or '', 
			line.move_id.name or '', 
			line.name or '', 
			"{0:,.2f}".format(line.debit),
			"{0:,.2f}".format(line.credit) 
			# '0' if line.debit==0 else str(line.debit), 
			# '0' if line.credit==0 else str(line.credit)
			]
			datas.append(temp)
			# i += 1
		res = {'header': headers, 'data':datas}
		return res
		
	
	def generate_report(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','cash.details.wizard')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','default')], limit=1)
		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))   

