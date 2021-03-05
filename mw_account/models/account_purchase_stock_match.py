# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from io import BytesIO
import base64
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError,Warning
# import urllib2
import urllib.request as urllib2

import logging
_logger = logging.getLogger(__name__)

class AccountPurchaseStock(models.Model):
	_name = "account.purchase.stock.match"
	_description = "account purchase stock match"

	name = fields.Text('Тайлбар')

	start_date = fields.Date('Эхлэх огноо', default=fields.Date.context_today, required=True)
	end_date = fields.Date('Дуусах огноо', default=fields.Date.context_today, required=True)
	state = fields.Selection([('draft','Ноорог'),('done','Дууссан')], 'Төлөв', default='draft')
	line_ids = fields.One2many('account.purchase.stock.match.line', 'parent_id', 'Мөр')
#	 account_line_ids = fields.One2many('stock.account.move.update.line','parent_id', 'Lines',copy=False)
	aml_ids = fields.Many2many('account.move.line','update_purchase_stock_move_rel','price_id','aml_id',u'ШИнэчлэгдсэн гүйлгээнүүд',copy=False)
	state = fields.Selection([('draft','Ноорог'),('done','Дууссан')], 'Төлөв', default='draft')

	inv_line_ids = fields.One2many('account.purchase.stock.match.invoice.line', 'parent_id', 'Мөр')


	def action_done(self):
		self.write({'state':'done'})
		partner_ids = [self.branch_id.manager_id.partner_id.id]


	def action_draft(self):
		self.write({'state':'draft'})


	def calc_dict(self):
		dic=False
		int_qty=0
		int_price=0
		am_obj = self.env['purchase.order.line']
		product_obj = self.env['product.product']
		technic_obj = self.env['technic.equipment']
		line_obj = self.env['account.purchase.stock.match.line']
		categ_obj = self.env['product.category']

#		 query1 = """
#				 select sm.purchase_line_id,sm.id as sm_id,
#						 date,state,product_qty,price_unit,picking_id,product_id,
#						 product_uom_qty from stock_move sm
#				 where sm.purchase_line_id notnull --and state='done';
#				 and sm.date between '%s' and '%s' and sm.state='done'
#			 """
		query1 = """
				select sum(product_qty) as product_qty,purchase_line_id,mdate as date,product_id,sum(abs(price_unit))/count(sm_id) as price_unit from (select sm.purchase_line_id,sm.id as sm_id,
						date,state,product_qty,price_unit,picking_id,product_id,
						product_uom_qty,to_char(date ,'YYYY/MM') mdate from stock_move sm
				where sm.purchase_line_id notnull
				and sm.date between '%s' and '%s' and sm.state='done'
				) as foo group by mdate,purchase_line_id,mdate,product_id
				--and state='done';
			"""

		query1 = query1 % (self.start_date,self.end_date)
#		 print 'query1 ',query1
		self.env.cr.execute(query1)
		query_result = self.env.cr.dictfetchall()
		if query_result:
			for re in query_result:
#				 print 're ',re
				query2 = """
						select il.id as il_id,quantity,invoice_id,i.date_invoice,i.state,il.price_unit,
						il.price_unit,price_subtotal,price_subtotal/quantity as unit
							from account_invoice_line il left join account_invoice i on i.id=il.invoice_id
							where purchase_line_id= %s
					"""
				query2 = query2 % (re['purchase_line_id'])
#				 print 'query2 ',query2
				self.env.cr.execute(query2)
				query_result2 = self.env.cr.dictfetchall()
#				 print 'query_result2 ',query_result2
				unit=0
				qty=0
				date_invoice=''
				state=''
				il_id=False
				invoice_id=False
				for r in query_result2:
					unit+=r['unit']
					qty+=r['quantity']
					date_invoice=r['date_invoice']
					state=r['state']
					il_id=r['il_id']
					invoice_id=r['invoice_id']

#							 if re['technic_id']:
#								 technic_id = technic_obj.browse(re['technic_id'])
# #							 print 'conf_acc ',conf_acc
#				 date_invoice<> or
				if not query_result2 or re['product_qty']!=qty \
					or not (date_invoice and date_invoice.split('-')[0]==re['date'].split('/')[0] and date_invoice.split('-')[1]==re['date'].split('/')[1]):# or state not in ('open','paid'):
#					 print 'query_result2 ',query_result2
#					 print 're[] ',re['product_qty']
#					 print 'qty ',qty
#					 print 'state ',state
					if re['product_id']:
						product_id = product_obj.browse(re['product_id'])
					if re['purchase_line_id']:
						pol_id = am_obj.browse(re['purchase_line_id'])
					dic={
									'parent_id':self.id,
									'product_id':product_id.id,
									'stock_unit':re['price_unit'],
									'invoice_unit':unit,
									'invoice_line_id':il_id,
									'invoice_id':invoice_id,
#									 'picking_id':re['picking_id'],
									'line_id':re['purchase_line_id'],
#									 'stock_move_id':re['sm_id'],
									'po_id':pol_id.order_id.id,

									'stock_qty':re['product_qty'],
									'stock_date':re['date'].split('/')[0]+'-'+re['date'].split('/')[1]+'-01',
									'invoice_qty':qty,
									'invoice_date':date_invoice,
							}
					line_obj.create(dic)

		return dic


	def action_import(self):
#		 if self.line_ids:
#			 for line in self.line_ids:
#		 line_obj = self.env['account.purchase.stock.match.line']
		dic=self.calc_dict()
#		 line_obj.create(dic)
		return True



	def calc_dict_inv(self):
		dic=False
		int_qty=0
		int_price=0
		am_obj = self.env['purchase.order.line']
		product_obj = self.env['product.product']
		technic_obj = self.env['technic.equipment']
		line_obj = self.env['account.purchase.stock.match.invoice.line']
		categ_obj = self.env['product.category']
#
#		 query1 = """
#				 select invoice_id,l.quantity,i.date_invoice,i.state,purchase_line_id,product_id,
#						 case when quantity<>0
#						 then
#						 price_subtotal/quantity
#						 else 0 END as unit,
#						 --0 as unit,
#						 l.id as line_id
#							 from account_invoice_line l left join
#								 account_invoice i on l.invoice_id=i.id left join
#								 product_product p on l.product_id=p.id left join
#								 product_template t on p.product_tmpl_id=t.id
#							 where i.date_invoice between '%s' and '%s' and purchase_line_id notnull and t.type='product'
#			 """
#

		query1 = """
				select sum(l.quantity) as quantity,purchase_line_id,
										sum(l.price_unit)/count(l.id)  as unit,product_id
										--, l.id as line_id
											from account_invoice_line l left join
												account_invoice i on l.invoice_id=i.id left join
												product_product p on l.product_id=p.id left join
												product_template t on p.product_tmpl_id=t.id
--											where i.date_invoice between '2019-01-01' and '2019-01-31'
--											and purchase_line_id notnull and t.type='product'
											where i.date_invoice between '%s' and '%s' and purchase_line_id notnull and t.type='product'
											group by purchase_line_id ,product_id
			"""

#		 query1 = """
#				 select sum(product_qty) as product_qty,purchase_line_id,mdate as date,product_id,sum(abs(price_unit))/count(sm_id) as price_unit from (select sm.purchase_line_id,sm.id as sm_id,
#						 date,state,product_qty,price_unit,picking_id,product_id,
#						 product_uom_qty,to_char(date ,'YYYY/MM') mdate from stock_move sm
#				 where sm.purchase_line_id notnull
#				 and sm.date between '%s' and '%s' and sm.state='done'
#				 ) as foo group by mdate,purchase_line_id,mdate,product_id
#				 --and state='done';
#			 """

		query1 = query1 % (self.start_date,self.end_date)
#		 print 'query1 ',query1
		self.env.cr.execute(query1)
		query_result = self.env.cr.dictfetchall()
		if query_result:
			for re in query_result:
#				 print 're ',re
#				 query2 = """
#						 select sum(product_qty) as product_qty,purchase_line_id,mdate as date,product_id,sum(abs(price_unit))/count(sm_id) as price_unit from (select sm.purchase_line_id,sm.id as sm_id,
#								 date,state,product_qty,price_unit,picking_id,product_id,
#								 product_uom_qty,to_char(date  + interval '8 hour' ,'YYYY/MM') mdate from stock_move sm
#						 where sm.purchase_line_id= %s
#						 and sm.state='done'
#						 and sm.date between '%s' and '%s'
#						 ) as foo group by mdate,purchase_line_id,mdate,product_id
#					 """
				query2 = """
							select sum(product_qty) as product_qty,purchase_line_id,mdate as date,product_id,
							sum(abs(price_unit))/count(sm_id) as price_unit from
							(select sm.purchase_line_id,sm.id as sm_id,date,state,
								 case when location_dest_id=8
								 then -product_qty
								 else product_qty end as product_qty
							 ,price_unit,picking_id,product_id,product_uom_qty,to_char(date  + interval '8 hour' ,'YYYY/MM') mdate
												 from stock_move sm
													where sm.purchase_line_id= %s
													and sm.state='done'
													and sm.date between '%s' and '%s'
													) as foo group by mdate,purchase_line_id,mdate,product_id
					"""
				query2 = query2 % (re['purchase_line_id'],self.start_date,self.end_date)
#				 print 'query2 ',query2
				self.env.cr.execute(query2)
				query_result2 = self.env.cr.dictfetchall()
#				 print 'query_result2 ',query_result2
				unit=0
				qty=0
				date_invoice=''
				state=''
				il_id=False
				invoice_id=False
				for r in query_result2:
					unit=r['price_unit']
					qty+=r['product_qty']
#					 date_invoice=r['date']
#					 state=r['state']
#					 il_id=r['il_id']
#					 invoice_id=r['invoice_id']

#							 if re['technic_id']:
#								 technic_id = technic_obj.browse(re['technic_id'])
# #							 print 'conf_acc ',conf_acc
#				 date_invoice<> or
#				 print 'date_invoice ',date_invoice
#				 if not query_result2 or re['quantity']<>qty \
#					 or not (date_invoice and re['date_invoice'].split('-')[0]==date_invoice.split('/')[0] and re['date_invoice'].split('-')[1]==date_invoice.split('/')[1]):# or state not in ('open','paid'):
				if not query_result2 or re['quantity']!=qty:# or state not in ('open','paid'):
					type='qty'
					date=''
					if not query_result2:
						type='no_stock'
						date=self.end_date
#					 print 'query_result2 ',query_result2
#					 print 're[] ',re['product_qty']
#					 print 'qty ',qty
#					 print 'state ',state
					if re['product_id']:
						product_id = product_obj.browse(re['product_id'])
					if re['purchase_line_id']:
						pol_id = am_obj.browse(re['purchase_line_id'])
					dic={
									'parent_id':self.id,
									'product_id':product_id.id,
									'stock_unit':unit,
									'invoice_unit':re['unit'],
#									 'invoice_line_id':re['line_id'],
#									 'invoice_id':re['invoice_id'],
#									 'picking_id':re['picking_id'],
									'line_id':re['purchase_line_id'],
#									 'stock_move_id':re['sm_id'],
									'po_id':pol_id.order_id.id,

									'stock_qty':qty,
									'stock_date':date,#зөвхөн тухайн сард тоо нь тулсаныг шалгах date_invoice and (date_invoice.split('/')[0]+'-'+date_invoice.split('/')[1]+'-01') or False,
									'invoice_qty':re['quantity'],
									'type':type,
									'invoice_date':self.end_date,#re['date_invoice'],
							}
					line_obj.create(dic)

		return dic


	def action_calc_inv(self):
#		 if self.line_ids:
#			 for line in self.line_ids:
#		 line_obj = self.env['account.purchase.stock.match.line']
		dic=self.calc_dict_inv()
#		 line_obj.create(dic)
		return True


	def action_update(self):
		return True
#		 if self.line_ids:
#			 for line in self.line_ids:
#				 if line.aml_debit_id and line.aml_debit_id.debit>0 and line.acc_config_id:
#						 self.env.cr.execute("update account_move_line set account_id ={0} where id= {1} ".format(line.acc_config_id.id,line.aml_debit_id.id))
#						 self.env.cr.execute("insert into update_price_stock_move_rel(price_id,aml_id) values({0},{1})".format(self.id,line.aml_debit_id.id))
#				 else:

class StockAccountUpdateLine(models.Model):
	_name = 'account.purchase.stock.match.line'
	_description = u'мөр'

	parent_id = fields.Many2one('account.purchase.stock.match', 'Толгой', ondelete='cascade')
	product_id = fields.Many2one('product.product', 'Product')
	stock_unit = fields.Float('Stock unit')
	invoice_unit = fields.Float('Invoice unit')
#	 acc_debit_id = fields.Many2one('account.account', 'Debit account')
#	 acc_credit_id = fields.Many2one('account.account', 'Credit account')
	stock_qty = fields.Float('Stock qty')
	invoice_qty = fields.Float('Invoice qty')

	invoice_date = fields.Date('Invoice date')
	stock_date = fields.Date('Stock date')

	invoice_line_id = fields.Many2one('account.move.line', 'Invoice line')#invoice
	invoice_id = fields.Many2one('account.move', 'Invoice')#invoice
	picking_id = fields.Many2one('stock.picking', 'picking')
	stock_move_id = fields.Many2one('stock.move', 'Stock')
	line_id = fields.Many2one('purchase.order.line', 'Purchase line')
	po_id = fields.Many2one('purchase.order', 'PO')



class StockAccountUpdateInvoiceLine(models.Model):
	_name = 'account.purchase.stock.match.invoice.line'
	_description = u'мөр'

	parent_id = fields.Many2one('account.purchase.stock.match', 'Толгой', ondelete='cascade')
	product_id = fields.Many2one('product.product', 'Product')
	stock_unit = fields.Float('Stock unit')
	invoice_unit = fields.Float('Invoice unit')
#	 acc_debit_id = fields.Many2one('account.account', 'Debit account')
#	 acc_credit_id = fields.Many2one('account.account', 'Credit account')
	stock_qty = fields.Float('Stock qty')
	invoice_qty = fields.Float('Invoice qty')

	invoice_date = fields.Date('Invoice date')
	stock_date = fields.Date('Stock date')

	invoice_line_id = fields.Many2one('account.move.line', 'Invoice line')#invoice
	invoice_id = fields.Many2one('account.move', 'Invoice')#invoice
	picking_id = fields.Many2one('stock.picking', 'picking')
	stock_move_id = fields.Many2one('stock.move', 'Stock')
	line_id = fields.Many2one('purchase.order.line', 'Purchase line')
	po_id = fields.Many2one('purchase.order', 'PO')
	type = fields.Selection([('qty','Тоо зөрсөн'),('no_stock','Гүйлгээгүй')], 'Төрөл', default='qty')

