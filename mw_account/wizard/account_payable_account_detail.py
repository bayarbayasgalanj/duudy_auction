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

import base64
import time
import datetime
from datetime import datetime

from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

from datetime import timedelta
from lxml import etree
from odoo.tools.translate import _

import xlwt
from xlwt import *
from operator import itemgetter
import collections
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare

import logging

_logger = logging.getLogger(__name__)

class account_payable_account_detail(models.TransientModel):
    """
        Өглөгийн дансны дэлгэрэнгүй бүртгэл
    """
    
#     _inherit = "abstract.report.excel"
    _inherit = "account.common.report"
    _name = "account.payable.account.detail"
    _description = "Payable Account Detail Report"
    
    company_id = fields.Many2one('res.company', 'Company')
    account_id = fields.Many2one('account.account', 'Account', domain=[('user_type_id.type','in',['payable','receivable'])])
    date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))
    target_move = fields.Selection([('all', 'All Entries'),
                                    ('posted', 'All Posted Entries')], 'Target Moves', required=True,default='posted')
    partner_id = fields.Many2one('res.partner', 'Partner', help="If empty, display all partners")

#     type = fields.Selection([('all', 'All'),('payable', 'Payable'),
#                                     ('receivable', 'Receivable')], 'Type',default='all')
    is_currency = fields.Boolean('Is currency',default=False)
    is_date = fields.Boolean('Is Date',default=False)
    is_from_invoice = fields.Boolean('Is from invoice',default=False)
    state_invoice = fields.Selection([('open',u'Нээлттэй'),('paid',u'Төлөгдсөн'),('all',u'Бүгд')], 'Төлөв', required=True,default='all')    

    is_open = fields.Boolean('Only open?',default=False)
    is_invoice_open = fields.Boolean('Only open?',default=False)

    is_warehouse = fields.Boolean('Warehouse?',default=False)
    is_tag = fields.Boolean('Is tag')
    
    tag_id = fields.Many2one('res.partner.category', 'Category')
    
    def _build_contexts(self, data):
        result = {}
#         print "data ",data
        if not data['form']['date_from'] or not data['form']['date_to']:
            raise UserError((u'Эхлэх дуусах огноо сонгоно уу.'))
        elif data['form']['date_from'] > data['form']['date_to']:
            raise UserError((u'Эхлэх огноо дуусах огнооноос бага байх ёстой.'))
            
#         result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        result['strict_range'] = True if result['date_from'] else False
 
        return result

    def prepare_data(self, context=None):
        
        data = {}
        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
#         data = self.pre_print_report(data)
        data['form']['company_id'] = form['company_id'][0]
        
        return data
    
    def print_report(self,context=None):
        if context is None:
            context = {}
        
        data = self.prepare_data(context=context)
        
        context.update({'report_type':'payable'})
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'account.payable.account.detail',
            'datas': data,
            'context': context,
            'nodestroy': True,
        }
    

    def _print_report(self, data):
        form = self.read()[0]
        data['form'] = form
        data['form'].update(self._build_contexts(data))
#         data = self.pre_print_report(data)
        if self.is_invoice_open:
            return self._make_excel_open(data)
        return self._make_excel(data)
        

    def _amount_residual(self,lines):
        """ Computes the residual amount of a move line from a reconciliable account in the company currency and the line's currency.
            This amount will be 0 for fully reconciled lines or lines from a non-reconciliable account, the original line amount
            for unreconciled lines, and something in-between for partially reconciled lines.
        """
#         print 'lines ',lines
        for line in lines:
            if not line.account_id.reconcile:
                line.reconciled = False
                line.amount_residual = 0
                line.amount_residual_currency = 0
                continue
            #amounts in the partial reconcile table aren't signed, so we need to use abs()
            amount = abs(line.debit - line.credit)
            other_amount=0
#             print 'amount1 ',amount
            amount_residual_currency = abs(line.amount_currency) or 0.0
            sign = 1 if (line.debit - line.credit) > 0 else -1
            if not line.debit and not line.credit and line.amount_currency and line.currency_id:
                #residual for exchange rate entries
                sign = 1 if float_compare(line.amount_currency, 0, precision_rounding=line.currency_id.rounding) == 1 else -1
#             print 'line.matched_debit_ids ',line.matched_debit_ids
#             print 'line.matched_credit_ids ',line.matched_credit_ids
            for partial_line in (line.matched_debit_ids + line.matched_credit_ids):
                # If line is a credit (sign = -1) we:
                #  - subtract matched_debit_ids (partial_line.credit_move_id == line)
                #  - add matched_credit_ids (partial_line.credit_move_id != line)
                # If line is a debit (sign = 1), do the opposite.
                sign_partial_line = sign if partial_line.credit_move_id == line else (-1 * sign)
#                 if line.id==84496:
#                     print 'partial_line.amount______________ ',partial_line.amount
#     #                 print 'partial_line ',partial_line
#                     print 'partial_line.max_date> ',partial_line.max_date
#                     print 'self.date_to ',self.date_to
                if partial_line.max_date<self.date_from or partial_line.max_date>self.date_to:
#                     if line.id==84496:
#                         print 'partial_line-------: ',partial_line
                    other_amount+=sign_partial_line * partial_line.amount
                amount += sign_partial_line * partial_line.amount
                #getting the date of the matched item to compute the amount_residual in currency
                if line.currency_id:
                    if partial_line.currency_id and partial_line.currency_id == line.currency_id:
                        amount_residual_currency += sign_partial_line * partial_line.amount_currency
                    else:
                        if line.balance and line.amount_currency:
                            rate = line.amount_currency / line.balance
                        else:
                            date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                            rate = line.currency_id.with_context(date=date).rate
                        amount_residual_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)

            #computing the `reconciled` field.
            reconciled = False
            digits_rounding_precision = line.company_id.currency_id.rounding
            if float_is_zero(amount, precision_rounding=digits_rounding_precision):
#                 print 'amount ',amount
                if line.currency_id and line.amount_currency:
#                     print 'amount_residual_currency ',amount_residual_currency
                    if float_is_zero(amount_residual_currency, precision_rounding=line.currency_id.rounding):
                        reconciled = True
                else:
                    reconciled = True
            line.reconciled = reconciled
        return amount,other_amount
#             lineamount_residual = line.company_id.currency_id.round(amount * sign)
#             line.amount_residual_currency = line.currency_id and line.currency_id.round(amount_residual_currency * sign) or 0.0

        
    def get_report_data(self, data,partner):
        ''' Харилцагчийн өглөг авлагын гүйлгээг эхний үлдэгдэлийн хамтаар
            боловсруулж бэлтгэнэ.
        '''
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        
        partner_ids = []
#         if data['partner_id']:
#             partner_ids = [data['partner_id'][0]]
        partner_ids = [partner.id]
#             child_ids = partner_obj.search([('parent_id','=',data['partner_id'][0])])
#             if child_ids :
#                 partner_ids = partner_ids + child_ids
        account_ids = []
        if data['account_id']:
#             account_ids = [data['account_id'][0]]
            account_ids = account_obj.search([('id','=',data['account_id'][0])])
        elif data['account_type'] == 'payable':
            account_ids = account_obj.search([('user_type_id.type','=','payable')])
        elif data['account_type'] == 'receivable':
            account_ids = account_obj.search([('user_type_id.type','=','receivable')])

        if not data['account_id']:
            if data['account_type'] == 'receivable':
                add_account_ids = account_obj.search([('is_recpay','=',True),('user_type_id.balance_type','=','active')])
            elif data['account_type'] == 'payable':
                add_account_ids = account_obj.search([('is_recpay','=',True),('user_type_id.balance_type','=','passive')])
            account_ids+=add_account_ids
        date_where = ""
#         if data['date_from'] == fiscalyear.date_start:
#             print 'if --------- 1'
#             date_where = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
#         else :
#             print 'if --------- 2'
        date_where = " m.date < '%s' " % data['date_from']
        open_where=""
        if self.is_open:
            open_where =" AND l.amount_residual<>0 " #and amount_residual_currency<>0 
        state_where = ""
        if data['target_move'] != 'all':
            state_where = " AND m.state = '%s' " % data['target_move']
        partner_where = " AND l.partner_id is not null "
        if partner_ids :
            partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        if self.company_id:
            partner_where += " AND l.company_id = {0}".format(self.company_id.id)        
        
        a = []
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
                                                        state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        init_wheres = [""]
        
        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
#         print 'filters=======: ',filters
#         print 'init_where_params ',init_where_params
#         print ('account_ids ',account_ids)
        for account in account_ids.ids:
#            cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
#                       "FROM account_move_line l "
#                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
#                       "LEFT JOIN account_period p ON (p.id=l.period_id) "
#                       "WHERE "+date_where+" AND p.fiscalyear_id = %s "
#                       " AND l.state <> 'draft' "+state_where+partner_where+" "
#                       " AND l.account_id = %s "
#                       "GROUP BY l.account_id ", (data['fiscalyear_id'], account))
#Эхний үлдэгдэл
    #         move_lines = dict(map(lambda x: (x, []), accounts.ids))
    #         print "data context ",data
            if self.is_open:
                cr.execute("SELECT coalesce(sum(l.amount_residual),0.0), coalesce(sum(l.amount_residual_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "WHERE "
                       " state='posted' "+partner_where+" " 
                       " "+filters+" "
                       " AND l.account_id = " + str(account) + 
                       " GROUP BY l.account_id ",tuple(init_where_params))
                fetched = cr.fetchone()
#                 print "fetched::::::",fetched
                sresidual, samount_currency = fetched or (0,0)
                account_str = account_obj.browse(account)
                acc=account_str.code + ' ' + account_str.name
                if data['account_type'] == 'payable':
                    initial_amount = -sresidual
                    initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
                else :
                    initial_amount = sresidual
                    initial_amount_currency = samount_currency
            
            else:
                cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "WHERE "
                       " state='posted' "+partner_where+" " 
                       " "+filters+" "
                       " AND l.account_id = " + str(account) + 
                       " GROUP BY l.account_id ",tuple(init_where_params))
    #             AND l.state <> 'draft' 
                fetched = cr.fetchone()
    #             print "fetched::::::",fetched
    #             if fetched:
    #                 q = "SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) \
    #                            FROM account_move_line l \
    #                            LEFT JOIN account_move m ON (m.id=l.move_id) \
    #                            LEFT JOIN account_period p ON (p.id=l.period_id) \
    #                            WHERE "+date_where+" "+state_where \
    #                            + partner_where+" AND l.account_id = " + str(account) + " \
    #                            GROUP BY l.account_id "
    #                 print 'Query;       ', q
    #                 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
                sdebit, scredit, samount_currency = fetched or (0,0,0)
                account_str = account_obj.browse(account)
                acc=account_str.code + ' ' + account_str.name
                if data['account_type'] == 'payable':
                    initial_amount = scredit - sdebit
                    initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
                else :
                    initial_amount = sdebit - scredit
                    initial_amount_currency = samount_currency
            
            balance, balance_currency = initial_amount, initial_amount_currency
            #balance, balance_currency = 0, 0
            move_line_obj = self.env['account.move.line']
            date_where1 = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
            # if initial_bal_journal:
            #     date_where1 += "AND l.journal_id <> %s " % initial_bal_journal
#             and (j.special is null or j.special='f') 
            cr.execute("SELECT l.id  "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "LEFT JOIN res_partner r ON (l.partner_id=r.id) "
                       "LEFT JOIN account_journal j ON (j.id=l.journal_id) "
                       "WHERE "+date_where1+"  "
                       " "+state_where+partner_where+"  " #+open_where+" "
                       " AND l.account_id =  " + str(account)+" "
                       "ORDER BY l.date, r.name")
#             data['fiscalyear_id'], AND p.fiscalyear_id = %s
#                        "LEFT JOIN account_period p ON (p.id=l.period_id) "
            fetched = cr.fetchall()
            result = []
            number = 1
            if fetched or initial_amount!=0:
                q1 = "SELECT l.id  FROM account_move_line l \
                           LEFT JOIN account_move m ON (m.id=l.move_id) \
                           LEFT JOIN res_partner r ON (l.partner_id=r.id) \
                           LEFT JOIN account_journal j ON (j.id=l.journal_id) \
                           WHERE "+date_where1+" \
                            "+state_where+partner_where+"  "+open_where+" AND l.account_id = " + str(account) + " and (j.special is null or j.special='f') \
                           ORDER BY l.date, r.name"
#                            LEFT JOIN account_period p ON (p.id=l.period_id) \
# AND p.fiscalyear_id = " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
#                 print 'Q1 :  ', q1
                line_ids = [x[0] for x in fetched]
#                 print 'line_idslen::::::::',len(line_ids)               
#                print ('line_ids::::::::',line_ids)
                for line in move_line_obj.browse(line_ids):
                    row = {}
                    row['number'] = str(number)
                    row['date'] = line.date
                    row['name'] = line.move_id.ref or line.move_id.name
                    row['account'] = account_str.code + ' ' + account_str.name
                    debit_lines = []
                    credit_lines = []
                    if self.is_open:
                        if line.debit>0:
#                             debit = line.amount_residual
                            ch_debit,other_amount=self._amount_residual([line])
                            debit=abs(ch_debit)+abs(other_amount)
                            credit = 0
                        else:
#                             credit = abs(line.amount_residual)
                            ch_credit,other_amount = self._amount_residual([line])
                            credit=abs(ch_credit)+abs(other_amount)
                            debit = 0
                    else:
                        debit = line.debit
                        credit = line.credit
                    sale_line_ids=False
                    for other_line in line.move_id.line_ids :
                        if other_line.id != line.id :
                            if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                debit_lines.append(u'Дт:'+other_line.account_id.code)
                            elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                credit_lines.append(u'Кт:'+other_line.account_id.code)
                            if other_line.sale_line_ids:
                                sale_line_ids=other_line.sale_line_ids
                    row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                    row['partner'] = line.partner_id.name
                    

                    sale_child_partner=''
#                     print ('line.sale_line_ids ',sale_line_ids)
                    so_id=False
                    if sale_line_ids:
                        so_id=sale_line_ids[0].order_id
                        if so_id.partner_id.id != so_id.partner_invoice_id.id:
                            sale_child_partner = ' - '+so_id.partner_id.name
                    if line.move_id.sale_return_id:
                        sale_child_partner=line.move_id.sale_return_id.partner_id.name
                        if not line.name:
                            line.name=line.move_id.name
                    narration =(line.name or '') + (sale_child_partner or '') + (so_id and ' '+so_id.name or '')  
                    if not narration:
                        if line.move_id.type in ('in_invoice','in_refund') and line.move_id.invoice_origin:
                            narration=line.move_id.invoice_origin
                    row['narration'] = narration                 
#                     row['narration'] = line.name 
                    row['currency'] = (line.currency_id and line.currency_id.name) or ''
                    row['debit_currency'] = (line.debit > 0 and line.amount_currency) or 0
                    row['debit'] = debit
                    row['credit_currency'] = (line.credit > 0 and abs(line.amount_currency)) or 0
                    row['credit'] = credit
                    
                    row['so_id']=so_id
                    row['branch']=line.branch_id and line.branch_id.name or ''
                    if data['account_type'] == 'payable':
                        balance = balance + credit - debit
#                         balance_currency += line.amount_currency if line.credit == 0 else line.amount_currency
                        if line.amount_currency!=0:
                            if line.credit>0 :
                                balance_currency += abs(line.amount_currency)
                            else:
                                balance_currency -= abs(line.amount_currency)
                    else :
                        balance = balance + debit - credit
#                         balance_currency += line.amount_currency if line.debit == 0 else line.amount_currency
                        if line.amount_currency!=0:
                            if line.debit>0 :
                                balance_currency += abs(line.amount_currency)
                            else:
                                balance_currency -= abs(line.amount_currency)

                    row['balance_currency'] = balance_currency
                    row['balance'] = balance
                    number += 1
                    if self.is_open:
                        if debit!=0 or credit!=0:
                            result.append(row)
                    else:
                        result.append(row)
                    
                a.append([initial_amount, initial_amount_currency, result,acc])
        #return initial_amount, initial_amount_currency, result
        return a
            
    def get_report_data_inv(self, data):
        ''' Харилцагчийн өглөг авлагын гүйлгээг эхний үлдэгдэлийн хамтаар
            боловсруулж бэлтгэнэ.
        '''
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        
        partner_ids = []
        if data['partner_id']:
            partner_ids = [data['partner_id'][0]]
#             child_ids = partner_obj.search([('parent_id','=',data['partner_id'][0])])
#             if child_ids :
#                 partner_ids = partner_ids + child_ids
        account_ids = []
        if data['account_id']:
#             account_ids = [data['account_id'][0]]
            account_ids = account_obj.search([('id','=',data['account_id'][0])])
        elif data['account_type'] == 'payable':
            account_ids = account_obj.search([('user_type_id.type','=','payable')])
        elif data['account_type'] == 'receivable':
            account_ids = account_obj.search([('user_type_id.type','=','receivable')])

        date_where = ""
        
        date_where = " m.date < '%s' " % data['date_from']
        state_where = ""
        state_invoice_where=""
        if data['state_invoice']=='all':
            state_invoice_where=" AND l.state in ('open','paid')"
        else:
            state_invoice_where=" AND l.state ='{0}'".format(data['state_invoice'])
        if data['target_move'] != 'all':
            state_where = " AND m.state = '%s' " % data['target_move']
        partner_where = " AND l.partner_id is not null "
        if partner_ids :
            partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        if self.company_id:
            partner_where += " AND l.company_id = {0}".format(self.company_id.id)        
        a = []
        for account in account_ids.ids:
            cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "WHERE "+date_where+
                       " "+state_where+partner_where+" "
                       " AND l.account_id = " + str(account) +
                       " GROUP BY l.account_id ")
#             AND l.state <> 'draft' 
            fetched = cr.fetchone()
#             print "fetched::::::",fetched
            if fetched:
                q = "SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) \
                           FROM account_move_line l \
                           LEFT JOIN account_move m ON (m.id=l.move_id) \
                           LEFT JOIN account_period p ON (p.id=l.period_id) \
                           WHERE "+date_where+" "+state_where \
                           + partner_where+"  AND l.account_id = " + str(account) + " GROUP BY l.account_id "
#                 print 'Query;       ', q
#                 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
            sdebit, scredit, samount_currency = fetched or (0,0,0)
            account_str = account_obj.browse(account)
            acc=account_str.code + ' ' + account_str.name
            if data['account_type'] == 'payable':
                initial_amount = scredit - sdebit
                initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
            else :
                initial_amount = sdebit - scredit
                initial_amount_currency = samount_currency
            
            balance, balance_currency = initial_amount, initial_amount_currency
            #balance, balance_currency = 0, 0
            invoice_obj = self.env['account.invoice']
            date_where1 = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
            # if initial_bal_journal:
            #     date_where1 += "AND l.journal_id <> %s " % initial_bal_journal
            cr.execute("SELECT l.id  FROM account_invoice l "
                        "   LEFT JOIN account_move m ON (m.id=l.move_id) "
                        "   LEFT JOIN res_partner r ON (l.partner_id=r.id) "
                       "WHERE "+date_where1+"  "
                       " "+state_where+partner_where+" "
                       " AND l.account_id =  " + str(account)+ " "
                       " "+state_invoice_where+" "
                       "ORDER BY l.date, r.name")
#             data['fiscalyear_id'], AND p.fiscalyear_id = %s
#                        "LEFT JOIN account_period p ON (p.id=l.period_id) "
            fetched = cr.fetchall()
            result = []
            number = 1
            if fetched or initial_amount!=0:
                q1 = "SELECT l.id  FROM account_invoice l \
                           LEFT JOIN account_move m ON (m.id=l.move_id) \
                           LEFT JOIN res_partner r ON (l.partner_id=r.id) \
                           WHERE "+date_where1+" \
                           \ "+state_where+partner_where+" AND l.account_id = " + str(account) + " \
                           "+state_invoice_where+" \
                           ORDER BY m.date, r.name"
#                            LEFT JOIN account_period p ON (p.id=l.period_id) \
# AND p.fiscalyear_id = " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
#                 print 'Q1 :  ', q1
                line_ids = [x[0] for x in fetched]
                for line in invoice_obj.browse(line_ids):
                    row = {}
                    row['number'] = str(number)
                    row['date'] = line.move_id.date
                    row['name'] = line.move_id.ref or line.move_id.name
                    row['account'] = account_str.code + ' ' + account_str.name
                    debit_lines = []
                    credit_lines = []
                    for other_line in line.move_id.line_ids :
                        if other_line.id != line.id :
                            if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                debit_lines.append(u'Дт:'+other_line.account_id.code)
                            elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                credit_lines.append(u'Кт:'+other_line.account_id.code)
                    row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                    row['partner'] = line.partner_id.name
                    row['narration'] = line.name or line.narration
                    row['currency'] = (line.currency_id and line.currency_id.name) or ''
                    row['debit_currency'] = 0#(line.amount > 0 and line.amount_currency) or 0
                    if line.type=='out_refund':
                        row['credit'] =line.amount_total
                        row['debit'] = 0#line.amount_total
                    else:
                        row['credit'] = 0#line.amount_total
                        row['debit'] = line.amount_total
                    row['credit_currency'] = 0#(line.credit > 0 and abs(line.amount_currency)) or 0
#                     balance = balance + line.amount_total
                    balance = balance + row['debit'] - row['credit']

                    row['balance_currency'] = balance_currency
                    row['balance'] = balance
                    number += 1
                    result.append(row)
                    
                a.append([initial_amount, initial_amount_currency, result,acc])
        return a
                
    def _make_excel(self, data):
        account_obj = self.env['account.account']
        styledict = self.env['abstract.report.excel'].get_easyxf_styles()
        
        ezxf = xlwt.easyxf
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet(u'Payable Receivable Detail')

        data = data['form']
        
#         account = account_obj.browse(cr, uid, data['account_id'], context=context)
        partner = False
        partners=[]
        if data['partner_id']:
            partners = [self.env['res.partner'].browse(data['partner_id'][0])]
        elif self.tag_id:
            partners = self.env['res.partner'].search([('category_id','in',[self.tag_id.id])])
            
        title = ''
        report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
        sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
        rowx = 5
        
        for partner in partners:
            
            date_str = '%s-%s' % (
    #             datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
    #             datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
                    data['date_from'],
                     data['date_to']
            )
            '''
            if context['report_type'] == 'payable' :
                title = u'Маягт ӨГ-2'
                report_name = u'Өглөгийн дансны дэлгэрэнгүй бүртгэл'
            else :
                title = u'Маягт АВ-2'
                report_name = u'Авлагын дансны дэлгэрэнгүй бүртгэл'
            '''
#             title = ''
#             report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
#             sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#             sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#             sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
            sheet.write(rowx, 8, u'Тайлант хугацаа: %s' % date_str, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
            sheet.write(rowx, 0, u"Харилцагчийн код: %s" % ((partner and (partner.ref or '')) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
            sheet.write(rowx+1, 0, u"Харилцагчийн нэр: %s" % ((partner and partner.name) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
            sheet.write(rowx+1, 8, time.strftime('%Y-%m-%d %H:%M'), xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
            rowx+=3
#             rowx = 8
            
            reports = ['receivable','payable']
            
            total_amount=[0,0,0,0,0,0]
            tmp_amount = [0,0,0,0,0,0]
            report_num = 0
            for report in reports:
                data['account_type'] = report
    #             print 'data[] ',data['account_id']
                if data['account_id']:
                    acc = account_obj.browse(data['account_id'][0])
                    if acc.user_type_id.type != report: continue
                if self.is_currency:
                    sheet.write_merge(rowx, rowx+2, 0, 0, u'№', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 1, 1, u'Огноо', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 3, 3, u'Данс', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 6, 9, u'Гүйлгээний дүн', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 10, 11, u'Үлдэгдэл', styledict['heading_xf'])
                    rowx += 1
                    sheet.write_merge(rowx, rowx, 6, 7, u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 8, 9, u'Кредит', styledict['heading_xf'])
                    #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 10, 11, (report == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx-1, rowx+1, 12, 12, u'Харьцсан данс', styledict['heading_xf'])
                    rowx += 1
                    sheet.write(rowx, 6, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
                    sheet.write(rowx, 8, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
                    sheet.write(rowx, 10, u'Валют', styledict['heading_xf'])
                    sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
                    rowx += 1
                else:
                    sheet.write_merge(rowx, rowx+1, 0, 0, u'№', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 1, 1, u'Огноо', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 3, 3, u'Данс', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx+1, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
    #                 sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                    sheet.write_merge(rowx, rowx, 5, 6, u'Гүйлгээний дүн', styledict['heading_xf'])
                    sheet.write(rowx, 7, u'Үлдэгдэл', styledict['heading_xf'])
                    rowx += 1
                    sheet.write(rowx, 5, u'Дебет', styledict['heading_xf'])
                    sheet.write(rowx, 6, u'Кредит', styledict['heading_xf'])
                    #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write(rowx, 7, (report == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                    sheet.write_merge(rowx-1, rowx, 8, 8, u'Харьцсан данс', styledict['heading_xf'])
                    if self.is_warehouse and not data['is_from_invoice']:
                        sheet.write_merge(rowx-1, rowx, 9, 9, u'Агуулах', styledict['heading_xf'])
                        sheet.write_merge(rowx-1, rowx, 10, 10, u'Салбар', styledict['heading_xf'])
                    else:
                        sheet.write_merge(rowx-1, rowx, 9, 9, u'Салбар', styledict['heading_xf'])
    #                 rowx += 1
    #                 sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
    #                 sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
    #                 sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
                    rowx += 1            
                #initial_amount, initial_amount_currency, lines = report_service.get_report_data(cr, uid, data, context=context)
    #             datas = report_service.get_report_data(cr, uid, data, context=context)
#                 print ('data--- ',data)
#                 data['partner_id'][0]=partner
                if data['is_from_invoice']:
                    datas = self.get_report_data_inv(data)
                else:
                    datas = self.get_report_data(data,partner)
#                 print ('datas ',datas)
                #test
                totals = [0,0,0,0,0,0]
                for d in datas:
                    if self.is_currency:
                        sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                        sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                        sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                        sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 7, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                #        sheet.write(rowx, 12, initial_amount_currency, styledict['number_xf'])
                #        sheet.write(rowx, 13, initial_amount, styledict['number_xf'])
                        sheet.write(rowx, 10, d[1], styledict['grey_number_bold_xf1'])
                        sheet.write(rowx, 11, d[0], styledict['grey_number_bold_xf1'])
                        sheet.write(rowx, 12, 'x', styledict['heading_xf-grey'])
                        rowx += 1
                        
                        number = 0
                        balance = 0
                        balance_currency =0
                        for line in d[2]:
                            
                            sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                            sheet.row(rowx).height = 370
                            sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                            sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                            sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                            sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
                            sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
                            sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 7, line['debit'], styledict['number_xf'])
                            sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 9, line['credit'], styledict['number_xf'])
                            sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                            sheet.write(rowx, 11, line['balance'], styledict['number_xf'])
                            sheet.write(rowx, 12, line['other'], styledict['text_xf'])
                            totals[0] += line['debit_currency']
                            totals[1] += line['debit']
                            totals[2] += line['credit_currency']
                            totals[3] += line['credit']
                            balance_currency = line['balance_currency']
                            balance = line['balance']
                            number = int(line['number'])
                            rowx += 1
                        totals[4] += balance_currency
                        totals[5] += balance
                    else:
                        sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                        sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
        #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                        sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                        sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                        sheet.write(rowx, 7, d[0], styledict['heading_xf-grey'])
                        sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
                        if self.is_warehouse and not data['is_from_invoice']:
                            sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                            sheet.write(rowx, 10, 'x', styledict['heading_xf-grey'])
                        else:
                            sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
                        
    #                     sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
    #             #        sheet.write(rowx, 12, initial_amount_currency, styledict['number_xf'])
    #             #        sheet.write(rowx, 13, initial_amount, styledict['number_xf'])
    #                     sheet.write(rowx, 10, d[1], styledict['grey_number_bold_xf1'])
    #                     sheet.write(rowx, 11, d[0], styledict['grey_number_bold_xf1'])
    #                     sheet.write(rowx, 12, 'x', styledict['heading_xf-grey'])
                        rowx += 1
                        
                        number = 0
                        balance = 0
                        balance_currency =0
                        d_dict={}
                        if self.is_date:
                            for line in d[2]:
                                if d_dict.has_key(line['date']):
                                    d_dict[line['date']]['debit']+=line['debit']
                                    d_dict[line['date']]['credit']+=line['credit']
                                else:
                                    d_dict[line['date']]={'debit':line['debit'],
                                                          'credit':line['credit'],
                                                          'account':line['account'],
                                                          'balance':line['balance'],
                                                          }
                            od = collections.OrderedDict(sorted(d_dict.items()))
                            m=1
                            for i in od:
    #                            print 'ii ',d_dict
                                sheet.write(rowx, 0, m, styledict['text_center_xf'])
                                sheet.row(rowx).height = 370
                                sheet.write(rowx, 1, i, styledict['text_center_xf'])
                                sheet.write(rowx, 2, '', styledict['text_xf'])
                                sheet.write(rowx, 3, od[i]['account'], styledict['text_xf'])
                                sheet.write(rowx, 4, '', styledict['text_xf'])
                                sheet.write(rowx, 5, od[i]['debit'], styledict['number_xf'])
                                sheet.write(rowx, 6, od[i]['credit'], styledict['number_xf'])
    #                             sheet.write(rowx, 7, d_dict[i]['balance'], styledict['number_xf'])
    #                             sheet.add_formula(rowx, 7, 
    #                                 '=H'+rowx-1+'+F'+rowx+'-G'+rowx+'', styledict['number_xf'])
    #                             sheet.write(rowx, 7, xlwt.Formula('H'+`rowx`+'+F'+`rowx+1`+'-G'+`rowx+1`+''), styledict['number_xf'])
                                
                                sheet.write(rowx, 8, '', styledict['text_xf'])
                                
                                m+=1
                                rowx+=1
                        else:
                            for line in d[2]:
                                sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                                sheet.row(rowx).height = 370
                                sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                                sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                                sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                                sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
        #                         sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
        #                         sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                                sheet.write(rowx, 5, line['debit'], styledict['number_xf'])
        #                         sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                                sheet.write(rowx, 6, line['credit'], styledict['number_xf'])
        #                         sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                                sheet.write(rowx, 7, line['balance'], styledict['number_xf'])
                                sheet.write(rowx, 8, line['other'], styledict['text_xf'])
                                branch=line['branch']
                                if self.is_warehouse and not data['is_from_invoice']:
                                    wh=''
                                    if line['so_id']:
                                        if line['so_id'].warehouse_id:
                                            wh=line['so_id'].warehouse_id.name
                                    sheet.write(rowx, 9, wh, styledict['text_xf'])
                                    sheet.write(rowx, 10, branch, styledict['text_xf'])
                                else:
                                    sheet.write(rowx, 9, branch, styledict['text_xf'])
                                
                                rowx+=1
                                totals[0] += line['debit_currency']
                                totals[1] += line['debit']
                                totals[2] += line['credit_currency']
                                totals[3] += line['credit']
                                balance_currency = line['balance_currency']
                                balance = line['balance']
                                number = int(line['number'])
                            rowx += 1
                        totals[4] += balance_currency
                        totals[5] += balance        
                if self.is_currency:
                    sheet.write_merge(rowx, rowx, 0, 5, u'НИЙТ ДҮН', styledict['heading_xf-1'])
                    sheet.write(rowx, 6, totals[0], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 7, totals[1], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 8, totals[2], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 9, totals[3], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 10, totals[4], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 11, totals[5], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 12, '', styledict['heading_xf-1'])
                    rowx += 1
                    if report_num == 0:
                        sheet.write_merge(rowx, rowx+1, 0, 12, '', styledict['text_xf'])
                        rowx += 2
                    report_num += 1
                    total_amount[0] += totals[0]
                    total_amount[1] += totals[1]
                    total_amount[2] += totals[2]
                    total_amount[3] += totals[3]
                    total_amount[4] += totals[4]
                    total_amount[5] += totals[5]
                else:
                    sheet.write_merge(rowx, rowx, 0, 4, u'НИЙТ ДҮН', styledict['heading_xf-1'])
                    sheet.write(rowx, 5, totals[1], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 6, totals[3], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 7, totals[5], styledict['grey_number_bold_xf'])
                    sheet.write(rowx, 8, '', styledict['heading_xf-1'])
                    if self.is_warehouse and not data['is_from_invoice']:
                        sheet.write(rowx, 9, '', styledict['heading_xf-1'])
                        sheet.write(rowx, 10, '', styledict['heading_xf-1'])
                    else:
                        sheet.write(rowx, 9, '', styledict['heading_xf-1'])
                    
                    rowx += 1
                    if report_num == 0:
                        sheet.write_merge(rowx, rowx+1, 0, 8, '', styledict['text_xf'])
                        rowx += 2
                    report_num += 1
                    total_amount[0] += totals[0]
                    total_amount[1] += totals[1]
                    total_amount[2] += totals[2]
                    total_amount[3] += totals[3]
                    total_amount[4] += totals[4]
                    total_amount[5] += totals[5]
            if self.is_currency:
                if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
                else: total_amount[0] = -total_amount[0]
                if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
                else: total_amount[1] = -total_amount[1]
                if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
                else: total_amount[2] = -total_amount[2]
                if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
                else: total_amount[3] = -total_amount[3]
                if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
                else: total_amount[4] = -total_amount[4]
                if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
                else: total_amount[5] = -total_amount[5]
                
                sheet.write_merge(rowx, rowx, 0, 5, u'НИЙТ ДҮН', styledict['heading_xf'])
                sheet.write(rowx, 6, total_amount[0], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 7, total_amount[1], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 8, total_amount[2], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 12, '', styledict['heading_xf'])
                inch = 60
                sheet.col(0).width = 12*inch
                sheet.col(1).width = 37*inch
                sheet.col(2).width = 38*inch
                sheet.col(3).width = 75*inch
                sheet.col(4).width = 80*inch
                sheet.col(5).width = 36*inch
                sheet.col(6).width = 40*inch
                sheet.col(7).width = 55*inch
                sheet.col(8).width = 40*inch
                sheet.col(9).width = 55*inch
                sheet.col(10).width = 40*inch
                sheet.col(11).width = int(59.5*inch)
                sheet.col(12).width = 42*inch
            else:
                if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
                else: total_amount[0] = -total_amount[0]
                if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
                else: total_amount[1] = -total_amount[1]
                if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
                else: total_amount[2] = -total_amount[2]
                if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
                else: total_amount[3] = -total_amount[3]
                if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
                else: total_amount[4] = -total_amount[4]
                if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
                else: total_amount[5] = -total_amount[5]
                
                sheet.write_merge(rowx, rowx, 0, 4, u'НИЙТ ДҮН', styledict['heading_xf'])
                sheet.write(rowx, 5, total_amount[1], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 6, total_amount[3], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 7, total_amount[5], styledict['number_boldtotal_xf'])
    #             sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
    #             sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
    #             sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
                sheet.write(rowx, 8, '', styledict['heading_xf'])
                if self.is_warehouse and not data['is_from_invoice']:
                    sheet.write(rowx, 9, '', styledict['heading_xf'])
                    sheet.write(rowx, 10, '', styledict['heading_xf'])
                else:
                    sheet.write(rowx, 9, '', styledict['heading_xf'])
                
                inch = 60
                sheet.col(0).width = 12*inch
                sheet.col(1).width = 37*inch
                sheet.col(2).width = 42*inch
                sheet.col(3).width = 85*inch
                sheet.col(4).width = 85*inch
                sheet.col(5).width = 36*inch
                sheet.col(6).width = 40*inch
                sheet.col(7).width = 55*inch
                sheet.col(8).width = 55*inch
#             sheet.col(9).width = 55*inch
#             sheet.col(10).width = 40*inch
#             sheet.col(11).width = int(59.5*inch)
#             sheet.col(12).width = 42*inch
            rowx+=3
        sheet.write(rowx+4, 3, u"Зөвшөөрсөн: Эд хариуцагч ......................................... /                                         /", 
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write(rowx+6, 3, u"Боловсруулсан: Нягтлан бодогч ......................................... /                                         /", 
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write(rowx+8, 3, u"Хянасан: Ерөнхий нягтлан бодогч .............................................../                                         /", 
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        

#         from StringIO import StringIO
#         buffer = StringIO()
#         from io import BytesIO
#         buffer = BytesIO()
#         book.save(buffer)
#         buffer.seek(0)
#          
#         filename = "partner_detail_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
#         out = base64.encodestring(buffer.getvalue())
#         buffer.close()
#          
#         excel_id = self.env['report.excel.output'].create({
#                                 'data':out,
#                                 'name':filename
#         })
#         mod_obj = self.env['ir.model.data']
#         form_res = mod_obj.get_object_reference('mw_base', 'action_excel_output_view')
#         form_id = form_res and form_res[1] or False
#         return {
#              'type' : 'ir.actions.act_url',
#              'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
#              'target': 'new',
#         }
        
        from io import BytesIO
        buffer = BytesIO()
        book.save(buffer)
        buffer.seek(0)
        
        filename = "partner_detail_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
        out = base64.encodestring(buffer.getvalue())
        buffer.close()
        
        excel_id = self.env['report.excel.output'].create({
                                'data':out,
                                'name':filename
        })
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }            
        #--------------------------------\open\---------------------------------------#

    def _amount_residual_open(self,lines):
        """ 
            account_partial_reconcile д currency цэнэглэх шаардлагагүй болсон, account_partial_reconcile цэнэглэнс
        """
#         print a
        #Валютын гүйлгээ орсон эсэх
        check_curr=False
        rate_currency_move=False
        compute_currency_id=False
        
        #Cr гүйлгээ тулгалтууд хасагдсаар Дт болоход - болох ба ингэхэд буцааж нэмэх ёстой
        check_amount=0
        for check in lines:
            if check.currency_id and check.amount_currency:
                check_curr=True
                compute_currency_id=check.currency_id.id
                rate_currency_move=check
#         print 'check_curr ',check_curr
        for line in lines:
#             print 'linelinelinelinelinelinelinelinelinelineline ',line
            if not line.account_id.reconcile:
#                 line.reconciled = False
#                 line.amount_residual = 0
#                 line.amount_residual_currency = 0
                continue
            #amounts in the partial reconcile table aren't signed, so we need to use abs()
            amount = abs(line.debit - line.credit)
            compute_amount_currency=0
            compute_amount_currency_non_residual=0
#             check_amount = amount
#             print 'check_amount ',check_amount
            amount_residual_currency = abs(line.amount_currency) or 0.0
            sign = 1 if (line.debit - line.credit) > 0 else -1
            if not line.debit and not line.credit and line.amount_currency and line.currency_id:
                #residual for exchange rate entries
                sign = 1 if float_compare(line.amount_currency, 0, precision_rounding=line.currency_id.rounding) == 1 else -1
#             print 'line.matched_debit_ids ',line.matched_debit_ids
#             print 'line.matched_credit_ids ',line.matched_credit_ids
#             print 'amount_residual_currency11111 ',amount_residual_currency
            for partial_line in (line.matched_debit_ids + line.matched_credit_ids):
                sign_partial_line = sign if partial_line.credit_move_id == line else (-1 * sign)
#                 print 'sign_partial_line ',sign_partial_line
#                 print 'line ',line.id
#                 print 'partial_line.amount ',partial_line.amount
#                         if partial_line.max_date>=self.date_from or partial_line.max_date<=self.date_to:#огнооны хооронд бол
#                 if partial_line.max_date<=self.date_to:#Тайлангийн огноононнс өмнө төлбөр бол төлөлтөнд орох
                if partial_line.all_max_date<=self.date_to:#Тайлангийн огноононнс өмнө төлбөр бол төлөлтөнд орох

                    amount += sign_partial_line * partial_line.amount
#                 check_amount +=sign_partial_line * partial_line.amount#Үргэжлүүлэх
#                 print 'check_amount ',check_amount
                #getting the date of the matched item to compute the amount_residual in currency
                if line.currency_id:
                    if partial_line.currency_id and partial_line.currency_id == line.currency_id:
#                         if partial_line.max_date>=self.date_from or partial_line.max_date<=self.date_to:#огнооны хооронд бол
#                         if partial_line.max_date<=self.date_to:#Тайлангийн огноононнс өмнө төлбөр бол төлөлтөнд орох
                        if partial_line.all_max_date<=self.date_to:#Тайлангийн огноононнс өмнө төлбөр бол төлөлтөнд орох
                            amount_residual_currency += sign_partial_line * partial_line.amount_currency
                    else:
                        if partial_line.credit_move_id.id==line.id:
                            rate_move=partial_line.debit_move_id
                        else:
                            rate_move=partial_line.credit_move_id
#                         print 'rate_move1111111111111111111111 ',rate_move
                        if rate_move.balance and rate_move.amount_currency:
                            rate = rate_move.amount_currency / rate_move.balance
                        else:
#                             date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
#                             print 'partial_line.all_max_date ',partial_line.all_max_date
#                             if partial_line.all_max_date:
#                                 date = partial_line.all_max_date
#                             else:
#                                 date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                            # statement_currency <> company_currency буюу банкнаас үүсэхэд төлөлтинй ханшаар бус үүссэн ханшаар авах
                            # ингэхэд amount_residual_currency 0 харин amount_residual ханшийн зөрүүгийн үлдэгдэглтэй
                            # Харин төлөлтийн буюу дээрх ханшаар max авахад Валютын үлдэгдэлтэй amount_residual_currency боловч amount_residual 0 байна.
                            # Иймд Тэхээр өөрийн ханшаар  үлдэгдлээ гаргаад, төлөлтийн өдрөөр тэгшитгэлтэй тулгах
                            date = line.date # partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                            rate = 1/line.currency_id.with_context(date=date).rate
                            #--------------------
#                             if partial_line.all_max_date:
#                                 date = partial_line.all_max_date
#                             else:
#                                 date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                        
                        
#                         if partial_line.max_date>=self.date_from or partial_line.max_date<=self.date_to:#огнооны хооронд бол
#                         if partial_line.max_date<=self.date_to:#Тайлангийн огноононнс өмнө төлбөр бол төлөлтөнд орох
                        if partial_line.all_max_date<=self.date_to:#Тайлангийн огноононнс өмнө төлбөр бол төлөлтөнд орох
                            amount_residual_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)
                        compute_amount_currency += sign_partial_line * line.currency_id.round(partial_line.amount * rate)
                elif check_curr:# Валютын төгрөгөөр төлөлт
                    if partial_line.credit_move_id.id==line.id:
                        rate_move=partial_line.credit_move_id#Эсрэгээр оруулж үзэх
                    else:
                        rate_move=partial_line.debit_move_id
                    if rate_move.balance and rate_move.amount_currency:
                        rate = rate_move.amount_currency / rate_move.balance
                        rate2=rate
                    else:
#                             date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
#                         print 'partial_line.all_max_date ',partial_line.all_max_date
                        if partial_line.all_max_date:
                            date = partial_line.all_max_date
                        else:
                            date = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
#                         rate = 1/line.currency_id.with_context(date=date).rate
                        rate=0
#                         print 'line ',line
#                         date2 = partial_line.credit_move_id.date if partial_line.debit_move_id == line else partial_line.debit_move_id.date
                        date2=line.date#Өөрийнхөө огноог авах
                        rate2=0
                        if rate_currency_move:#Валюттай гүйлгээ
#                             rate = 1/line.currency_id.with_context(date=date).rate
                            rate = 1/rate_currency_move.currency_id.with_context(date=date).rate
                            rate2  = 1/rate_currency_move.currency_id.with_context(date=date2).rate
                        #--------------------
                    compute_amount_currency += sign_partial_line * round(partial_line.amount * rate,2)  
#                     compute_amount_currency_non_residual += sign_partial_line * round(partial_line.amount * rate2,2) 
                    if line.debit>0:
#                         compute_amount_currency_non_residual =  round(line.debit * rate2,2) #Өөрийн үүссэн өдрийн ханш бол өөрөө тулгагдана
                        compute_amount_currency_non_residual =  round(line.debit * rate,2) #төлөлтийн ханшаар байж
                    else:
                        compute_amount_currency_non_residual =  round(line.credit * rate,2) 
#                     print 'compute_amount_currency ',compute_amount_currency  
#                 print 'amount_residual_currency3333333 ',amount_residual_currency               
            _logger.info(u'ttjv residual amount------------- %s / move_ids: %s!'%(amount,str(line.id)))
            #computing the `reconciled` field.
            reconciled = False
            digits_rounding_precision = line.company_id.currency_id.rounding
#             if float_is_zero(amount, precision_rounding=digits_rounding_precision):
#                 if line.currency_id and line.amount_currency:
# #                     print 'amount_residual_currency ',amount_residual_currency
#                     if float_is_zero(amount_residual_currency, precision_rounding=line.currency_id.rounding):
#                         reconciled = True
#                 else:
#                     print '1231'
#                     reconciled = True
        
        #Аль нэг нь 0 бол
            if float_is_zero(amount, precision_rounding=digits_rounding_precision) \
                or \
                (line.currency_id and line.amount_currency and \
                    float_is_zero(amount_residual_currency, precision_rounding=line.currency_id.rounding)):
                reconciled = True
#             print 'reconciled--- ',reconciled
#             print 'compute_amount_currency  ttjv: : ',compute_amount_currency
            amount_residual = line.company_id.currency_id.round(amount * sign)
            amount_residual_currency = line.currency_id and line.currency_id.round(amount_residual_currency * sign) or 0.0
#             print 'line ',line
            return reconciled,amount_residual_currency,amount_residual
#             if not line.currency_id:
# #                 if compute_amount_currency_non_residual==1560855.39:
# #                     print 'line.credit ',line.credit
# #                     print 'rate2 ',rate2
# #                     print a
#                 print 'sign ',sign
#                 line.compute_amount_currency = compute_amount_currency_non_residual * sign #or 0.0
#                 line.compute_currency_id = compute_currency_id
#                 line.compute_amount_residual_currency  = compute_amount_currency * sign #or 0.0
                
    def get_report_open_data(self, data):
        ''' Харилцагчийн өглөг авлагын гүйлгээг эхний үлдэгдэлийн хамтаар
            боловсруулж бэлтгэнэ. 
            НЭЭЛТТЭЙ ГҮЙЛГЭЭНҮҮДИЙГ ЗӨВХӨН
        '''
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        
        partner_ids = []
        if data['partner_id']:
            partner_ids = [data['partner_id'][0]]
#             child_ids = partner_obj.search([('parent_id','=',data['partner_id'][0])])
#             if child_ids :
#                 partner_ids = partner_ids + child_ids
        account_ids = []
        if data['account_id']:
#             account_ids = [data['account_id'][0]]
            account_ids = account_obj.search([('id','=',data['account_id'][0])])
        elif data['account_type'] == 'payable':
            account_ids = account_obj.search([('user_type_id.type','=','payable')])
        elif data['account_type'] == 'receivable':
            account_ids = account_obj.search([('user_type_id.type','=','receivable')])

        
        date_where = ""
#         if data['date_from'] == fiscalyear.date_start:
#             print 'if --------- 1'
#             date_where = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
#         else :
#             print 'if --------- 2'
        date_where = " m.date < '%s' " % data['date_from']
        open_where=""
        if self.is_open:
            open_where =" AND l.amount_residual<>0 " #and amount_residual_currency<>0 
        state_where = ""
        if data['target_move'] != 'all':
            state_where = " AND m.state = '%s' " % data['target_move']
        partner_where = " AND l.partner_id is not null "
        if partner_ids :
            partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        
        if self.company_id:
            partner_where += " AND l.company_id = {0}".format(self.company_id.id)
            
        a = []
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
                                                        state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        init_wheres = [""]
        
        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
#         print 'filters=======: ',filters
#         print 'init_where_params ',init_where_params
        
        for account in account_ids.ids:
#            cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
#                       "FROM account_move_line l "
#                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
#                       "LEFT JOIN account_period p ON (p.id=l.period_id) "
#                       "WHERE "+date_where+" AND p.fiscalyear_id = %s "
#                       " AND l.state <> 'draft' "+state_where+partner_where+" "
#                       " AND l.account_id = %s "
#                       "GROUP BY l.account_id ", (data['fiscalyear_id'], account))
#Эхний үлдэгдэл
    #         move_lines = dict(map(lambda x: (x, []), accounts.ids))
    #         print "data context ",data
#             if self.is_open:
#                 cr.execute("SELECT coalesce(sum(l.amount_residual),0.0), coalesce(sum(l.amount_residual_currency),0.0) "
#                        "FROM account_move_line l "
#                        "LEFT JOIN account_move m ON (m.id=l.move_id) "
#                        "WHERE "
#                        " state='posted' "+partner_where+" " 
#                        " "+filters+" "
#                        " AND l.account_id = " + str(account) + 
#                        " GROUP BY l.account_id ",tuple(init_where_params))
#                 fetched = cr.fetchone()
# #                 print "fetched::::::",fetched
#                 sresidual, samount_currency = fetched or (0,0)
#                 account_str = account_obj.browse(account)
#                 acc=account_str.code + ' ' + account_str.name
#                 if data['account_type'] == 'payable':
#                     initial_amount = -sresidual
#                     initial_amount_currency = (samount_currency <> 0 and -samount_currency) or 0
#                 else :
#                     initial_amount = sresidual
#                     initial_amount_currency = samount_currency
            
#             else:
#             print 'partner_where12 ',partner_where+' filters '+str(filters)+' init_where_params '+str(init_where_params)
            cr.execute("SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) "
                   "FROM account_move_line l "
                   "LEFT JOIN account_move m ON (m.id=l.move_id) "
                   "WHERE "
                   " state='posted' "+partner_where+" " 
                   " "+filters+" "
                   " AND l.account_id = " + str(account) + 
                   " GROUP BY l.account_id ",tuple(init_where_params))
#             AND l.state <> 'draft' 
            fetched = cr.fetchone()
#             print "fetched::::::",fetched
#             if fetched:
#                 q = "SELECT coalesce(sum(l.debit),0.0), coalesce(sum(l.credit),0.0), coalesce(sum(l.amount_currency),0.0) \
#                            FROM account_move_line l \
#                            LEFT JOIN account_move m ON (m.id=l.move_id) \
#                            LEFT JOIN account_period p ON (p.id=l.period_id) \
#                            WHERE "+date_where+" "+state_where \
#                            + partner_where+" AND l.account_id = " + str(account) + " \
#                            GROUP BY l.account_id "
#                 print 'Query;       ', q
#                 AND p.fiscalyear_id =  " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
            sdebit, scredit, samount_currency = fetched or (0,0,0)
            account_str = account_obj.browse(account)
            acc=account_str.code + ' ' + account_str.name
            if data['account_type'] == 'payable':
                initial_amount = scredit - sdebit
                initial_amount_currency = (samount_currency != 0 and -samount_currency) or 0
            else :
                initial_amount = sdebit - scredit
                initial_amount_currency = samount_currency
        
            balance, balance_currency = initial_amount, initial_amount_currency
            #balance, balance_currency = 0, 0
            move_line_obj = self.env['account.move.line']
            date_where1 = " m.date >= '%s' AND m.date <= '%s' " % (data['date_from'], data['date_to'])
            # if initial_bal_journal:
            #     date_where1 += "AND l.journal_id <> %s " % initial_bal_journal
#             and (j.special is null or j.special='f') 
            cr.execute("SELECT l.id  "
                       "FROM account_move_line l "
                       "LEFT JOIN account_move m ON (m.id=l.move_id) "
                       "LEFT JOIN res_partner r ON (l.partner_id=r.id) "
                       "LEFT JOIN account_journal j ON (j.id=l.journal_id) "
                       "WHERE "+date_where1+"  "
                       " "+state_where+partner_where+"  " #+open_where+" "
                       " AND l.account_id =  " + str(account)+" "
                       "ORDER BY l.date, r.name")
#             data['fiscalyear_id'], AND p.fiscalyear_id = %s
#                        "LEFT JOIN account_period p ON (p.id=l.period_id) "
            fetched = cr.fetchall()
            result = []
            number = 1
            if fetched or initial_amount!=0:
#                 q1 = "SELECT l.id  \
#                        FROM account_move_line l \
#                        LEFT JOIN account_move m ON (m.id=l.move_id) \
#                        LEFT JOIN res_partner r ON (l.partner_id=r.id) \
#                        LEFT JOIN account_journal j ON (j.id=l.journal_id) \
#                        WHERE "+date_where1+"  \
#                         "+state_where+partner_where+"  \
#                         AND l.account_id =  " + str(account)+" \
#                        ORDER BY l.date, r.name"
# #                            LEFT JOIN account_period p ON (p.id=l.period_id) \
# # AND p.fiscalyear_id = " + str(data['fiscalyear_id']) + " AND l.state <> 'draft' 
#                 print 'Q1 :  ', q1
                line_ids = [x[0] for x in fetched]

                check_payment_ids=[]#Төлөлтүүд тулгагдсан гүйлгээний төлөлтүүдийг оруулахгүй
                check_old_payment_ids=[]#Тухайн тайлант хугацаанд хамаарахгүй гүйлгээний төлөлт байсан ч харуулахгүй
                #Төлөлт шалгах 1 давталт
                for line in move_line_obj.browse(line_ids):
                    if data['account_type'] == 'payable':
                        if line.credit>0: #1. Үндсэн өр
#                             if (line.amount_residual<>0 or (line.amount_currency<>0 and line.amount_residual_currency<>0)):#Үндсэн өр нээлттэй бол
                            reconsiled,amount,amount_curr=self._amount_residual_open([line])
                            if reconsiled:
                                for md in line.matched_debit_ids:
                                    check_payment_ids.append(md.debit_move_id.id)
                                for mc in line.matched_credit_ids:
                                    check_payment_ids.append(md.credit_move_id.id)
                        else:#Дт Төлөлт эсвэл урьдчилгаа, хэрэв төлөлт байгаад reconcile гүйлгээ нь өмнө бол
                            for md in line.matched_debit_ids:
                                if md.debit_move_id.date<data['date_from']:
                                    check_old_payment_ids.append(line.id)
                            for mc in line.matched_credit_ids:
                                if mc.credit_move_id.date<data['date_from']:
                                    check_old_payment_ids.append(line.id)
                            
#                 print 'check_old_payment_ids ',check_old_payment_ids
#                 print 'check_payment_ids ',check_payment_ids
                #Эхний үлдэгдэл шалгах дахиад 1 давталт
                tailand_garah=[]
                tailand_garahgui=[]
                history_pool=self.env['account.currency.equalization.history']
                history_move_pool = self.env['account.currency.equalization.history.move']
                for line in move_line_obj.browse(line_ids):
                    print ('linelineline ',line.date)
                    tussan=False
                    rate_move_id=history_move_pool.search([('move_id','=',line.move_id.id)])
#                     print 'rate_move_id 1122 ',rate_move_id
                    if data['account_type'] == 'payable':#1. Өглөг бол Кт, АВлага Дт үлдэгдэлтэй бол гаргах //
#                         if line.move_id.id in real_rate_move_ids:#Ханш бол бүгдтусахгүй
                        if rate_move_id and rate_move_id.history_id.currency_move_line_id and \
                            rate_move_id.history_id.currency_move_line_id.date<data['date_from']:#Өмнөх гүйлгээний хэрэгжээгүй ханш бол бас эхний 
                            tussan=False
                        elif line.credit>0: #1. Үндсэн өр
#                             if (line.amount_residual<>0 or (line.amount_currency<>0 and line.amount_residual_currency<>0)):#Үндсэн өр нээлттэй бол
                            reconsiled,amount,amount_curr=self._amount_residual_open([line])
#                             print 'reconsiled222 ',reconsiled
#                             print 'line 111111 ',line
                            if not reconsiled:#Үндсэн өр нээлттэй бол хугацаа харгалзах
                                tailand_garah.append(line.id)
                                tussan=True
                        elif line.id not in check_payment_ids and line.id not in check_old_payment_ids:#төлөлт биш бас хуучин төлбөрийн төлөлт биш
                            reconsiled,amount,amount_curr=self._amount_residual_open([line])
                            if not reconsiled:
                                tailand_garah.append(line.id)
                                tussan=True
#                         elif line.id in check_old_payment_ids:
                            
                        if not tussan:#Тайланд гарахгүй бол эхний үлдэргдэл дээр оч
                            tailand_garahgui.append(line.id)
                            if line.debit>0:
                                initial_amount -= line.debit
                                if line.amount_currency!=0:
                                    initial_amount_currency -= line.amount_currency
                            else:#CR
                                initial_amount += line.credit
                                if line.amount_currency!=0:
                                    initial_amount_currency += abs(line.amount_currency)
#                 balance, balance_currency = initial_amount, initial_amount_currency
                #Тайланд тусч буй гүйлгээний ханш бол шууд үндсэн гүйлгээний дүнг засах
                rated_history=history_pool.search([('currency_move_line_id','in',tailand_garah)])
                history_moves={}
                rate_aml_ids=[]
                for his in rated_history:
                    for hline in his.equalization_move_lines:
                        if hline.move_id:
                            for aml in hline.move_id.line_ids:
                                if aml.id in tailand_garah:
                                    rate_aml_ids.append(aml.id)
                                    if history_moves.get(his.currency_move_line_id.id):
                                        history_moves[his.currency_move_line_id.id]['amount']+=aml.debit-aml.credit
                                        history_moves[his.currency_move_line_id.id]['aml_ids'].append(aml.id)
                                    else:
                                        history_moves[his.currency_move_line_id.id]={'amount':aml.debit-aml.credit,
                                                                                     'aml_ids':[aml.id]
                                                                                     }
#                 #гарахгүй unreal бол эхний үлд
#                 rated_history=history_pool.search([('currency_move_line_id','not in',tailand_garah)])
                #Рийл ханшууд
                real_history_moves={}
                real_rate_aml_ids=[]
                if tailand_garah:
                    cr.execute("select l.id as rate_aml,r.account_move_line_id as main_payable \
                                                            from account_move_account_move_line_rel r \
                                                            left join account_move_line l on r.account_move_id=l.move_id \
                                                            where l.id in ("+','.join(map(str,tailand_garah))+") ")
#                     cr.execute("select * from account_move_account_move_line_rel ")

                    
                    fetched_real = cr.dictfetchall()   
#                     print 'fetched_real2222222 ',fetched_real
                    change_rate_amls=[]
                    for r in fetched_real:
    #                     real_rate_move_ids.append(r[0])  
                        if r['rate_aml'] in tailand_garah:#Тайланд гарах бол гарахгүй болгох
                            if r['rate_aml'] not in real_rate_aml_ids:#дахин хасагдахгүй байх
                                real_rate_aml_ids.append(r['rate_aml'])
                                #1 үндсэн өр нь тайланд гарах бол 
    #                             print 'rate_amlrate_amlrate_amlrate_aml',r['rate_aml']
                                if r['main_payable'] in tailand_garah:
                                    aml = self.env['account.move.line'].browse(r['rate_aml'])
                                    if real_history_moves.get(r['main_payable']):
                                        real_history_moves[r['main_payable']]['amount']+=aml.debit-aml.credit
                                        real_history_moves[r['main_payable']]['aml_ids'].append(aml.id)
                                    else:
                                        real_history_moves[r['main_payable']]={'amount':aml.debit-aml.credit,
                                                                                 'aml_ids':[aml.id]
                                                                                 } 
                                else:#Үгүй бол эхний үлдэглийг хөдөлгөх
                                    line = self.env['account.move.line'].browse(r['rate_aml'])
                                    if line.debit>0:
                                        initial_amount -= line.debit
                                        if line.amount_currency!=0:
                                            initial_amount_currency -= line.amount_currency
                                    else:#CR
                                        initial_amount += line.credit
                                        if line.amount_currency!=0:
                                            initial_amount_currency += abs(line.amount_currency)
                balance, balance_currency = initial_amount, initial_amount_currency                                                                                    
#                 print 'history_moves123 ',history_moves
                for line in move_line_obj.browse(line_ids):
                    if data['account_type'] == 'payable':#1. Өглөг бол Кт, АВлага Дт үлдэгдэлтэй бол гаргах //
#                         if line.credit>0: #1. Үндсэн өр
# #                             if (line.amount_residual<>0 or (line.amount_currency<>0 and line.amount_residual_currency<>0)):#Үндсэн өр нээлттэй бол
#                             reconsiled,amount,amount_curr=self._amount_residual_open([line])
#                             print 'reconsiled222 ',reconsiled
#                             print 'line 111111 ',line
#                             if not reconsiled:#Үндсэн өр нээлттэй бол хугацаа харгалзах
                        if line.id in tailand_garah:
                                row = {}
                                row['number'] = str(number)
                                row['date'] = line.date
                                row['name'] = line.move_id.ref or line.move_id.name
                                row['account'] = account_str.code + ' ' + account_str.name
                                debit_lines = []
                                credit_lines = []
                                #rate moves are add
                                debit = line.debit
                                credit = line.credit
                                if line.id in rate_aml_ids:
                                    continue
                                if line.id in history_moves:
                                    if debit>0:
                                        debit-=history_moves[line.id]['amount']
                                    else:
                                        credit-=history_moves[line.id]['amount']
                                        
                                if line.id in real_rate_aml_ids:
                                    continue
                                if line.id in real_history_moves:
                                    if debit>0:
                                        debit-=real_history_moves[line.id]['amount']
                                    else:
                                        credit-=real_history_moves[line.id]['amount']                                        
                                        
                                for other_line in line.move_id.line_ids :
                                    if other_line.id != line.id :
                                        if other_line.debit > 0 and u'Дт:'+other_line.account_id.code not in debit_lines:
                                            debit_lines.append(u'Дт:'+other_line.account_id.code)
                                        elif other_line.credit > 0 and u'Кт:'+other_line.account_id.code not in credit_lines:
                                            credit_lines.append(u'Кт:'+other_line.account_id.code)
                                row['other'] = '\n'.join(debit_lines[:5]) + '\n'+ '\n'.join(credit_lines[:5])
                                row['partner'] = line.partner_id.name
                                row['narration'] = line.name or line.narration
                                row['currency'] = (line.currency_id and line.currency_id.name) or ''
                                row['debit_currency'] = (line.debit > 0 and line.amount_currency) or 0
                                row['debit'] = debit
                                row['credit_currency'] = (line.credit > 0 and abs(line.amount_currency)) or 0
                                row['credit'] = credit
                                if data['account_type'] == 'payable':
                                    balance = balance + credit - debit
            #                         balance_currency += line.amount_currency if line.credit == 0 else line.amount_currency
                                    if line.amount_currency!=0:
                                        if line.credit>0 :
                                            balance_currency += abs(line.amount_currency)
                                        else:
                                            balance_currency -= abs(line.amount_currency)
                                else :
                                    balance = balance + debit - credit
            #                         balance_currency += line.amount_currency if line.debit == 0 else line.amount_currency
                                    if line.amount_currency!=0:
                                        if line.debit>0 :
                                            balance_currency += abs(line.amount_currency)
                                        else:
                                            balance_currency -= abs(line.amount_currency)
            
                                row['balance_currency'] = balance_currency
                                row['balance'] = balance
                                number += 1
#                                 if self.is_open:
#                                     if debit<>0 or credit<>0:
#                                         result.append(row)
#                                 else:
                                result.append(row)
                        
                a.append([initial_amount, initial_amount_currency, result,acc])
        #return initial_amount, initial_amount_currency, result
        return a
                    

    def _make_excel_open(self, data):
        '''Нээлттэй инвойс болон гүйлгээг зөвхөн төлөлтүүдтэй харуулах.
        '''
        account_obj = self.env['account.account']
        styledict = self.env['abstract.report.excel'].get_easyxf_styles()
        
        ezxf = xlwt.easyxf
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet(u'Payable Receivable Detail')

        data = data['form']
        
#         account = account_obj.browse(cr, uid, data['account_id'], context=context)
        partner = False
        if data['partner_id']:
            partner = self.env['res.partner'].browse(data['partner_id'][0])
        
        date_str = '%s-%s' % (
            datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
            datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
        )
        '''
        if context['report_type'] == 'payable' :
            title = u'Маягт ӨГ-2'
            report_name = u'Өглөгийн дансны дэлгэрэнгүй бүртгэл'
        else :
            title = u'Маягт АВ-2'
            report_name = u'Авлагын дансны дэлгэрэнгүй бүртгэл'
        '''
        title = ''
        report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
        sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
        sheet.write(5, 8, u'Тайлант хугацаа: %s' % date_str, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
        sheet.write(5, 0, u"Харилцагчийн код: %s" % ((partner and (partner.ref or '')) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(6, 0, u"Харилцагчийн нэр: %s" % ((partner and partner.name) or ''), xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;'))
        sheet.write(6, 8, time.strftime('%Y-%m-%d %H:%M'), xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;'))
        
        rowx = 8
        
        reports = ['receivable','payable']
        
        total_amount=[0,0,0,0,0,0]
        tmp_amount = [0,0,0,0,0,0]
        report_num = 0
        for report in reports:
            data['account_type'] = report
#             print 'data[] ',data['account_id']
            if data['account_id']:
                acc = account_obj.browse(data['account_id'][0])
                if acc.user_type_id.type != report: continue
            if self.is_currency:
                sheet.write_merge(rowx, rowx+2, 0, 0, u'№', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+2, 1, 1, u'Огноо', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+2, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+2, 3, 3, u'Данс', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+2, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx, 6, 9, u'Гүйлгээний дүн', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx, 10, 11, u'Үлдэгдэл', styledict['heading_xf'])
                rowx += 1
                sheet.write_merge(rowx, rowx, 6, 7, u'Дебет', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx, 8, 9, u'Кредит', styledict['heading_xf'])
                #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx, 10, 11, (report == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                sheet.write_merge(rowx-1, rowx+1, 12, 12, u'Харьцсан данс', styledict['heading_xf'])
                rowx += 1
                sheet.write(rowx, 6, u'Валют', styledict['heading_xf'])
                sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
                sheet.write(rowx, 8, u'Валют', styledict['heading_xf'])
                sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
                sheet.write(rowx, 10, u'Валют', styledict['heading_xf'])
                sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
                rowx += 1
            else:
                sheet.write_merge(rowx, rowx+1, 0, 0, u'№', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+1, 1, 1, u'Огноо', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+1, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+1, 3, 3, u'Данс', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx+1, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
#                 sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
                sheet.write_merge(rowx, rowx, 5, 6, u'Гүйлгээний дүн', styledict['heading_xf'])
                sheet.write(rowx, 7, u'Үлдэгдэл', styledict['heading_xf'])
                rowx += 1
                sheet.write(rowx, 5, u'Дебет', styledict['heading_xf'])
                sheet.write(rowx, 6, u'Кредит', styledict['heading_xf'])
                #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                sheet.write(rowx, 7, (report == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
                sheet.write_merge(rowx-1, rowx, 8, 8, u'Харьцсан данс', styledict['heading_xf'])
#                 rowx += 1
#                 sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
#                 sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
#                 sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
                rowx += 1            
            #initial_amount, initial_amount_currency, lines = report_service.get_report_data(cr, uid, data, context=context)
#             datas = report_service.get_report_data(cr, uid, data, context=context)
            datas = self.get_report_open_data(data)

            #test
            totals = [0,0,0,0,0,0]
            for d in datas:
                if self.is_currency:
                    sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                    sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
    #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
    #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                    sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                    sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                    sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                    sheet.write(rowx, 7, 'x', styledict['heading_xf-grey'])
                    sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
                    sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
            #        sheet.write(rowx, 12, initial_amount_currency, styledict['number_xf'])
            #        sheet.write(rowx, 13, initial_amount, styledict['number_xf'])
                    sheet.write(rowx, 10, d[1], styledict['grey_number_bold_xf1'])
                    sheet.write(rowx, 11, d[0], styledict['grey_number_bold_xf1'])
                    sheet.write(rowx, 12, 'x', styledict['heading_xf-grey'])
                    rowx += 1
                    
                    number = 0
                    balance = 0
                    balance_currency =0
                    for line in d[2]:
                        sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                        sheet.row(rowx).height = 370
                        sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                        sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                        sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                        sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
                        sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
                        sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                        sheet.write(rowx, 7, line['debit'], styledict['number_xf'])
                        sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                        sheet.write(rowx, 9, line['credit'], styledict['number_xf'])
                        sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                        sheet.write(rowx, 11, line['balance'], styledict['number_xf'])
                        sheet.write(rowx, 12, line['other'], styledict['text_xf'])
                        totals[0] += line['debit_currency']
                        totals[1] += line['debit']
                        totals[2] += line['credit_currency']
                        totals[3] += line['credit']
                        balance_currency = line['balance_currency']
                        balance = line['balance']
                        number = int(line['number'])
                        rowx += 1
                    totals[4] += balance_currency
                    totals[5] += balance
                else:
                    sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
                    sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
    #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
    #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
                    sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
                    sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
                    sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
                    sheet.write(rowx, 7, d[0], styledict['heading_xf-grey'])
                    sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
#                     sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
#             #        sheet.write(rowx, 12, initial_amount_currency, styledict['number_xf'])
#             #        sheet.write(rowx, 13, initial_amount, styledict['number_xf'])
#                     sheet.write(rowx, 10, d[1], styledict['grey_number_bold_xf1'])
#                     sheet.write(rowx, 11, d[0], styledict['grey_number_bold_xf1'])
#                     sheet.write(rowx, 12, 'x', styledict['heading_xf-grey'])
                    rowx += 1
                    
                    number = 0
                    balance = 0
                    balance_currency =0
                    d_dict={}
                    if self.is_date:
                        for line in d[2]:
                            if d_dict.has_key(line['date']):
                                d_dict[line['date']]['debit']+=line['debit']
                                d_dict[line['date']]['credit']+=line['credit']
                            else:
                                d_dict[line['date']]={'debit':line['debit'],
                                                      'credit':line['credit'],
                                                      'account':line['account'],
                                                      'balance':line['balance'],
                                                      }
                        od = collections.OrderedDict(sorted(d_dict.items()))
                        m=1
                        for i in od:
#                            print 'ii ',d_dict
                            sheet.write(rowx, 0, m, styledict['text_center_xf'])
                            sheet.row(rowx).height = 370
                            sheet.write(rowx, 1, i, styledict['text_center_xf'])
                            sheet.write(rowx, 2, '', styledict['text_xf'])
                            sheet.write(rowx, 3, od[i]['account'], styledict['text_xf'])
                            sheet.write(rowx, 4, '', styledict['text_xf'])
                            sheet.write(rowx, 5, od[i]['debit'], styledict['number_xf'])
                            sheet.write(rowx, 6, od[i]['credit'], styledict['number_xf'])
#                             sheet.write(rowx, 7, d_dict[i]['balance'], styledict['number_xf'])
#                             sheet.add_formula(rowx, 7, 
#                                 '=H'+rowx-1+'+F'+rowx+'-G'+rowx+'', styledict['number_xf'])
#                             sheet.write(rowx, 7, xlwt.Formula('H'+`rowx`+'+F'+`rowx+1`+'-G'+`rowx+1`+''), styledict['number_xf'])
                            
                            sheet.write(rowx, 8, '', styledict['text_xf'])
                            
                            m+=1
                            rowx+=1
                    else:
                        for line in d[2]:
                            sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
                            sheet.row(rowx).height = 370
                            sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
                            sheet.write(rowx, 2, line['name'], styledict['text_xf'])
                            sheet.write(rowx, 3, line['account'], styledict['text_xf'])
                            sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
    #                         sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
    #                         sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 5, line['debit'], styledict['number_xf'])
    #                         sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
                            sheet.write(rowx, 6, line['credit'], styledict['number_xf'])
    #                         sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
                            sheet.write(rowx, 7, line['balance'], styledict['number_xf'])
                            sheet.write(rowx, 8, line['other'], styledict['text_xf'])
                            rowx+=1
                            totals[0] += line['debit_currency']
                            totals[1] += line['debit']
                            totals[2] += line['credit_currency']
                            totals[3] += line['credit']
                            balance_currency = line['balance_currency']
                            balance = line['balance']
                            number = int(line['number'])
                        rowx += 1
                    totals[4] += balance_currency
                    totals[5] += balance        
            if self.is_currency:
                sheet.write_merge(rowx, rowx, 0, 5, u'НИЙТ ДҮН', styledict['heading_xf-1'])
                sheet.write(rowx, 6, totals[0], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 7, totals[1], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 8, totals[2], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 9, totals[3], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 10, totals[4], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 11, totals[5], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 12, '', styledict['heading_xf-1'])
                rowx += 1
                if report_num == 0:
                    sheet.write_merge(rowx, rowx+1, 0, 12, '', styledict['text_xf'])
                    rowx += 2
                report_num += 1
                total_amount[0] += totals[0]
                total_amount[1] += totals[1]
                total_amount[2] += totals[2]
                total_amount[3] += totals[3]
                total_amount[4] += totals[4]
                total_amount[5] += totals[5]
            else:
                sheet.write_merge(rowx, rowx, 0, 4, u'НИЙТ ДҮН', styledict['heading_xf-1'])
                sheet.write(rowx, 5, totals[1], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 6, totals[3], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 7, totals[5], styledict['grey_number_bold_xf'])
                sheet.write(rowx, 8, '', styledict['heading_xf-1'])
                rowx += 1
                if report_num == 0:
                    sheet.write_merge(rowx, rowx+1, 0, 8, '', styledict['text_xf'])
                    rowx += 2
                report_num += 1
                total_amount[0] += totals[0]
                total_amount[1] += totals[1]
                total_amount[2] += totals[2]
                total_amount[3] += totals[3]
                total_amount[4] += totals[4]
                total_amount[5] += totals[5]
        if self.is_currency:
            if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
            else: total_amount[0] = -total_amount[0]
            if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
            else: total_amount[1] = -total_amount[1]
            if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
            else: total_amount[2] = -total_amount[2]
            if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
            else: total_amount[3] = -total_amount[3]
            if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
            else: total_amount[4] = -total_amount[4]
            if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
            else: total_amount[5] = -total_amount[5]
            
            sheet.write_merge(rowx, rowx, 0, 5, u'НИЙТ ДҮН', styledict['heading_xf'])
            sheet.write(rowx, 6, total_amount[0], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 7, total_amount[1], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 8, total_amount[2], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 12, '', styledict['heading_xf'])
            inch = 60
            sheet.col(0).width = 12*inch
            sheet.col(1).width = 37*inch
            sheet.col(2).width = 38*inch
            sheet.col(3).width = 75*inch
            sheet.col(4).width = 80*inch
            sheet.col(5).width = 36*inch
            sheet.col(6).width = 40*inch
            sheet.col(7).width = 55*inch
            sheet.col(8).width = 40*inch
            sheet.col(9).width = 55*inch
            sheet.col(10).width = 40*inch
            sheet.col(11).width = int(59.5*inch)
            sheet.col(12).width = 42*inch
        else:
            if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
            else: total_amount[0] = -total_amount[0]
            if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
            else: total_amount[1] = -total_amount[1]
            if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
            else: total_amount[2] = -total_amount[2]
            if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
            else: total_amount[3] = -total_amount[3]
            if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
            else: total_amount[4] = -total_amount[4]
            if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
            else: total_amount[5] = -total_amount[5]
            
            sheet.write_merge(rowx, rowx, 0, 4, u'НИЙТ ДҮН', styledict['heading_xf'])
            sheet.write(rowx, 5, total_amount[1], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 6, total_amount[3], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 7, total_amount[5], styledict['number_boldtotal_xf'])
#             sheet.write(rowx, 9, total_amount[3], styledict['number_boldtotal_xf'])
#             sheet.write(rowx, 10, total_amount[4], styledict['number_boldtotal_xf'])
#             sheet.write(rowx, 11, total_amount[5], styledict['number_boldtotal_xf'])
            sheet.write(rowx, 8, '', styledict['heading_xf'])
            inch = 60
            sheet.col(0).width = 12*inch
            sheet.col(1).width = 37*inch
            sheet.col(2).width = 42*inch
            sheet.col(3).width = 85*inch
            sheet.col(4).width = 85*inch
            sheet.col(5).width = 36*inch
            sheet.col(6).width = 40*inch
            sheet.col(7).width = 55*inch
            sheet.col(8).width = 55*inch
#             sheet.col(9).width = 55*inch
#             sheet.col(10).width = 40*inch
#             sheet.col(11).width = int(59.5*inch)
#             sheet.col(12).width = 42*inch
        sheet.write(rowx+4, 3, u"Зөвшөөрсөн: Эд хариуцагч ......................................... /                                         /", 
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write(rowx+6, 3, u"Боловсруулсан: Нягтлан бодогч ......................................... /                                         /", 
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.write(rowx+8, 3, u"Хянасан: Ерөнхий нягтлан бодогч .............................................../                                         /", 
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        

        from StringIO import StringIO
        buffer = StringIO()
        book.save(buffer)
        buffer.seek(0)
         
        filename = "partner_detail_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
        out = base64.encodestring(buffer.getvalue())
        buffer.close()
         
        excel_id = self.env['report.excel.output'].create({
                                'data':out,
                                'name':filename
        })
        mod_obj = self.env['ir.model.data']
        form_res = mod_obj.get_object_reference('mw_base', 'action_excel_output_view')
        form_id = form_res and form_res[1] or False
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
                
                

        
    def print_report_html(self):
        self.ensure_one()
        result_context=dict(self._context or {})
        self.ensure_one()
        result_context=dict(self._context or {})
        
#         data['form'].update(self._build_contexts(data))
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'journal_ids', 'target_move'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=self.env.context.get('lang') or 'en_US')
         
        data['form'].update(self._build_contexts(data))
        form = self.read()[0]
        data['account_id']=self.account_id and self.account_id.id or False
        data['partner_id']=self.partner_id and [self.partner_id.id] or []
        
        data['date_from']=self.date_from
        data['date_to']=self.date_to
        data['target_move']=self.target_move
        reports = ['receivable','payable']
        
        cr=self._cr
        account_obj = self.env['account.account']
        partner_obj = self.env['res.partner']
        
        
        total_amount=[0,0,0,0,0,0]
        tmp_amount = [0,0,0,0,0,0]
        all_datas=[]
        report_num = 0
        partners=[]
        if data['partner_id']:
            partners = [self.env['res.partner'].browse(data['partner_id'][0])]
        elif self.tag_id:
            partners = self.env['res.partner'].search([('category_id','in',[self.tag_id.id])])
            
        title = ''
#         report_name = u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан'
#         sheet.write(0, 0, u'Байгууллагын нэр: %s' % self.env.user.company_id.name, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#         sheet.write(0, 7, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#         sheet.write_merge(2, 2, 0, 8, report_name, xlwt.easyxf('font:bold on, height 250;align:wrap off,vert centre,horiz centre;'))
        rowx = 5
        for partner in partners:
            for report in reports:
                data['account_type'] = report
    #             print 'data[] ',data['account_id']
                if data['account_id']:
                    acc = account_obj.browse(data['account_id'][0])
                    if acc.user_type_id.type != report: continue
    #             if False:#self.is_currency:
    #                  return True#Daraa
    # #                 sheet.write_merge(rowx, rowx+2, 0, 0, u'№', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx+2, 1, 1, u'Огноо', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx+2, 2, 2, u'Баримтын дугаар', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx+2, 3, 3, u'Данс', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx+2, 4, 4, u'Гүйлгээний утга', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx+2, 5, 5, u'Валютын төрөл', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx, 6, 9, u'Гүйлгээний дүн', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx, 10, 11, u'Үлдэгдэл', styledict['heading_xf'])
    # #                 rowx += 1
    # #                 sheet.write_merge(rowx, rowx, 6, 7, u'Дебет', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx, 8, 9, u'Кредит', styledict['heading_xf'])
    # #                 #sheet.write_merge(rowx, rowx, 12, 13, (context['report_type'] == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx, rowx, 10, 11, (report == 'payable' and u'Кредит') or u'Дебет', styledict['heading_xf'])
    # #                 sheet.write_merge(rowx-1, rowx+1, 12, 12, u'Харьцсан данс', styledict['heading_xf'])
    # #                 rowx += 1
    # #                 sheet.write(rowx, 6, u'Валют', styledict['heading_xf'])
    # #                 sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
    # #                 sheet.write(rowx, 8, u'Валют', styledict['heading_xf'])
    # #                 sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
    # #                 sheet.write(rowx, 10, u'Валют', styledict['heading_xf'])
    # #                 sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
    # #                 rowx += 1
    #             else:
    # #                 rowx += 1
    # #                 sheet.write(rowx, 7, u'Төгрөг', styledict['heading_xf'])
    # #                 sheet.write(rowx, 9, u'Төгрөг', styledict['heading_xf'])
    # #                 sheet.write(rowx, 11, u'Төгрөг', styledict['heading_xf'])
    #                 rowx += 1            
                datas = self.get_report_data(data,partner)
                totals = [0,0,0,0,0,0]
                for d in datas:
                    if False:#self.is_currency:#DAraa
    #                     sheet.write(rowx, 0, 'x', styledict['heading_xf-grey'])
    #                     sheet.write_merge(rowx,rowx, 1,3,d[3], styledict['heading_xf-grey'])
    #     #                 sheet.write(rowx, 2, 'x', styledict['heading_xf-grey'])
    #     #                 sheet.write(rowx, 3, d[3], styledict['heading_xf-grey'])
    #                     sheet.write(rowx, 4, u'Эхний үлдэгдэл', styledict['heading_xf-grey'])
    #                     sheet.write(rowx, 5, 'x', styledict['heading_xf-grey'])
    #                     sheet.write(rowx, 6, 'x', styledict['heading_xf-grey'])
    #                     sheet.write(rowx, 7, 'x', styledict['heading_xf-grey'])
    #                     sheet.write(rowx, 8, 'x', styledict['heading_xf-grey'])
    #                     sheet.write(rowx, 9, 'x', styledict['heading_xf-grey'])
    #             #        sheet.write(rowx, 12, initial_amount_currency, styledict['number_xf'])
    #             #        sheet.write(rowx, 13, initial_amount, styledict['number_xf'])
    #                     sheet.write(rowx, 10, d[1], styledict['grey_number_bold_xf1'])
    #                     sheet.write(rowx, 11, d[0], styledict['grey_number_bold_xf1'])
    #                     sheet.write(rowx, 12, 'x', styledict['heading_xf-grey'])
    #                     rowx += 1
    #                     
    #                     number = 0
    #                     balance = 0
    #                     balance_currency =0
                        for line in d[2]:
    #                         
    #                         sheet.write(rowx, 0, line['number'], styledict['text_center_xf'])
    #                         sheet.row(rowx).height = 370
    #                         sheet.write(rowx, 1, line['date'], styledict['date_center_xf'])
    #                         sheet.write(rowx, 2, line['name'], styledict['text_xf'])
    #                         sheet.write(rowx, 3, line['account'], styledict['text_xf'])
    #                         sheet.write(rowx, 4, line['narration'], styledict['text_xf'])
    #                         sheet.write(rowx, 5, line['currency'], styledict['text_center_xf'])
    #                         sheet.write(rowx, 6, line['debit_currency'], styledict['number_xf'])
    #                         sheet.write(rowx, 7, line['debit'], styledict['number_xf'])
    #                         sheet.write(rowx, 8, line['credit_currency'], styledict['number_xf'])
    #                         sheet.write(rowx, 9, line['credit'], styledict['number_xf'])
    #                         sheet.write(rowx, 10, line['balance_currency'], styledict['number_xf'])
    #                         sheet.write(rowx, 11, line['balance'], styledict['number_xf'])
    #                         sheet.write(rowx, 12, line['other'], styledict['text_xf'])
    #                         totals[0] += line['debit_currency']
    #                         totals[1] += line['debit']
    #                         totals[2] += line['credit_currency']
    #                         totals[3] += line['credit']
                            balance_currency = line['balance_currency']
                            balance = line['balance']
    #                         number = int(line['number'])
    #                         rowx += 1
                        totals[4] += balance_currency
                        totals[5] += balance
                    else:
                        
                        row_data={
                                    'Dd':'x',
                                    'Date':'',
                                    'Number':'',
                                    'Account':d[3],
                                    'Name':u'Эхний үлдэгдэл',
                                    'Debit':'x',
                                    'Credit':'x',
                                    'C2':d[0],
                                    'CAccount':'x',
                                    'Branch':'x'
                                    }
                        all_datas.append(row_data)
                        number = 0
                        balance = 0
                        balance_currency =0
                        d_dict={}
                        if self.is_date:
                            for line in d[2]:
                                if d_dict.has_key(line['date']):
                                    d_dict[line['date']]['debit']+=line['debit']
                                    d_dict[line['date']]['credit']+=line['credit']
                                else:
                                    d_dict[line['date']]={'debit':line['debit'],
                                                          'credit':line['credit'],
                                                          'account':line['account'],
                                                          'balance':line['balance'],
                                                          }
                            od = collections.OrderedDict(sorted(d_dict.items()))
                            m=1
                            for i in od:
                                row_data={
                                            'Dd':m,
                                            'Date':i,
                                            'Number':'',
                                            'Account':od[i]['account'],
                                            'Name':'',
                                            'Debit':od[i]['debit'],
                                            'Credit':od[i]['credit'],
                                            'C2':'',
                                            'CAccount':'',
                                            'Branch':''
                                            }
                                all_datas.append(row_data)                            
                                m+=1
                        else:
                            for line in d[2]:
                                branch=line['branch']
                                row_data={
                                            'Dd':line['number'],
                                            'Date':line['date'],
                                            'Number':line['name'],
                                            'Account':line['account'],
                                            'Name':line['narration'],
                                            'Debit':line['debit'],
                                            'Credit':line['credit'],
                                            'C2':line['balance'],
                                            'CAccount':line['other'],
                                            'Branch':branch
                                            }
                                all_datas.append(row_data)  
                                
                                totals[0] += line['debit_currency']
                                totals[1] += line['debit']
                                totals[2] += line['credit_currency']
                                totals[3] += line['credit']
                                balance_currency = line['balance_currency']
                                balance = line['balance']
                                number = int(line['number'])
                        totals[4] += balance_currency
                        totals[5] += balance             
    
    
                    row_data={
                                'Dd':'',
                                'Date':'',
                                'Number':'',
                                'Account':'',
                                'Name':'',
                                'Debit':'',
                                'Credit':'',
                                'C2':'',
                                'CAccount':'',
                                'Branch':''
                                }
                    all_datas.append(row_data) 
                row_data={
                            'Dd':'x',
                            'Date':'',
                            'Number':'',
                            'Account':'',
                            'Name':u'НИЙТ ДҮН',
                            'Debit':totals[1],
                            'Credit':totals[3],
                            'C2':totals[5],
                            'CAccount':'',
                            'Branch':''
                            }
                all_datas.append(row_data)
                total_amount[0] += totals[0]
                total_amount[1] += totals[1]
                total_amount[2] += totals[2]
                total_amount[3] += totals[3]
                total_amount[4] += totals[4]
                total_amount[5] += totals[5]
            if total_amount[0] !=  totals[0]: total_amount[0] -= 2*totals[0]
            else: total_amount[0] = -total_amount[0]
            if total_amount[1] !=  totals[1]: total_amount[1] -= 2*totals[1]
            else: total_amount[1] = -total_amount[1]
            if total_amount[2] !=  totals[2]: total_amount[2] -= 2*totals[2]
            else: total_amount[2] = -total_amount[2]
            if total_amount[3] !=  totals[3]: total_amount[3] -= 2*totals[3]
            else: total_amount[3] = -total_amount[3]
            if total_amount[4] !=  totals[4]: total_amount[4] -= 2*totals[4]
            else: total_amount[4] = -total_amount[4]
            if total_amount[5] !=  totals[5]: total_amount[5] -= 2*totals[5]
            else: total_amount[5] = -total_amount[5]
            
            row_data={
                        'Dd':'x',
                        'Date':'',
                        'Number':'',
                        'Account':'',
                        'Name':u'НИЙТ ДҮН БҮГД',
                        'Debit':total_amount[1],
                        'Credit':total_amount[3],
                        'C2':total_amount[5],
                        'CAccount':'',
                        'Branch':''
                        }
            all_datas.append(row_data)        
                    
#         print ('all_datas ',all_datas)
        ir_model_obj = self.env['ir.model.data']
        report_id = self.env['mw.account.report'].with_context(data=all_datas).create({'name':'report2',
        #                                                                     'account_id':self.account_id.id,
                                                                    'date_from':self.date_from,
                                                                    'date_to':self.date_to
                                                                    })
        result_context.update({'data':all_datas})
        model, action_id = ir_model_obj.get_object_reference('mw_account', 'action_mw_account_partner_detail_report')
        [action] = self.env[model].browse(action_id).read()
        #         print ('result_context ',result_context)
        action['context'] = result_context
        action['res_id'] = report_id.id
        #         print ('action ',action)
        return action                
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
