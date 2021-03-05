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

import base64
import time
import datetime
from datetime import datetime

import xlwt
import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class account_cashflow_report(models.TransientModel):
    """
        Монголын Сангийн Яамнаас баталсан МГ тайлан.
    """
    
    _name = "account.cashflow.report.new"
    _description = "Account Cashflow Report"
    
    date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
    date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)

    from_account = fields.Boolean('Account?')
    
    def check_report(self):
        data=self#.read(cr,uid,ids)[0]
        return self._make_excel(data)
    

    def create_report_data(self, data):
        type_pool = self.env['account.cash.move.type']
        aml_pool = self.env['account.move.line']
        account_obj = self.env['account.account']
        res =[]
        
        date_start = self.date_from
        date_end = self.date_to

#        үндсэн ҮА мг
        total_op_income = 0.0
        total_op_expense =0.0
        total_income = 0.0
        total_expense =0.0
        

        res.append(['1',u'Үндсэн үйл ажиллагааны мөнгөн гүйлгээ',' ',True])
        res.append(['1.1',u'Мөнгөн орлогын дүн',0,True])
        res1 =[]
        type = type_pool.browse(type_pool.search([('group_name','=','activities_income')],order='sequence'))
        n=1
        cr=self.env.cr
        cquery='select id from account_account where internal_type =\'liquidity\' and (is_temporary isnull or is_temporary=\'f\')'
        cr.execute(cquery)
        cash_accounts=cr.fetchall()
        accounts=[]
        project_where=''
 #       if data['project']<>'all':
 #           project_where+=" and name like '%[{0}%'".format(data['project'])
 #       print "project_where ",project_where
        for a in cash_accounts:
            accounts.append(a[0])
        
        #===========================================================================
#         query_sum='SELECT id,name_mn,number,group_name from account_cash_move_type_group  order by sequence'
#         cr.execute(query_sum)
#         res_groups_sum=cr.fetchall()
        res_groups_sum=['investing_income',
                     'activities_income',
                     'financing_income',
                     'activities_expense',
                     'financing_expense',
                     'investing_expense',
                                    ]
        groups_sums={}
        for row_sum in res_groups_sum:
            is_in=' AND amount>0'
                            
            query='select sum(debit)-sum(credit) from account_move_line l left join \
                                                    account_move m on l.move_id=m.id left join \
                                                    account_account a on l.account_id=a.id left join \
                                                    account_account_cmt_rel r on r.account_id=a.id left join \
                                                    account_cash_move_type t on r.cmt_id=t.id \
                            where \
                                t.group_name=\'{0}\' \
                            and m.state=\'posted\' \
                            and m.id in (select move_id from account_move_line where  account_id in \
                            (select id from account_account where user_type_id=3))\
                            AND \
                            l.date >= \'{1}\' \
                            AND \
                            l.date <= \'{2}\' '.format(row_sum,str(date_start),str(date_end),project_where)

#                             and statement_id in (select id from account_bank_statement where state=\'confirm\') \ Заавал батлагдсан банк биш
#             print "query ",query
            cr.execute(query)
            tailant_sum=cr.fetchall()
#             print "tailant ",tailant
            amount_sum=tailant_sum[0]
            if amount_sum[0]:
                groups_sums[row_sum]=abs(amount_sum[0])
            else:
                groups_sums[row_sum]=0
#        print "groups_sums ",groups_sums
        #=============================================================================
        query='SELECT id,name,group_name,number from account_cash_move_type  order by sequence'
        cr.execute(query)
        res_groups=cr.fetchall()
#         groups=res_groups[0]
        totals={}
        res1_check={}
        buh=0
        for row in res_groups:
            is_in=' AND amount>0'
#             query='select sum(debit)-sum(credit) from account_move_line l left join \
#                                                     account_move m on l.move_id=m.id left join \
#                                                     account_account a on l.account_id=a.id left join \
#                                                     account_account_cmt_rel r on r.account_id=a.id left join \
#                                                     account_cash_move_type t on r.cmt_id=t.id \
#                             where \
#                             t.id=\'{0}\' \
#                             and m.state=\'posted\' \
#                             and m.id in (select move_id from account_move_line where  account_id in \
#                             (select id from account_account where user_type_id=3))\
#                             AND \
#                             l.date >= \'{1}\' \
#                             AND \
#                             l.date <= \'{2}\' '.format(row[0],str(date_start),str(date_end),project_where)
            query='select sum(debit)-sum(credit) from account_move_line l left join \
                                                    account_move m on l.move_id=m.id left join \
                                                    account_account a on l.account_id=a.id left join \
                                                    account_account_cmt_rel r on r.account_id=a.id left join \
                                                    account_cash_move_type t on r.cmt_id=t.id \
                            where \
                            t.id=\'{0}\' \
                            and m.state=\'posted\' \
                            and m.id in (select move_id from account_move_line where  account_id in \
                            (select id from account_account where user_type_id=3))\
                            AND \
                            l.date >= \'{1}\' \
                            AND \
                            l.date <= \'{2}\' '.format(row[0],str(date_start),str(date_end),project_where)


#                             and statement_id in (select id from account_bank_statement where state=\'confirm\') \ Заавал батлагдсан банк биш
                            
#             print "query2 ",query
            cr.execute(query)
            tailant=cr.fetchall()
#             print "tailant ",tailant
            amount=tailant[0]
            if not res1_check.has_key('activities_income') and row[2]=='activities_income':
                res1_check['activities_income']=True
                res1.append(['1',u'ҮНДСЭН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
#                 print "groups_sums['activities_income'] ",groups_sums['activities_income']
                res1.append(['1.1',u'Мөнгөн орлогын дүн',groups_sums['activities_income'],True])
            if not res1_check.has_key('activities_expense') and row[2]=='activities_expense':
                res1_check['activities_expense']=True
                res1.append(['1.2',u'Мөнгөн зарлагын дүн',groups_sums['activities_expense'],True])
            if not res1_check.has_key('investing_income') and row[2]=='investing_income':
                res1.append(['1.3',u'Үндсэн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн',groups_sums['activities_income']-groups_sums['activities_expense'],True])
                res1_check['investing_income']=True
                res1.append(['2',u'ХӨРӨНГӨ ОРУУЛАЛТЫН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
                res1.append(['2.1',u'Мөнгөн орлогын дүн',groups_sums['investing_income'],True])
            if not res1_check.has_key('investing_expense') and row[2]=='investing_expense':
                res1_check['investing_expense']=True
                res1.append(['2.2',u'Мөнгөн зарлагын дүн',groups_sums['investing_expense'],True])
            if not res1_check.has_key('financing_income') and row[2]=='financing_income':
                res1.append(['2.3',u'Хөрөнгө оруулалтын үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн',groups_sums['investing_income']-groups_sums['investing_expense'],True])
                res1_check['financing_income']=True
                res1.append(['3',u'САНХҮҮГИЙН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
                res1.append(['3.1',u'Мөнгөн орлогын дүн',groups_sums['financing_income'],True])
            if not res1_check.has_key('financing_expense') and row[2]=='financing_expense':
                res1_check['financing_expense']=True
                res1.append(['2.2',u'Мөнгөн зарлагын дүн',groups_sums['financing_expense'],True])
            if row[3]=='4.0':
                res1.append(['3.3',u'Санхүүгийн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн',groups_sums['financing_income']-groups_sums['financing_expense'],True])
#Ханший зөрүү:::
#                 query='select sum(debit-credit) from account_move_line \
#                                 where date>=\'{0}\' and date<=\'{1}\' \
#                                     and account_id  in \
#                                     (select id from account_account where type =\'liquidity\' or code=\'101000000\') \
#                                     and account_id not in (1373) \
#                                     and journal_id<>6 and move_id not in (select move_id from account_bank_statement_line_move_rel)'.format(str(date_start),str(date_end))
#                 cr.execute(query)
#                 print "query ",query
#                 valut=cr.fetchone()
#                 print "valut ",valut
                a=amount[0]
#Валютын харилцахаас төгрөгийн харилцахад клиринг ээр хийхэд ханшийн зөрүү үүссэн бол ӨХ бодит зөрүү:::
#                 query='select sum(credit-debit) from account_move_line aml \
#                             left join account_move ml on ml.id=aml.move_id \
#                             left join account_bank_statement_line_move_rel br on br.move_id=ml.id \
#                             left join account_bank_statement_line bl on bl.id=br.statement_line_id \
#                             left join account_cash_move_type mt on mt.id=bl.cash_move_type \
#                             left join account_account ac on ac.id=aml.account_id \
#                         where aml.move_id in (select move_id from account_move_line where account_id in (1217,1283)) \
#                         and aml.move_id in (select move_id from account_move_line where account_id in \
#                             (    select id from account_account where type =\'liquidity\' or code=\'101000000\')) \
#                             and aml.date>=\'{0}\' and aml.date<=\'{1}\' and aml.move_id in \
#                             (select move_id from account_bank_statement_line_move_rel) \
#                             and mt.id in (select id from account_cash_move_type where group_name_id isnull) and aml.account_id in (1217,1283)'.format(str(date_start),str(date_end))
# #                 print "query ",query
#                 cr.execute(query)
#                 valut2=cr.fetchone()
# #                 print "valut2 ",valut2
#                 if valut2[0]:
#                     if a:
#                         a+=valut2[0]
#                     else:
#                         a=valut2[0]
#                 if a:
#                     total_op_income+=abs(a)
#                     res1.append([str(row[3]),row[1],a,False])
#                     if totals.has_key(row[3]):
#                        totals[row[3]]+= a
#                     else:
#                        totals[row[3]]=a 
#                 else:
#                     total_op_income+=0
#                     res1.append([str(row[3]),row[1],0,False])
#                 print "a ",a
#                 if a:
#                     a=a
#                 else:
#                     a=0
                
                buh=groups_sums['activities_income']-groups_sums['activities_expense']\
                             +groups_sums['financing_income']-groups_sums['financing_expense']\
                             +groups_sums['investing_income']-groups_sums['investing_expense']#+a
                res1.append(['4.1',u'Бүх цэвэр мөнгөн гүйлгээ',buh,True])
            else:
                if amount[0]:
                    total_op_income+=amount[0]
#                     res1.append([str(row[2]),row[1],abs(amount[0]),False])
#                    orlogo hasah baihgui bol taarahgui bn
                    if 'income' in row[3]:
                        res1.append([str(row[3]),row[1],amount[0],False])
                    else:
                        if amount[0] and amount[0]>0:
                            amount2=-amount[0]
                        else:
                            amount2=abs(amount[0])
                        res1.append([str(row[3]),row[1],amount2,False])
                    if totals.has_key(row[3]):
                       totals[row[3]]+= amount[0]
                    else:
                       totals[row[3]]=amount[0] 
                else:
                    total_op_income+=0
                    res1.append([str(row[3]),row[1],0,False])
#             print "res ",res1

#            print "totalstotals ",totals 

#             if amount[1]>0:
# #                             
#                 query='SELECT l.id,l.name,m.name from account_move_line l left join account_move m on m.id=l.move_id where \
#                             account_id in ('+','.join(map(str,accounts))+') \
#                             and cash_move_type_id in (select id,name from account_cash_move_type where  group_name_id = {0} \
#                             and m.state <> \'draft\' \
#                             AND \
#                             l.date >= \'{1}\' \
#                             AND \
#                             l.date <= \'{2}\' and credit>0 '.format(row[0],str(date_start),str(date_end))
#                             
#                 cr.execute(query)
#                 buruu=cr.fetchall()
#                 raise osv.except_osv(_('warning'),_(u'Үндсэн үйл ажиллагааны Зарлагын гүйлгээн дээр орлогын утга сонгосон байна: %s (%s)')%(buruu,row.name))                
                
            n+=1
#     
        context={}
        context['state'] = 'posted'
        context['date_from'] = date_start
        context['date_to'] = date_end
        context['company_id'] = self.company_id.id
        context['return_initial_bal_journal'] = True
        
        search_args = [('internal_type', '=', 'liquidity'),('is_temporary', '=', False)]
        account_dict = {}
        account_ids = account_obj.search(search_args, order='code')
#         initial_bals = account_obj.get_initial_balance(cr, uid, account_ids, context=context)
        start_amount=0
        end_amount=0
#         for account in account_obj.with_context(context).browse(account_ids) :
        for account_id in account_ids:
#             data['used_context']['company_id']=self.company_id.id
            account_br=account_id.with_context(context) 
#             account_br=account.with_context(context)
            print ('account_br ',account_br.code)
            print ('account_brbalance_start ',account_br.balance_start)
            start_amount += account_br.balance_start
            end_amount += account_br.balance
            
#             start_amount += initial_bals[account.id]['debit'] - initial_bals[account.id]['credit']
#             end_amount+=account.debit-account.credit
#         end_amount=start_amount+end_amount
#         print 'start_amount ',start_amount
#         print 'end_amount ',end_amount
#         ehnii_cr=cr.fetchall()
#         ehnii,etssiin = 1000,2000 #self.mungunii_uldegdel(cr,uid,date_start,date_end,initial_journal_id,accounts,context=context)
        ehnii=start_amount
        etssiin=end_amount

        res5=[]
        res5.append(['5.1',u'Мөнгө, түүнтэй адилтгах хөрөнгийн эхний үлдэгдэл',ehnii,True])
        res5.append(['5.2',u'Мөнгө, түүнтэй адилтгах хөрөнгийн эцсийн үлдэгдэл',etssiin,True])
#         print "res1------- ",res1

#         return res+res2+res3+res4+res5
#         totalstotals  {u'investing_income': 3531356.46, u'investing_expense': -1451739185.56, u'activities_expense': -12976107021.73, 
#         u'financing_expense': -3004103400.6400003, u'activities_income': 12999239466.039999, u'financing_income': 2300000.0}
        res=[]
        res2=[]
        res3=[]
        res4=[]
        res6=[]
        res7=[]
        #20170214
#         print 'res1---------- ',res1
#=============================================
#         if (etssiin-ehnii-buh)<>0:
#             for r in res1:
# #                 print 'rrr ',r[0]
#                     if '1.2.9' in r[0] :
#                         r[2]-=etssiin-ehnii-buh
#                     if '4.1' in r[0]:
#                         r[2]+=etssiin-ehnii-buh
# #                     if '1.2' == r[0] :
# #                         print 'buh ',buh
# #                         print 'etssiin-ehnii ',etssiin-ehnii
# #                         r[2]-=etssiin-ehnii-buh
#                     if '1.3' == r[0] :
# #                         print 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaa ',r[0]
#                         r[2]+=etssiin-ehnii-buh

#=============================================
        #20170214                    
#         for total in totals:
#             print "totaltotal ",total
#             if total=='activities_income':
#                 res.append(['1',u'ҮНДСЭН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
#                 res.append(['1.1',u'Мөнгөн орлогын дүн',totals[total],True])
#             elif total=='activities_expense':
#                 res2.append(['1.2',u'Мөнгөн зарлагын дүн',totals[total],True])
#             elif total=='investing_income':
#                 res3.append(['2',u'ХӨРӨНГӨ ОРУУЛАЛТЫН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
#                 res3.append(['2.1',u'Мөнгөн орлогын дүн',totals[total],True])
#             elif total=='investing_expense':
#                 res4.append(['2.2',u'Мөнгөн зарлагын дүн',totals[total],True])
#             elif total=='financing_income':
#                 res6.append(['3',u'САНХҮҮГИЙН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
#                 res6.append(['3.1',u'Мөнгөн орлогын дүн',totals[total],True])
#             elif total=='financing_expense':
#                 res7.append(['3.2',u'Мөнгөн зарлагын дүн',totals[total],True])
#         print "res ",res
#         print "res6 ",res6
#         return res+res1+res2+res3+res4+res6+res7+res5   
        return res1+res5
    
    def _skip_data(self):
        skip_journals =[]
        skips = self.env['account.cash.skip.conf'].search([])
        for k in  skips:
            for j  in k.skip_journal_ids:
                skip_journals.append(j.id)
        sj = ','.join(map(str, skip_journals))
        return sj
    
    def _compute_amount(self,cash_type):
#             is_in=' AND amount>0'
#             query='select sum(debit)-sum(credit) from account_move_line l left join \
#                                                     account_move m on l.move_id=m.id left join \
#                                                     account_cash_move_type t on l.cash_type_id=t.id \
#                             where \
#                             t.id=\'{0}\' \
#                             and \
#                             l.account_id in \
#                             (select id from account_account where internal_type =\'liquidity\' and (is_temporary isnull or is_temporary=\'f\'))\
#                             AND \
#                             l.date >= \'{1}\' \
#                             AND \
#                             l.date <= \'{2}\' '.format(cash_type,str(date_start),str(date_end),project_where)
            sj=self._skip_data()
            sk_where=''
            if sj:
                  sk_where=' where bl.journal_id not in ({0})'.format(sj)
            
            query=' select case when sum(amount)>0 then sum(debit) else sum(credit) end as aaa,cash_type_id from ( \
                            select bl.id,bl.amount,aml.debit,aml.credit,bl.cash_type_id,aml.id as aml_id,aml.company_id,aml.date \
                            as date from account_bank_statement_line bl left join account_move_line aml on aml.statement_line_id=bl.id \
                              {4} and  aml.move_id not in (select move_id from account_move_line where account_id ={5}) \
                              and aml.move_id  in (select id from account_move where state=\'posted\') \
                            ) as foo where company_id={0} and date between \'{1}\' and \'{2}\' and cash_type_id={3} \
                            group by cash_type_id order by cash_type_id'.format(self.company_id.id,self.date_from,self.date_to,cash_type,sk_where,self.company_id.transfer_account_id.id)#,self.company_id.transfer_account_id.id

#                             and statement_id in (select id from account_bank_statement where state=\'confirm\') \ Заавал батлагдсан банк биш
                            
#             print ("query2 ",query)
            _logger.info(u'query----- %s '%(query))

            cr=self.env.cr
            cr.execute(query)
            tailant=cr.fetchall()     
#             print ('tailant ',tailant)   
            if tailant:
                res=tailant
            else:
                res=[[0]]
            return res
#         'posted'
#         
#         '2020-07-01' and '2020-09-30'
        
    def create_report_data_bank(self, data):
        type_pool = self.env['account.cash.move.type']
        aml_pool = self.env['account.move.line']
        account_obj = self.env['account.account']
        res =[]
        
        date_start = self.date_from
        date_end = self.date_to

#        үндсэн ҮА мг
        total_op_income = 0.0
        total_op_expense =0.0
        total_income = 0.0
        total_expense =0.0
        

        res.append(['1',u'Үндсэн үйл ажиллагааны мөнгөн гүйлгээ',' ',True])
        res.append(['1.1',u'Мөнгөн орлогын дүн',0,True])
        res1 =[]
        type = type_pool.browse(type_pool.search([('group_name','=','activities_income')],order='sequence'))
        n=1
        cr=self.env.cr
        cquery='select id from account_account where internal_type =\'liquidity\' and (is_temporary isnull or is_temporary=\'f\')'
        cr.execute(cquery)
        cash_accounts=cr.fetchall()
        accounts=[]
        project_where=''
        for a in cash_accounts:
            accounts.append(a[0])
        
        #===========================================================================
        res_groups_sum=['investing_income',
                     'activities_income',
                     'financing_income',
                     'activities_expense',
                     'financing_expense',
                     'investing_expense',
                                    ]
        groups_sums={}
        #Нийт дүнгүүд
#                             --        and m.state=\'posted\' \

        for row_sum in res_groups_sum:
#             is_in=' AND amount>0'
#                             
#             query='select sum(debit)-sum(credit) from account_move_line l left join \
#                                                     account_move m on l.move_id=m.id left join \
#                                                     account_cash_move_type t on l.cash_type_id=t.id \
#                             where \
#                                 t.group_name=\'{0}\' \
#                             AND \
#                             l.account_id in \
#                             (select id from account_account where internal_type =\'liquidity\' and (is_temporary isnull or is_temporary=\'f\'))\
#                             AND \
#                             l.date >= \'{1}\' \
#                             AND \
#                             l.date <= \'{2}\' '.format(row_sum,str(date_start),str(date_end),project_where)
                            
            sj=self._skip_data()
            sk_where=''
            if not self.company_id.transfer_account_id:
                raise UserError(u'Змад яваа мөнгөний данс тохируулагдаагүй байнав')
                
            if sj:
                  sk_where=' and bl.journal_id not in ({0})'.format(sj)
            query=' select sum(aaa) from ( \
                    select case when sum(amount)>0 then sum(debit) else sum(credit) end as aaa from ( \
                            select bl.id,bl.amount,aml.debit,aml.credit,bl.cash_type_id,aml.id as aml_id,aml.company_id,aml.date \
                            as date from account_bank_statement_line bl left join account_move_line aml on aml.statement_line_id=bl.id \
                                        left join account_cash_move_type t on bl.cash_type_id=t.id \
                                        where t.group_name=\'{3}\' {4} and aml.move_id not in (select move_id from account_move_line where account_id ={5}) \
                              and aml.move_id  in (select id from account_move where state=\'posted\') \
                            ) as foo where company_id={0} and date between \'{1}\' and \'{2}\') as fff '.format(self.company_id.id,self.date_from,self.date_to,row_sum,sk_where,self.company_id.transfer_account_id.id)#self.company_id.transfer_account_id.id
                            

#                             and statement_id in (select id from account_bank_statement where state=\'confirm\') \ Заавал батлагдсан банк биш
            cr.execute(query)
            tailant_sum=cr.fetchall()
            print ("tailant_sum ",tailant_sum)
            amount_sum=tailant_sum[0]
            if amount_sum[0]:
                groups_sums[row_sum]=abs(amount_sum[0])
            else:
                groups_sums[row_sum]=0
#        print "groups_sums ",groups_sums
        #=============================================================================
        query='SELECT id,name,group_name,number from account_cash_move_type  order by sequence'
        cr.execute(query)
        res_groups=cr.fetchall()
#         groups=res_groups[0]
        totals={}
        res1_check={}
        buh=0
#         --                            and m.state=\'posted\' \
        curr_amount=0
        for row in res_groups:
            tailant = self._compute_amount(row[0])
            print ("tailant ",tailant)
            amount=tailant[0]
#            print 'res1_check ',res1_check
            if not res1_check.get('activities_income',False) and row[2]=='activities_income':
                res1_check['activities_income']=True
                res1.append(['1',u'ҮНДСЭН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
#                 print "groups_sums['activities_income'] ",groups_sums['activities_income']
                res1.append(['1.1',u'Мөнгөн орлогын дүн',groups_sums['activities_income'],True])
            if not res1_check.get('activities_expense',False) and row[2]=='activities_expense':
                res1_check['activities_expense']=True
                res1.append(['1.2',u'Мөнгөн зарлагын дүн',groups_sums['activities_expense'],True])
            if not res1_check.get('investing_income',False) and row[2]=='investing_income':
                res1.append(['1.3',u'Үндсэн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн',groups_sums['activities_income']-groups_sums['activities_expense'],True])
                res1_check['investing_income']=True
                res1.append(['2',u'ХӨРӨНГӨ ОРУУЛАЛТЫН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
                res1.append(['2.1',u'Мөнгөн орлогын дүн',groups_sums['investing_income'],True])
            if not res1_check.get('investing_expense',False) and row[2]=='investing_expense':
                res1_check['investing_expense']=True
                res1.append(['2.2',u'Мөнгөн зарлагын дүн',groups_sums['investing_expense'],True])
            if not res1_check.get('financing_income',False) and row[2]=='financing_income':
                res1.append(['2.3',u'Хөрөнгө оруулалтын үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн',groups_sums['investing_income']-groups_sums['investing_expense'],True])
                res1_check['financing_income']=True
                res1.append(['3',u'САНХҮҮГИЙН ҮЙЛ АЖИЛЛАГААНЫ МӨНГӨН ГҮЙЛГЭЭ',' ',True])
                res1.append(['3.1',u'Мөнгөн орлогын дүн',groups_sums['financing_income'],True])
            if not res1_check.get('financing_expense',False) and row[2]=='financing_expense':
                res1_check['financing_expense']=True
                res1.append(['2.2',u'Мөнгөн зарлагын дүн',groups_sums['financing_expense'],True])
            #Валютын ханш нь касс харилцахад байхгүй тул МГТ сонгох боломжгүй учраас
            _logger.info(u'row[3]----- %s '%(row[3]))
            if row[3]=='3.2.5':
                _logger.info(u'row[3] %s '%(row[3]))
                if self.company_id.currency_exchange_journal_id:
                    journal=self.company_id.currency_exchange_journal_id
                    query='select sum(debit)-sum(credit) from account_move_line \
                                        where account_id in (select id from account_account where internal_type =\'liquidity\' \
                                        and (is_temporary isnull or is_temporary=\'f\')) and \
                                        date between \'{0}\' and \'{1}\' and journal_id={2} and company_id={3} '.format(str(date_start),str(date_end),journal.id,self.company_id.id)
        
        
        #                             and statement_id in (select id from account_bank_statement where state=\'confirm\') \ Заавал батлагдсан банк биш
                                    
        #            print "query2 ",query
                    cr.execute(query)
                    tailant_curr=cr.fetchall()
                    _logger.info(u'tailant_curr %s '%(tailant_curr))
                    amount_curr=tailant_curr[0]                
    #                 amount+=amount_curr
                    if amount[0]:
                        _logger.info(u'amount_curr[0] %s '%(amount_curr[0]))
                        if amount_curr[0]:
                            aa=amount[0]+amount_curr[0]
                            amount=(aa,)
                    elif amount_curr[0]:
                            amount=amount_curr
                    curr_amount=amount[0]
                    print ('curr_amount ',curr_amount)
            if row[3]=='4.0':
                res1.append(['3.3',u'Санхүүгийн үйл ажиллагааны цэвэр мөнгөн гүйлгээний дүн',groups_sums['financing_income']-groups_sums['financing_expense'],True])
#Ханший зөрүү:::
#                 query='select sum(debit-credit) from account_move_line \
#                                 where date>=\'{0}\' and date<=\'{1}\' \
#                                     and account_id  in \
#                                     (select id from account_account where type =\'liquidity\' or code=\'101000000\') \
#                                     and account_id not in (1373) \
#                                     and journal_id<>6 and move_id not in (select move_id from account_bank_statement_line_move_rel)'.format(str(date_start),str(date_end))
#                 cr.execute(query)
#                 print "query ",query
#                 valut=cr.fetchone()
#                 print "valut ",valut
                a=amount[0]
#Валютын харилцахаас төгрөгийн харилцахад клиринг ээр хийхэд ханшийн зөрүү үүссэн бол ӨХ бодит зөрүү:::
#                 query='select sum(credit-debit) from account_move_line aml \
#                             left join account_move ml on ml.id=aml.move_id \
#                             left join account_bank_statement_line_move_rel br on br.move_id=ml.id \
#                             left join account_bank_statement_line bl on bl.id=br.statement_line_id \
#                             left join account_cash_move_type mt on mt.id=bl.cash_move_type \
#                             left join account_account ac on ac.id=aml.account_id \
#                         where aml.move_id in (select move_id from account_move_line where account_id in (1217,1283)) \
#                         and aml.move_id in (select move_id from account_move_line where account_id in \
#                             (    select id from account_account where type =\'liquidity\' or code=\'101000000\')) \
#                             and aml.date>=\'{0}\' and aml.date<=\'{1}\' and aml.move_id in \
#                             (select move_id from account_bank_statement_line_move_rel) \
#                             and mt.id in (select id from account_cash_move_type where group_name_id isnull) and aml.account_id in (1217,1283)'.format(str(date_start),str(date_end))
# #                 print "query ",query
#                 cr.execute(query)
#                 valut2=cr.fetchone()
# #                 print "valut2 ",valut2
#                 if valut2[0]:
#                     if a:
#                         a+=valut2[0]
#                     else:
#                         a=valut2[0]
#                 if a:
#                     total_op_income+=abs(a)
#                     res1.append([str(row[3]),row[1],a,False])
#                     if totals.has_key(row[3]):
#                        totals[row[3]]+= a
#                     else:
#                        totals[row[3]]=a 
#                 else:
#                     total_op_income+=0
#                     res1.append([str(row[3]),row[1],0,False])
#                 print "a ",a
#                 if a:
#                     a=a
#                 else:
#                     a=0
                
                buh=groups_sums['activities_income']-groups_sums['activities_expense']\
                             +groups_sums['financing_income']-groups_sums['financing_expense']\
                             +groups_sums['investing_income']-groups_sums['investing_expense']+curr_amount#+a
                res1.append(['4.1',u'Бүх цэвэр мөнгөн гүйлгээ',buh,True])
            else:
                if amount[0]:
                    total_op_income+=amount[0]
#                     res1.append([str(row[2]),row[1],abs(amount[0]),False])
#                    orlogo hasah baihgui bol taarahgui bn
                    if 'income' in row[3]:
                        res1.append([str(row[3]),row[1],amount[0],False])
                    else:
                        if amount[0] and amount[0]>0:
                            amount2=amount[0]
                        else:
                            amount2=abs(amount[0])
                        res1.append([str(row[3]),row[1],amount2,False])
                    if totals.get(row[3],False):
                       totals[row[3]]+= amount[0]
                    else:
                       totals[row[3]]=amount[0] 
                else:
                    total_op_income+=0
                    res1.append([str(row[3]),row[1],0,False])
#             print "res ",res1

#            print "totalstotals ",totals 

#             if amount[1]>0:
# #                             
#                 query='SELECT l.id,l.name,m.name from account_move_line l left join account_move m on m.id=l.move_id where \
#                             account_id in ('+','.join(map(str,accounts))+') \
#                             and cash_move_type_id in (select id,name from account_cash_move_type where  group_name_id = {0} \
#                             and m.state <> \'draft\' \
#                             AND \
#                             l.date >= \'{1}\' \
#                             AND \
#                             l.date <= \'{2}\' and credit>0 '.format(row[0],str(date_start),str(date_end))
#                             
#                 cr.execute(query)
#                 buruu=cr.fetchall()
#                 raise osv.except_osv(_('warning'),_(u'Үндсэн үйл ажиллагааны Зарлагын гүйлгээн дээр орлогын утга сонгосон байна: %s (%s)')%(buruu,row.name))                
                
            n+=1
#     
        context={}
#         context['state'] = 'posted'
        context['date_from'] = date_start
        context['date_to'] = date_end
        context['company_id'] = self.company_id.id
        context['return_initial_bal_journal'] = True
        context['state'] = 'posted'
        
        context['strict_range'] = True
        context['check_balance_method'] = True
        context['chart_account_ids'] = []
        
        
        search_args = [('internal_type', '=', 'liquidity'),('is_temporary', '=', False)]
        account_dict = {}
        account_ids = account_obj.search(search_args, order='code')
        start_amount=0
        end_amount=0
        for account_id in account_ids:
#             data['used_context']['company_id']=self.company_id.id
            account_br=account_id.with_context(context) 
            start_amount += account_br.balance_start
            end_amount += account_br.balance
#             print ('account_br111111111111 ',account_br.code)
            print ('account_brbalance_start ',str(account_br.balance)+' account_br.code '+str(account_br.code))

        query='select sum(debit)-sum(credit) from account_move_line \
                    where account_id in (select id from account_account where internal_type=\'liquidity\') and \
                    date<=\'{0}\' \
                    '.format(str(date_end))


#                             and statement_id in (select id from account_bank_statement where state=\'confirm\') \ Заавал батлагдсан банк биш
                            
#         cr.execute(query)
#         tailant_end=cr.fetchall()
#         end_amount=tailant_end[0][0]            



#             print 'account_br ',account_br.code+' end_amount ',account_br.balance
            
#             start_amount += initial_bals[account.id]['debit'] - initial_bals[account.id]['credit']
#             end_amount+=account.debit-account.credit
#         end_amount=start_amount+end_amount
#         print 'start_amount ',start_amount
#         print 'end_amount ',end_amount
#         ehnii_cr=cr.fetchall()
#         ehnii,etssiin = 1000,2000 #self.mungunii_uldegdel(cr,uid,date_start,date_end,initial_journal_id,accounts,context=context)
        ehnii=start_amount
        etssiin=end_amount

        res5=[]
        res5.append(['5.1',u'Мөнгө, түүнтэй адилтгах хөрөнгийн эхний үлдэгдэл',ehnii,True])
        res5.append(['5.2',u'Мөнгө, түүнтэй адилтгах хөрөнгийн эцсийн үлдэгдэл',etssiin,True])
#        print "res1------- ",res1

        return res1+res5    
        
    def _make_excel(self, data):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        datas = data
#         fiscalyear_obj = self.env['account.fiscalyear']
        account_obj = self.env['account.account']
#        report_service = atbr.balance_sheet('report.balance.sheet.report')
        if self.from_account:
            report_datas = self.create_report_data(data)
        else:
            report_datas = self.create_report_data_bank(data)
#         print 'report_datas ',report_datas
#         company_obj = self.env['res.company']
#         report_obj = self.env['account.financial.report']
        
        
        ezxf = xlwt.easyxf
        heading_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        text_xf = ezxf('font: bold off; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        text_right_xf = ezxf('font: bold off; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;')
        text_bold_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin;')
        text_bold_right_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin;')
        text_center_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;')
        number_xf = ezxf('font: bold off; align: horz right; borders: top thin, left thin, bottom thin, right thin;', num_format_str='#,##0.00')
        number_bold_xf = ezxf('font: bold on; align: horz right; borders: top thin, left thin, bottom thin, right thin;', num_format_str='#,##0.00')
        number_green_xf = ezxf('font: italic on; align: horz right; borders: top thin, left thin, bottom thin, right thin;pattern: pattern solid, fore_colour gray25;', num_format_str='#,##0.00')
        text_green_xf = ezxf('font: bold on; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin;pattern: pattern solid, fore_colour gray25;')
        
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet('Balance sheet')

        sheet.write(1, 1, u'МӨНГӨН ГҮЙЛГЭЭНИЙ ТАЙЛАН', ezxf('font: bold on; align: wrap off, vert centre, horiz left;font: height 250'))
#         sheet.write_merge(3, 3, 0, 2,  u'Тайлангийн нэр: %s' %(report_obj.browse(data['form']['report_id']).name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
#         sheet.write_merge(4, 4, 0, 2,  u'Байгууллагын нэр: %s' %(company_obj.browse(data['form']['company_id']).name), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))
        sheet.row(1).height = 400
        sheet.write(4, 2, u"%s оны %s сарын %s өдөр" %(time.strftime('%Y'),time.strftime('%m'),time.strftime('%d')), ezxf('font:bold off;align:wrap off,vert centre,horiz left;'))

        rowx = 5
        sheet.write_merge(rowx, rowx+1, 0, 0, u'Мөрийн дугаар', heading_xf)
        sheet.write_merge(rowx, rowx+1, 1, 1, u'Үзүүлэлт', heading_xf)
#         sheet.write_merge(rowx, rowx, 2, 3, u'Үлдэгдэл', heading_xf)
        sheet.write_merge(rowx, rowx+1, 2, 2, u'Тайлант үеийн дүн', heading_xf)
#         sheet.write_merge(rowx+1, rowx+1, 3, 3, data['date_to'], heading_xf)
#        
        rowx += 1
        for line in report_datas:
#             print 'line ',line
            rowx += 1
            text=text_xf
            number=number_xf
            if line[3]:
                text=text_bold_xf
                number=number_bold_xf
#             if not report_datas[line]['is_number']:
#                 balance=''
#                 balance_start=''
            sheet.write(rowx, 0, line[0],text)
            sheet.write(rowx, 1, line[1], text)
            sheet.write(rowx, 2, line[2], number)
#             sheet.write(rowx, 3, line[3], number)

        inch = 3000
        sheet.col(0).width = int(0.7*inch)
        sheet.col(1).width = int(4.5*inch)
        sheet.col(2).width = int(2*inch)
        sheet.col(3).width = int(2*inch)
        sheet.row(7).height = 500
         
        sheet.write(rowx+2, 1, u'Боловсруулсан нягтлан бодогч.........................................../\
                                                 /',ezxf('font: bold off; align: wrap off, vert centre, horiz left;'))
        sheet.write(rowx+4, 1, u'Хянасан ерөнхий нягтлан бодогч....................................../\
                                                 /', ezxf('font: bold off; align: wrap off, vert centre, horiz left;'))
 
        from io import BytesIO
        buffer = BytesIO()
        book.save(buffer)
        buffer.seek(0)
        
        filename = "cashflow_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
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
                


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
