# -*- encoding: utf-8 -*-
############################################################################################
#
#    Managewall-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2017 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#    $Id:  $
#
#    Менежволл-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
#
#
############################################################################################

from datetime import timedelta
from lxml import etree

from io import BytesIO
import base64
import time
import datetime
from datetime import datetime

import xlwt
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
import logging
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
from odoo.tools import float_is_zero, float_compare, pycompat

_logger = logging.getLogger(__name__)

class account_payment_report(models.TransientModel):
    
    _name = "account.sale.payment.report"
    _description = "Account Payment Report"
    
    date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
    date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User',  default=lambda self: self.env.user.id)#readonly=True,
    branch_ids = fields.Many2many('res.branch', string='Branches')
    user_ids = fields.Many2many('res.users', string='Users')

    user_get_so = fields.Boolean(u'Жолоочийн тохиргоог SO с авах?')

    def _print_report(self, data):
        # print "guilgee balancee   23165465464654654654",data
        data['form'].update(self._build_contexts(data))
        return self._make_excel(data)

    
    def _compute_partner_user_so_payment(self,data,invoice_ids):
#         data={'date':'2018-09-10','partner_id':self.partner_id.id}
#         if sos:
#             for so in sos:
#                 invoice_id = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
#                 if not invoice_ids:
#                     invoice_ids=invoice_id
#                 else:
#                     invoice_ids+=invoice_id
#        print 'invoice_ids22 ',invoice_ids

        aml_obj = self.env['account.move.line']
        payment_obj = self.env['account.payment']
        so_obj = self.env['sale.order']
        payments_all=[]
        so_amount=0
        so_ids=[]
        users=[]
        if self.user_ids.ids:
            query = """
                    select rel.user_id from res_partner_route rpr 
                                    left join user_route_rel rel on rel.route_id=rpr.id 
                                where driver_id in ({0}) group by user_id  
                """.format(','.join(map(str,self.user_ids.ids)))
#                         print 'query11 ',query
            self.env.cr.execute(query)
            query_result = self.env.cr.dictfetchall()                        
#                         print 'query_result ',query_result
            for r in query_result:
                users.append(r['user_id'])     
            if len(users)==0:
                users=self.user_ids.ids
                
        for inv in invoice_ids:
#             for pay in  inv.payment_move_line_ids.filtered(lambda r: 
#                                                                r.date >=self.date_from and
#                                                                r.date<=self.date_to):
            pay_term_line_ids = inv.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable'))
            partials = pay_term_line_ids.mapped('matched_debit_ids') + pay_term_line_ids.mapped('matched_credit_ids')
            for partial in partials:
#                 print ('partial.debit_move_id1 ',partial.debit_move_id)#Авлага
#                 print ('partial.credit_move_id ',partial.credit_move_id)#Төлөлт
                counterpart_lines = partial.debit_move_id + partial.credit_move_id#Төлөлт болон авлага
                counterpart_line = counterpart_lines.filtered(lambda line: line not in inv.line_ids)#Төлөлт
#                 print ('counterpart_lines ',counterpart_lines)
#                 print ('counterpart_line ',counterpart_line)
#                 if foreign_currency and partial.currency_id == foreign_currency:
#                     amount = partial.amount_currency
#                 else:
                amount = partial.company_currency_id._convert(partial.amount, inv.currency_id, inv.company_id, inv.date)
                if float_is_zero(amount, precision_rounding=inv.currency_id.rounding):
                    continue

                #Нэг төлөлтөөр олон нэхэмжлэхийн төлөлт хийсэн бол
                payment_currency_id = False
#                 if inv.type in ('out_invoice', 'in_refund'):
# #                     amount=0
# #                     for p in pay.matched_debit_ids:
# #                         if p.debit_move_id in inv.move_id.line_ids:
# # #                             if len(inv.payment_move_line_ids)>1:
# #                             if pay.payment_id and pay.payment_id.is_more:
# #                                 amount+=p.credit_move_id.credit
# #                             else :
# #                                 amount+=p.amount-pay.payment_id.discount or 0
#                     amount_currency = sum(
#                         [p.amount_currency for p in pay.matched_debit_ids if p.debit_move_id in inv.move_id.line_ids])
#                     if pay.matched_debit_ids:
#                         payment_currency_id = all([p.currency_id == pay.matched_debit_ids[0].currency_id for p in
#                                                    pay.matched_debit_ids]) and pay.matched_debit_ids[
#                                                   0].currency_id or False
#                     if inv.partner_id.id==3263:
#                         print 'amount ',amount
#                         print 'pay.matched_debit_ids ',pay.matched_debit_ids
#                         print 'inv.move_id.line_ids ',inv.move_id.line_ids
#                 elif inv.type in ('in_invoice', 'out_refund'):
#                     amount = sum(
#                         [p.amount for p in pay.matched_credit_ids if p.credit_move_id in inv.move_id.line_ids])
#                     amount_currency = sum([p.amount_currency for p in pay.matched_credit_ids if
#                                            p.credit_move_id in inv.move_id.line_ids])
#                     if pay.matched_credit_ids:
#                         payment_currency_id = all([p.currency_id == pay.matched_credit_ids[0].currency_id for p in
#                                                    pay.matched_credit_ids]) and pay.matched_credit_ids[
#                                                   0].currency_id or False
                # get the payment value in invoice currency
#                 if payment_currency_id and payment_currency_id == inv.currency_id:
#                     amount_to_show = amount_currency
#                 else:
#                     amount_to_show = pay.company_id.currency_id.with_context(date=inv.date).compute(amount,
#                                                                                                             inv.currency_id)
#                 if float_is_zero(amount_to_show, precision_rounding=inv.currency_id.rounding):
#                     continue
#                 print 'payments_all 1 ',payments_all
                order_id=False
                for l in inv.invoice_line_ids:
                    for sol in l.sale_line_ids:
                        order_id=sol.order_id
#                 print ('order_id ',order_id)
                if not order_id:
                    refunds = so_obj.search([('name', 'like', inv.invoice_origin), ('company_id', '=', inv.company_id.id)])
                    if refunds:
                        order_id=refunds
#                     invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
#                     print 'invoice_ids ',invoice_ids
#                         discount+=discount_percent_contract+discount_percent_coupon+discount_percent_contract_month

#                         print 'order_id ',order_id
                #2 төлөлт хийсэн бол нийт дүнгээрээ 2 ирж байна
#                         res.append({'so_id':order_id,'amount':(m.debit_move_id.invoice_id.amount_total-m.debit_move_id.invoice_id.residual)})
#                 res.append({'so_id':order_id,'amount':(m.amount)})
#                 if pay:
#                     so_amount+=inv.amount_total
                state='service'
                if inv.date<data['date_from']:
                    state=u'Дамнасан'
                elif inv.amount_residual==0:
#                 elif round(partial.debit_move_id.amount_residual,0)==0:
                    state=u'Хаагдсан'
                cash_amount=0
#                 print 'pay ',pay
                payments_dic=False
#                 print ('counterpart_line ',counterpart_line)
                pay=counterpart_line
                if pay.journal_id.type=='cash':
                    cash_amount+=pay.credit
                amount_to_show=amount
                if order_id:
                    discount=order_id.total_discount/order_id.main_amount_total*100
                    if order_id.id in so_ids:
                        so_amount = 0
                        inv_amount = 0
                    else:
                        so_amount = order_id.main_amount_total
                        inv_amount = inv.amount_total
                        so_ids.append(order_id.id)
                    if self.user_get_so:
#                         if query_result:
                        if order_id.driver_id and order_id.driver_id.id in (self.user_ids.ids): 
#                             print 'pay.credit---------: ',pay.credit             
                            payments_dic={
#                                 'amount':pay.credit,
                                'amount':amount_to_show,
#                                'move_ids':[pay.id],
                               'partner_name':pay.partner_id.name,
                               'type':pay.journal_id.type,
#                                'journal_name':pay.journal_id.short_name,
                                'journal_name':pay.journal_id.name,
                               'payment_type':order_id.payment_type,
                               'so_id':order_id.id,
                               'so_name':order_id.name,
                               'so_amount':so_amount,
                               'inv_amount':inv_amount,
                               'residual_amount':inv.amount_residual,
                               'created':pay.create_uid.name,
                               'state':state,
                               'discount':discount,
                               'user':order_id.user_id.name,
                               'date':pay.date,
                               'cash_amount':cash_amount,
                               'partner_id':pay.partner_id.id,
                               'created_id':pay.create_uid.id,
                               'user_id':order_id.user_id.id,
                               }
#                         else:
#                                 payments_dic={'amount':pay.credit,
#     #                                'move_ids':[pay.id],
#                                    'partner_name':pay.partner_id.name,
#                                    'type':pay.journal_id.type,
#                                    'journal_name':pay.journal_id.short_name,
#                                    # 'journal_name':pay.journal_id.name,
#                                    'payment_type':order_id.payment_type,
#                                    'so_id':order_id.id,
#                                    'so_name':order_id.name,
#                                    'so_amount':so_amount,
#                                    'inv_amount':inv_amount,
#                                    'residual_amount':inv.residual,
#                                    'created':pay.create_uid.name,
#                                    'state':state,
#                                    'discount':discount,
#                                    'user':order_id.user_id.name,
#                                    'date':pay.date,
#                                    'cash_amount':cash_amount,
#                                    'partner_id':pay.partner_id.id,
#                                    'created_id':pay.create_uid.id,
#                                    'user_id':order_id.user_id.id,
#                                    }                            
                    else:
                        print ('users ',users)
                        if users:
                            if order_id.user_id.id in users:  
                                
                                payments_dic={
#                                     'amount':pay.credit,
                                    'amount':amount_to_show,
    #                                'move_ids':[pay.id],
                                   'partner_name':pay.partner_id.name,
                                   'type':pay.journal_id.type,
#                                    'journal_name':pay.journal_id.short_name,
                                    'journal_name':pay.journal_id.name,
                                   'payment_type':order_id.payment_type,
                                   'so_id':order_id.id,
                                   'so_name':order_id.name,
                                   'so_amount':so_amount,
                                   'inv_amount':inv_amount,
                                   'residual_amount':inv.amount_residual,
                                   'created':pay.create_uid.name,
                                   'state':state,
                                   'discount':discount,
                                   'user':order_id.user_id.name,
                                   'date':pay.date,
                                   'cash_amount':cash_amount,
                                   'partner_id':pay.partner_id.id,
                                   'created_id':pay.create_uid.id,
                                   'user_id':order_id.user_id.id,
                                   }
                        else:
                            
                                    payments_dic={
        #                                 'amount':pay.credit,
                                        'amount':amount_to_show,
        #                                'move_ids':[pay.id],
                                       'partner_name':pay.partner_id.name,
                                       'type':pay.journal_id.type,
#                                        'journal_name':pay.journal_id.name,
                                        'journal_name':pay.journal_id.name,
                                       'payment_type':order_id.payment_type,
                                       'so_id':order_id.id,
                                       'so_name':order_id.name,
                                       'so_amount':so_amount,
                                       'inv_amount':inv_amount,
                                       'residual_amount':inv.amount_residual,
                                       'created':pay.create_uid.name,
                                       'state':state,
                                       'discount':discount,
                                       'user':order_id.user_id.name,
                                       'date':pay.date,
                                       'cash_amount':cash_amount,
                                       'partner_id':pay.partner_id.id,
                                       'created_id':pay.create_uid.id,
                                       'user_id':order_id.user_id.id,
                                       }
                else:

                    payments_dic={
#                                 'amount':pay.credit,
                                'amount':amount_to_show,
#                                'move_ids':[pay.id],
                               'partner_name':pay.partner_id.name,
                               'type':pay.journal_id.type,
#                                'journal_name':pay.journal_id.short_name,
                                'journal_name':pay.journal_id.name,
                               'payment_type':'none',
                               'so_id':'-1',
                               'so_name':'none',
                               'so_amount':0,
                               'inv_amount':inv.amount_total,
                               'residual_amount':inv.amount_residual,
                               'created':pay.create_uid.name,
                               'state':state,
                               'discount':0,
#                                'user':'',
                               'user':inv.user_id.name,
                               'date':pay.date,
                               'cash_amount':cash_amount,
                               'partner_id':pay.partner_id.id,
                               'created_id':pay.create_uid.id,
                               'user_id':False,
                               }    
                if payments_dic:                   
                    payments_all.append(payments_dic)

#                 _logger.info("-----------payments_all111 %s  ", str(payments_all))
        # Төлбөр үүсээгүй picking uud
        where=""
        print ('so_ids ',so_ids)
#         if len(so_ids)>0:
#             where += ' and s.id not in ( '+','.join(map(str,so_ids))+')'
#             
#         if self.user_get_so:
#             if len(self.user_ids)>1:   
#                 where += '  and s.driver_id in ( '+','.join(map(str,self.user_ids.ids))+')'
#             if len(self.user_ids)==1:   
#                 where += '  and s.driver_id = '+str(self.user_ids[0].id)+' '
#             elif self.user_id:
#                 where += '  and s.driver_id = '+str(self.user_id.id)+' '
#         else:
#             if len(users)>1:   
#                 where += '  and s.user_id in ( '+','.join(map(str,users))+')'
#             if len(users)==1:   
#                 where += '  and s.user_id = '+str(users[0])+' '
#             elif self.user_id:
#                 where += '  and s.driver_id = '+str(self.user_id.id)+' '
#             
#         query = """
#                 select 
#                         sale_id,
#                         m.date as m_date,
#                         s.driver_id,
#                         s.user_id,
#                         max(s.main_amount_total),
#                         max(amount_total) 
#                 from stock_picking p 
#                     left join stock_move m on m.picking_id=p.id 
#                     left join sale_order s on p.sale_id=s.id  
#                 where date(m.date) between '{1}' and '{2}' and p.state='done'   
#             """.format(self.user_id.id,self.date_from,self.date_to)+""" """+where+"""
#                 group by sale_id,m_date,driver_id,s.user_id"""
# #        print 'query11 ',query
#         self.env.cr.execute(query)
#         query_result = self.env.cr.dictfetchall()
#         for line in query_result:
# #            print 'line',line
#             so = so_obj.browse(line['sale_id'])
#             resi=0
#             inv_states=[]
#             if so.invoice_ids:
#                 for i in so.invoice_ids:  
#                     if i.state in ('open','draft'):
#                          inv_states.append(i)   
#             if not so.invoice_ids or len(inv_states)>0:
#                 if so.payment_type!='loan':
#                     resi=so.amount_total
#                     
#                 payments_dic={'amount':0,
#     #                                'move_ids':[pay.id],
#                            'partner_name':so.partner_id.name,
#                            'type':'',
#                            'journal_name':'',
#                            # 'journal_name':pay.journal_id.name,
#                            'payment_type':so.payment_type,
#                            'so_id':line['sale_id'],
#                            'so_name':so.name,
#                            'so_amount':so.main_amount_total,
#                            'inv_amount':so.amount_total,
#                            'residual_amount':resi,
#                            'created':'',
#                            'state':u'Төлөгдөөгүй',
#                            'discount':0,
#                            'user':so.user_id.name,
#                            'date':'',
#                            'cash_amount':0,
#                            'partner_id':so.partner_id.id,
#                            'created_id':False,
#                            'user_id':so.user_id.id,
#                            }                    
#                 payments_all.append(payments_dic)
        return payments_all

                    
    @api.model
    def get_payment_list(self,data):
#         data={'date':'2018-09-10','partner_id':self.partner_id.id}
#         data={'date':'2018-10-10','partner_id':False}
        _logger.info("------ payment -----get_payment_so_list %s  %s", str(data), type(data))
        sale_orders = []
        sale_obj = self.env['sale.order']
        pay_obj=self.env['sale.payment.info']
        acc_pay_obj=self.env['account.payment']
#         so_ids = sale_obj.search([
#         #                                   ('validity_date','=',current_date),
#                                 ('user_id','=',data['user_id'])
#                                   ])
        if self.user_ids:   
            payment_ids = acc_pay_obj.search([
                                ('payment_date','>=',data['date_from']),
                                ('payment_date','<=',data['date_to']),
                                ('create_uid','in',self.user_ids.ids),
                                ('state','in',('posted','reconciled'))
                                  ])
        elif self.user_id:
            payment_ids = acc_pay_obj.search([
                                ('payment_date','>=',data['date_from']),
                                ('payment_date','<=',data['date_to']),
                                ('create_uid','=',data['user_id']),
                                ('state','in',('posted','reconciled'))
                                  ])            
        pay_obj=self.env['sale.payment.info']
        so_amount=0
        print ('payment_ids--- ',payment_ids)
#         for so in so_ids:
#             invoice_ids = so.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
#         for payment in payment_ids:
#             invoice_ids = payment.mapped('invoice_ids').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
#         print 'invoice_ids---- ',invoice_ids
        invoice_ids = payment_ids.mapped('invoice_ids').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
        print ('invoice_ids---- ',invoice_ids)
        payments = self._compute_partner_user_so_payment(data,invoice_ids)    
#         payments = pay_obj._compute_partner_user_so_payment2(False,sdate,edate,so_ids)    
        return payments

    def pivot_report(self):
        '''pivot 
        '''
        report_datas = self.get_payment_list({
                                                'date_from':self.date_from,
                                                'date_to':self.date_to,
                                                'user_id':self.user_id.id})
        report_obj = self.env['pivot.report.payment.account']
        def _create_line(line):
            vals={
                'report_id':self.id,
                'partner_id':line['partner_id'],
                'state':line['state'],
                'type =':line['journal_name'],
                'padaan':line['so_name'],
                'created_id':line['created_id'],
                'user_id':line['user_id'],
                'date':line['date'],
                'choose_type':line['payment_type'],
                'amount':line['so_amount'],
                'get_amount':line['inv_amount'],
                'payd_amount':line['amount'],
                'zuruu':line['residual_amount'],
                'prec':line['discount']  
                }             
            report_obj.create(vals)

        for line in report_datas:
            _create_line(line)
        mod_obj = self.env['ir.model.data']        
        search_res = mod_obj.get_object_reference('mn_account', 'account_payment_pivot_search')
        search_id = search_res and search_res[1] or False
        pivot_res = mod_obj.get_object_reference('mn_account', 'account_payment_pivot_pivot')
        pivot_id = pivot_res and pivot_res[1] or False

        return {
            'name': u'Түгээлтийн тайлан',
            'view_type': 'form',
            'view_mode': 'pivot',
            'res_model': 'report.payment.account.pivot',
            'view_id': False,
            'views': [(pivot_id, 'pivot')],
            'search_view_id': search_id,
            'domain': [('report_id','=',self.id)],
            'type': 'ir.actions.act_window',
            'target': 'current'
        }        
    def check_report(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
#         datas = data
        report_datas = self.get_payment_list({
                                                'date_from':self.date_from,
                                                'date_to':self.date_to,
                                                'user_id':self.user_id.id})
        company_obj = self.env['res.company']

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet(u'Payments')
        
        num_format = '# ##0,00_);(# ##0,00)'#wizard.company_currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 24})
        date_format = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        
        def _header_sheet(sheet):
            sheet.write(0, 4, u'ТҮГЭЭЛТИЙН ТАЙЛАН', report_format)
            sheet.write(2, 0, _(u'Компани:'), bold)
            sheet.write(3, 0, self.company_id.name,)
            sheet.write(4, 0, _('Print on %s') % time.strftime('%Y-%m-%d'))#report.print_time)

            sheet.write(2, 2, _(u'Эхлэх огноо : %s ') % self.date_from if self.date_from else '')
            sheet.write(3, 2, _(u'Дуусах огноо : %s ') % self.date_to if self.date_to else '')
        
        rowx = 5
        _header_sheet(sheet)
        
        head = [
            {'name': _(u'Дд'),
             'larg': 8,
             'col': {}},
            {'name': _(u'Төлөв'),
             'larg': 10,
             'col': {}},
            {'name': _(u'Төлсөн хэлбэр'),
             'larg': 10,
             'col': {}},
            {'name': _(u'харилцагч'),
             'larg': 40,
             'col': {}},
            {'name': _(u'Падаан №'),
             'larg': 12,
             'col': {}},
            {'name': _(u'Оруулсан'),
             'larg': 15,
             'col': {}},
            {'name': _(u'Борлуулагч'),
             'larg': 15,
             'col': {}},
            {'name': _(u'Огноо'),
             'larg': 15,
             'col': {}},
            {'name': _( u'Сонгосон хэлбэр'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
#             {'name': _(u'Дүн'),
#              'larg': 15,
#              'col': {'total_function': 'sum', 'format': currency_format}},#
            {'name': _(u'Авах дүн'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
            {'name': _(u'Авсан дүн'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
            {'name': _(u'Зөрүү'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
            {'name': _(u'%'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
        ]
        table = []
        for h in head:
            col = {'header': h['name']}
            col.update(h['col'])
            table.append(col)
                    
        def _set_line(line):
            sheet.write(rowx, 0, n)
            sheet.write(rowx, 1, line['state'])
            sheet.write(rowx, 2, line['journal_name'])
            sheet.write(rowx, 3, line['partner_name'])
            sheet.write(rowx, 4, line['so_name'])
            sheet.write(rowx, 5, line['created'], currency_format)
            sheet.write(rowx, 6, line['user'])
            sheet.write(rowx, 7, line['date'],date_format)
            sheet.write(rowx, 8, line['payment_type'], currency_format)
#             sheet.write(rowx, 9, line['so_amount'], currency_format)
            sheet.write(rowx, 9, line['inv_amount'], currency_format)
    #             sheet.write(rowx, 8, line['residual_amount'], currency_format)
            sheet.write(rowx, 10, line['amount'], currency_format)
#             sheet.write(rowx, 10, line['inv_amount'] - line['amount'], currency_format)
            sheet.write(rowx, 11, line['residual_amount'], currency_format)
            sheet.write(rowx, 12, line['discount'], currency_format)
            
        def _set_table(start_row, row):
            sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                            {'total_row': 1,
                             'columns': table,
                             'style': 'Table Style Light 9',
                             })
            
        rowx += 1
        n=1

        start_row = rowx
        cash_amount=0
        for line in report_datas:
            _set_line(line)
            cash_amount+=line['cash_amount']
            rowx += 1

            n+=1
            
        for j, h in enumerate(head):
            sheet.set_column(j, j, h['larg'])

        _set_table(start_row, rowx)
        rowx += 2
            
        sheet.write(rowx, 3, u'Нийт бэлэн')
        sheet.write(rowx, 4, cash_amount, currency_format)
#             sheet.write(rowx, 5, line[5], number_xf)
#             sheet.write(rowx, 6, line[6], number_xf)
#             sheet.write(rowx, 7, line[7], number_xf)
#             sheet.write(rowx, 8, line[8], number_xf)
 
        #sheet.set_panes_frozen(True) # frozen headings instead of split panes
        #sheet.set_horz_split_pos(2) # in general, freeze after last heading row
        #sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
        #sheet.set_col_default_width(True)
         
        workbook.close()

        out = base64.encodestring(output.getvalue())
        file_name='payment_report.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }



    
    def _compute_partner_payment(self,date_start,date_end,user_ids=False):
        _logger.info(u'payment user-------_compute_partner_payment \n') 
        query=True
        if query:
            result=0   
            
            if user_ids:
                 
#                 sql_query = """
#                                     select sum(debit) as debit,(select name from res_partner where id=partner) as part  from (                              
#                                     select aml.debit as debit,aj.name,aml.id as aml_id,aml.partner_id as partner from 
#                                                 account_payment p left join 
#                                                 account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
#                                                 account_invoice ai on ai.id=ipr.invoice_id left join
#                                                 account_move_line aml on aml.payment_id=p.id left join     
#                                                 account_journal aj on aml.journal_id=aj.id left join      
#                                                 account_account a on aml.account_id=a.id
#                                                 WHERE
#                                                 payment_date>=%s
#                                                 and payment_date<=%s 
#                                                 and ai.user_id = %s
#                                                 and p.state in ('posted','reconciled')
#                                                 and a.internal_type='liquidity'
#                                                       group by aj.name ,aml.id,aml.partner_id  ) as foo  group by partner order by sum(debit)
#                     """
#                 where = '  and ai.user_id in ( '+','.join(map(str,self.user_ids.ids))+')'

#                 sql_query = """
# 
#                   select sum(inv_amount) as inv_amount,sum(debit) as debit,name,(select name from res_partner where id=partner_id) as part from (
#                                  --давхар шүүлт
#                                  select case when inv_count2=1 and debit>inv_amount 
#                                  then debit else inv_amount end as inv_amount,debit,name,partner_id from
#                                  (
#                             ------
#                                select sum(debit) debit,inv_id,count(inv_id),
#                                 ----
#                               (select count(distinct invoice_id) from account_invoice_payment_rel where payment_id =p_id) as inv_count2,
#                               -----    
#                                    (select sum(apr.amount) from  
#                                         account_invoice ai left join
#                                         account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
#                                         account_partial_reconcile apr on aiaml.account_move_line_id=apr.credit_move_id--matched_debit_ids
#                                         left join
#                                         account_move am on ai.move_id=am.id left join
#                                         account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
#                                         where ai.id=inv_id and aml.id notnull) as inv_amount,name,partner_id
#                                    from (
#                                    select aml.id as aml_id,aml.debit,ai.id as inv_id , 
#                                        aj.name as name,p.id as p_id,p.partner_id as partner_id
#                                         from 
#                                         account_payment p left join 
#                                         account_invoice_payment_rel ipr on ipr.payment_id=p.id left join 
#                                         account_invoice ai on ai.id=ipr.invoice_id left join
#                                         account_invoice_line ail on ai.id=ail.invoice_id left join        
#                                         sale_order_line_invoice_rel slr on slr.invoice_line_id=ail.id left join
#                                         sale_order_line sol on slr.order_line_id=sol.id        left join 
#                                         sale_order so on sol.order_id=so.id     left join 
#                                         account_move_line aml on aml.payment_id=p.id left join     
#                                         account_journal aj on aml.journal_id=aj.id   left join
#                                         account_account a on aml.account_id=a.id
#                                       where 
#                                        
#                                                 payment_date>=%s
#                                                 and payment_date<=%s 
#                                                 """+where+"""
#                                                 and p.state in ('posted','reconciled')
#                                                 and a.internal_type='liquidity'
#                                   group by aml.id,ai.id, aj.name,p.id,p.partner_id) as foo group by inv_id,name,p_id,partner_id order by inv_id desc
#                                      ) as foo2
#                                   ) as baar group by name ,partner_id   
#                     """
#                 params = (date_start,date_end)
                where = '  and ai.user_id in ( '+','.join(map(str,self.user_ids.ids))+')'
                
                sql_query = """
                    select sum(pay_amount) as pay_amount,sum(amount),sum(discount),sum(amount_report) as amount_report,(select name from res_partner where id=foo.partner_id) as part from (
                    select p.amount as pay_amount,apr.amount,aml.debit,aml.credit,aml.id,apr.id,ai.id ai_id,aj.name,p.is_more,p.discount,
                                case when p.is_more then (select credit from account_move_line where id=apr.credit_move_id)--p.credit_move_id.credit
                                else apr.amount end as amount_report,p.id as p_id,p.with_discount,p.from_bank,aml.partner_id
                                from  
                                account_invoice ai left join
                                account_invoice_account_move_line_rel aiaml on aiaml.account_invoice_id=ai.id left join --payment_move_line_ids 
                                account_move_line aml on aiaml.account_move_line_id=aml.id left join--and aml.id=apr.debit_move_id 
                                account_partial_reconcile apr on aml.id=apr.credit_move_id--matched_debit_ids
                                        and apr.debit_move_id in (select id from account_move_line aml2 where move_id=ai.move_id)--inv.move_id.line_ids
                                        left join
                                account_payment p on p.id=aml.payment_id left join
                                account_journal aj on aml.journal_id=aj.id 
                        
                        --        left join
                        --        account_move am on ai.move_id=am.id left join
                        --        account_move_line aml on aml.move_id=am.id and aml.id=apr.debit_move_id 
                                where 
                                aml.date>=%s
                                and aml.date<=%s
                                """ + where +""" 
                                and p.state in ('posted','reconciled')
                                order by ai.id  
    ) as foo group by partner_id     """

#                 sql_query += ' group by ipr.invoice_id,aml.date,so.id'
#                 print 'sql_query ',sql_query
                params = (date_start,date_end)

                self.env.cr.execute(sql_query, params)
                query_res=self.env.cr.dictfetchall()                    
#                 print 'query_res ',query_res                                  
    
#             _logger.info("------ mobile -----result %s  ", str(result))
                         
            return query_res
        

    def check_report_partner(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
#         datas = data
        report_datas = self._compute_partner_payment(
                                                self.date_from,
                                                self.date_to,
                                                self.user_ids.ids)
        
        company_obj = self.env['res.company']

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet(u'Payments')
        
        num_format = '# ##0,00_);(# ##0,00)'#wizard.company_currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 24})
        date_format = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        
        def _header_sheet(sheet):
            sheet.write(0, 4, u'ТҮГЭЭЛТИЙН ТАЙЛАН', report_format)
            sheet.write(2, 0, _(u'Компани:'), bold)
            sheet.write(3, 0, self.company_id.name,)
            sheet.write(4, 0, _('Print on %s') % time.strftime('%Y-%m-%d'))#report.print_time)

            sheet.write(2, 2, _(u'Эхлэх огноо : %s ') % self.date_from if self.date_from else '')
            sheet.write(3, 2, _(u'Дуусах огноо : %s ') % self.date_to if self.date_to else '')
        
        rowx = 5
        _header_sheet(sheet)
        
        head = [
            {'name': _(u'Дд'),
             'larg': 8,
             'col': {}},
            {'name': _(u'Харилцагч'),
             'larg': 10,
             'col': {}},
            {'name': _(u'Дүн'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
        ]
        table = []
        for h in head:
            col = {'header': h['name']}
            col.update(h['col'])
            table.append(col)
                    
        def _set_line(line):
            amount =0
#             if line['debit']>line['inv_amount']:
#                 amount=line['inv_amount']
#             else:
#                 amount=line['debit']
            amount=line['amount_report']

                
            sheet.write(rowx, 0, n)
            sheet.write(rowx, 1, line['part'])
            sheet.write(rowx, 2, amount)
            
        def _set_table(start_row, row):
            sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
                            {'total_row': 1,
                             'columns': table,
                             'style': 'Table Style Light 9',
                             })
            
        rowx += 1
        n=1

        start_row = rowx
        cash_amount=0
        for line in report_datas:
            _set_line(line)
#             cash_amount+=line['cash_amount']
            rowx += 1

            n+=1
            
        for j, h in enumerate(head):
            sheet.set_column(j, j, h['larg'])

        _set_table(start_row, rowx)
        rowx += 2
            
        workbook.close()

        out = base64.encodestring(output.getvalue())
        file_name='payment_report_detail.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }

        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

