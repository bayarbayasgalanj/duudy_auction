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

from dateutil import rrule
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from operator import itemgetter
from lxml import etree
import calendar
from io import BytesIO
import base64
import time

import xlwt
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError
import logging
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
from odoo.tools import float_is_zero, float_compare, pycompat
import collections
_logger = logging.getLogger(__name__)

class account_payable_aged_date_report(models.TransientModel):
    
    _name = "account.payable.aged.date.report"
    _description = "Account Payable Report"
    
#     date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
    date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User',  default=lambda self: self.env.user.id)#readonly=True,
    branch_ids = fields.Many2many('res.branch', string='Branches')
    user_ids = fields.Many2many('res.users', string='Users')
    
    all = fields.Boolean('All?',default=False)

    categ_ids = fields.Many2many('res.partner.category', string='Category')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries'),
                                    ], string='Target Moves', required=True, default='posted')
    period_length = fields.Integer(string='Period Length (days)', required=True, default=30)
    is_odoo = fields.Boolean('Odoo?',default=False)

#     user_get_so = fields.Boolean(u'Жолоочийн тохиргоог SO с авах?')

    def get_partner_ids(self, data):
        res = []
        total = []
        cr = self.env.cr
        company_ids = self.env.context.get('company_ids', (self.env.user.company_id.id,))
        move_state = ['draft', 'posted']
        target_move = data['target_move']
        account_type='payable'
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        return partner_ids
    
#     @api.model
    def create_report_data(self, data):
        data.update({'target_move':'posted'})
        cr=self._cr
        def characteristic_key(r):
            p = 'none'
            if r['partner_id']:
                p = str(r['partner_id'])
#             a = 'none'
#             if r['account_id']:
#                 a = str(r['account_id'])
            f = 'none'
            if r['ref']:
                f = r['ref']
            return (p + ':' + f)
        
        account_obj = self.env['account.account']
        partner_obj = self.pool.get('res.partner')
        
        account_where = ""
        if data.get('account_id',False):
            account_where = " AND l.account_id = %s " % data['account_id'][0]
        partner_where = ""
        if data.get('partner_id', False):
            partner_ids = [data['partner_id'][0]]
            child_ids = self.env['res.partner'].search([('parent_id','=',data['partner_id'][0])])
            if child_ids :
                partner_ids = child_ids
            if data['partner_id'][0] not in partner_ids:
                partner_ids += [data['partner_id'][0]]
            partner_where = " AND l.partner_id in ("+','.join(map(str,partner_ids))+") "
        
        categ_where = ""
        if data.get('account_id',False):
            account_where = " AND l.account_id = %s " % data['account_id'][0]
        

        company_where = ""
        if data.get('company_id', False):
            company_where = " AND l.company_id = %s " % data['company_id'][0]

#Эхний  
        
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
#         move_lines = dict(map(lambda x: (x, []), accounts.ids))
#         print "data context ",data
        init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
                                                        state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        init_wheres = [""]
        
        if init_where_clause.strip():
            init_wheres.append(init_where_clause.strip())
        init_filters = " AND ".join(init_wheres)
        filters = init_filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
#         print 'filters=======: ',filters
#         print 'where ',where
        initw=filters
        move_state = ['draft','posted']
        if data['target_move'] != 'all':
            move_state = ['posted']
        initial_query=''
#         fil=filters,tuple(init_where_params)
#         print 'initial_query ',str(fil)
#         report_types = '\'' + data['type'] + '\''
        report_types="'payable'"
#         if data['type'] == 'all':
#             report_types = "'receivable','payable'"
        # Тайлант хугацааны эхний үлдэгдлийг тооцоолно
# ,l.account_id as account_id, ac.name AS account_name,ac.code AS code,acct.type AS account_type,
        cr.execute(
            "SELECT p.id as partner_id, p.ref as ref, "
                    "p.name as partner_name, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
                    "CASE WHEN l.amount_currency > 0 "
                        "THEN sum(l.amount_currency) "
                        "ELSE 0 "
                    "END AS debit_cur,"
                    "CASE WHEN l.amount_currency < 0 "
                        "THEN sum(l.amount_currency) "
                        "ELSE 0 "
                    "END AS credit_cur,"
                    "(SUM(credit) - sum(debit)) AS ibalance, "
                    "(select category_id from res_partner_res_partner_category_rel where partner_id=p.id limit 1) as category_id "
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
            "JOIN account_account ac ON (l.account_id = ac.id) "
            "JOIN account_move am ON (am.id = l.move_id) "
            "JOIN account_account_type acct ON (acct.id=ac.user_type_id) "
            "WHERE acct.type =" + report_types + " "
            " " + initial_query + " "+ account_where + " "+ partner_where +" "+ company_where+" " + filters + " "
            "GROUP BY p.id, p.ref, p.name,l.currency_id,l.amount_currency "
            "ORDER BY p.name ",tuple(init_where_params))
#         cr.execute(sql, params)
        res = cr.dictfetchall()
#         print 'res ',res
        partner_data = {}
        for r in res:
            if r['ibalance'] != 0 :
                key = characteristic_key(r)
                if key not in partner_data:
                    partner_data[key] = {
                        'partner_id':r['partner_id'],
                        'currency_id':r['currency_id'],
                        'date':'',
                        'partner_ref': r['ref'] or '',
                        'name': r['partner_name'] or u'Харилцагчгүй',
#                         'account_code': r['code'],
#                         'account': '%s %s' % (r['code'],r['account_name']),
#                         'account_name': r['account_name'],
#                         'account_type':r['account_type'],
                        'initial_cur': 0,
                        'initial': 0,
                        'debit_cur': 0,
                        'debit': 0,
                        'credit_cur': 0,
                        'credit': 0,
                        'balance_cur': 0,
                        'balance': 0,
                        'category_id':r['category_id'],
                    }
#                 if r['balance_type'] == 'passive':
                partner_data[key]['initial'] += (r['credit'] or 0) - (r['debit'] or 0)
                partner_data[key]['initial_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
#                 else :
#                     partner_data[key]['initial'] += (r['debit'] or 0) - (r['credit'] or 0)
#                     partner_data[key]['initial_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
        
        for key, value in partner_data.iteritems():
            partner_data[key]['balance_cur'] = partner_data[key]['initial_cur']
            partner_data[key]['balance'] = partner_data[key]['initial']
            
#-------------------------------------------------------------------------------
#         Тайлант хугацааны гүйлгээг тооцоолж эцсийн үлдэгдлийг тодорхойлно
        MoveLine = self.env['account.move.line']
#         init_tables, init_where_clause, init_where_params = MoveLine.with_context(date_from=data['date_from'],
#                                                         state=data['target_move'],date_to=False, strict_range=True, initial_bal=True)._query_get()
        tables, where_clause, where_params = MoveLine.with_context(date_from=data['date_from'],
                                                        state=data['target_move'],date_to=data['date_to'],strict_range=True, )._query_get()
        query=''
        wheres = [""]
#         print 'where_params============================ ',where_params
#         print 'where_clause---------------------------- ',where_clause
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        filters = filters.replace('account_move_line__move_id', 'am').replace('account_move_line', 'l')
        
#         fil=filters,tuple(init_where_params)
#         print 'initial_query ',str(fil)
#         report_types = '\'' + data['type'] + '\''
#         if data['type'] == 'all':
#             report_types = "'receivable','payable'"
        report_types="'payable'"
#,l.account_id as account_id, ac.name AS account_name,ac.code AS code,acct.type AS account_type,
#                     "acct.balance_type "
        cr.execute(
            "SELECT p.id as partner_id, p.ref as ref, "
                    "p.name as partner_name, l.currency_id as currency_id, sum(debit) AS debit, sum(credit) AS credit, "
                    "CASE WHEN l.amount_currency > 0 "
                        "THEN sum(l.amount_currency) "
                        "ELSE 0 "
                    "END AS debit_cur,"
                    "CASE WHEN l.amount_currency < 0 "
                        "THEN sum(l.amount_currency) "
                        "ELSE 0 "
                    "END AS credit_cur, "
                    "(select category_id from res_partner_res_partner_category_rel where partner_id=p.id limit 1) as category_id "
            "FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) "
            "JOIN account_account ac ON (l.account_id = ac.id) "
            "JOIN account_move am ON (am.id = l.move_id) "
            "JOIN account_account_type acct ON (acct.id=ac.user_type_id) "
            "WHERE acct.type IN (" + report_types + ") "
            " " + query + " "+ account_where + " " + partner_where + " "+ company_where+" " + filters +" "
            "GROUP BY p.id, p.ref, p.name, l.currency_id, l.amount_currency "
            "ORDER BY p.name ",tuple(where_params))
        #,l.account_id,ac.name,ac.code,acct.balance_type, acct.type
            #"ORDER BY p.name,l.account_id ")
         
        res = cr.dictfetchall()
#         print 'res ',res
        for r in res:
            if r['debit'] > 0 or r['credit'] > 0 :
                key = characteristic_key(r)
                if key not in partner_data:
                    partner_data[key] = {
                        'partner_id':r['partner_id'],
                        'currency_id':r['currency_id'],
                        'date':'',
                        'partner_ref': r['ref'] or '',
                        'name': r['partner_name'] or u'Харилцагчгүй',
#                         'account': '%s %s' % (r['code'],r['account_name']),
#                         'account_code': r['code'],
#                         'account_name': r['account_name'],
#                         'account_type':r['account_type'],
                        'initial_cur': 0,
                        'initial': 0,
                        'debit_cur': 0,
                        'debit': 0,
                        'credit_cur': 0,
                        'credit': 0,
                        'balance': 0,
                        'balance_cur': 0,
                        'category_id':r['category_id'],
                    }
                partner_data[key]['debit_cur'] += (r['debit_cur'] or 0)
                partner_data[key]['debit'] += (r['debit'] or 0)
                partner_data[key]['credit_cur'] += (abs(r['credit_cur']) or 0)
                partner_data[key]['credit'] += (abs(r['credit']) or 0)
#                 if r['balance_type'] == 'passive':
                partner_data[key]['balance'] += (r['credit'] or 0) - (r['debit'] or 0)
                partner_data[key]['balance_cur'] += (abs(r['credit_cur']) or 0) - (r['debit_cur'] or 0)
#                 else :
#                     partner_data[key]['balance'] += (r['debit'] or 0) - (r['credit'] or 0)
#                     partner_data[key]['balance_cur'] += (r['debit_cur'] or 0) - (abs(r['credit_cur']) or 0)
#         print 'partner_data: ', partner_data
        data.update({'condition':'all'})
        if not data.get('partner_id', False) and data['condition'] != 'all':
            if data['condition'] == 'non-balance':
                for key in partner_data.keys():
                    if abs(partner_data[key]['balance']) >= 1:
                        del partner_data[key]
            else :
                for key in partner_data.keys():
                    if abs(partner_data[key]['balance']) < 1:
                        del partner_data[key]
                        
#         print 'partner_data ,',partner_data
        #return sorted(partner_data.values(), key=itemgetter('name'))
        return sorted(partner_data.values(), key=itemgetter('name'))    
    
    def check_report2(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
       '''
#          datas = data
        company_obj = self.env['res.company']

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        y=int(self.date_to.split('-')[0])
        m=int(self.date_to.split('-')[1])
        d=int(self.date_to.split('-')[2])
        six_months = date(y,m,d) + relativedelta(months=-6)
        sheet = workbook.add_worksheet('payable')
        num_format = '# ##0,00_);(# ##0,00)'#wizard.company_currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 24})
                

        def _header_sheet(sheet):
            sheet.write(0, 3, u'Account payable', report_format)
            sheet.write(2, 0, _(u'Компани:'), bold)
            sheet.write(3, 0, self.company_id.name,)
            sheet.write(4, 0, _('Print on %s') % time.strftime('%Y-%m-%d'))#report.print_time)
        rowx = 5
        _header_sheet(sheet)
        
        accounts=self.env['account.account'].search([('internal_type','=','payable')])
#         partner_ids = self.get_partner_ids({
# #                                     'date_from':date_from,
# #                                     'date_to':date_to,
#                                     'target_move':'posted'
#                                                     })
#         print 'partner_ids ',partner_ids
        date_from = str(self.date_to.split('-')[0])+'-'+str(self.date_to.split('-')[1])+'-01'
        #Дуусах огнооны үеийн үлдэгдэлтэй харилцагчид
        report_datas = self.create_report_data({
                                                    'date_from':date_from,
                                                    'date_to':self.date_to,
                                                    })
        
        
        
        data_dict={}
        for dt in rrule.rrule(rrule.MONTHLY, dtstart=six_months, until=date(y,m,d)):
#             print 'ddd ',dt
            end=calendar.monthrange(int(dt.year),int(dt.month))
#             print 'end ',end
#            print 'i',i
            date_from = str(dt.year)+'-'+str(dt.month)+'-01'
            date_to=str(dt.year)+'-'+str(dt.month)+'-'+str(end[1])
#             report_datas = self.get_payment_list({
            report_datas = self.create_report_data({
                                                    'date_from':date_from,
                                                    'date_to':date_to,
                                                    })
#             report_datas=collections.OrderedDict(sorted(report_datas.items()))
#             report_datas.update({'check_date':dt})
            data_dict[dt]=report_datas
#         
    #             sheet.write(2, 2, _(u'Эхлэх огноо : %s ') % self.date_from if self.date_from else '')
    #             sheet.write(3, 2, _(u'Дуусах огноо : %s ') % self.date_to if self.date_to else '')
#         print 'report_datas ',report_datas
#         print 'data_dict ',data_dict
        head = [
            {'name': _(u'Account'),
             'larg': 10,
             'col': {}},
            {'name': _(u'Name'),
             'larg': 25,
             'col': {}},
        ]        
        for data in data_dict:
#             print 'data ',data
#             print 'data_dict ',data_dict[data]
            head.append({'name': str(data),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}})
        table = []
        for h in head:
                col = {'header': h['name']}
                col.update(h['col'])
                table.append(col)
        colm=2
        rowx = 6
        i=6
        data_2 = {}
        
        for data in data_dict:
            #data ognoo
#             print '5555 ',data_dict[data]
#             print 'data ',data
            for j in data_dict[data]:
#                 print 'jjjj ',j
                if j['category_id'] not in data_2.keys():
                    data_2[j['category_id']] = [{'partner_ref' : j['partner_ref'],
                                                               'name' : j['name'],
                                                               'balance' : j['balance'],
                                                                'partner_id': j['partner_id'],
                                                                'check_date':j['check_date']
                                                               }]   
                else:
                    data_2[j['category_id']].append({'partner_ref' : j['partner_ref'],
                                                               'name' : j['name'],
                                                               'balance' : j['balance'],
                                                                'partner_id': j['partner_id'],
                                                                'check_date':j['check_date']
                                                               }) 
                    

#         print 'data_2 ',data_2               
        for data in data_dict:
#             print 'data222 ' ,data
            for  k in data_2:
                partner_cat = self.env['res.partner.category'].browse(k)
                
                def _set_line(line):
#                     print 'iiiiiiii ',i
#                     print 'line ',line
                    sheet.write(i, 0, line['partner_ref'])
                    sheet.write(i, 1, line['name'])
                    sheet.write(i, colm, line['balance'])
                    
                def _set_table(start_row, rowx):
                    
                    sheet.add_table(start_row - 1, 0, rowx + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })
                    
        #         start_row = rowx
                cash_amount=0
                sheet.write(rowx, 0, partner_cat.name)
                sheet.write(rowx, 1, '')
                sheet.write(rowx, colm, '')
                rowx +=2
                start_row = rowx
                
                for line in data_dict[data]:
#                     print 'data ',data
#                     print 'line--- ',line
                    if line['category_id'] ==k:
    #                 print 'ss ',data_dict[data][line]
                        rowx+=1
                        n=1
        #                 for i,l in enumerate(line):
        #                     print 'l++++ ',l
        #                     print 'iii ',i
                        i = rowx
                        _set_line(line)
                        n+=1
    #                     cash_amount+=l['amount_mnt']
    #                 rowx = i
    #                 rowx+=1
                for j, h in enumerate(head):
                    sheet.set_column(j, j, h['larg'])
            
            #         _set_table(start_row, rowx)
        
                _set_table(start_row, rowx)
                rowx += 3
    #             rowx += 1
    
            colm+=1
                
#             sheet.write(rowx, 2, u'Нийт ')
#             sheet.write(rowx, 3, cash_amount, currency_format)
    #             sheet.write(rowx, 5, line[5], number_xf)
    #             sheet.write(rowx, 6, line[6], number_xf)
    #             sheet.write(rowx, 7, line[7], number_xf)
    #             sheet.write(rowx, 8, line[8], number_xf)
     
            #sheet.set_panes_frozen(True) # frozen headings instead of split panes
            #sheet.set_horz_split_pos(2) # in general, freeze after last heading row
            #sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
            #sheet.set_col_default_width(True)
#             break
        workbook.close()

        out = base64.encodestring(output.getvalue())
        file_name='payable_report.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }


    def _get_partner_move_lines(self, account_type, date_from, target_move, period_length):
        # This method can receive the context key 'include_nullified_amount' {Boolean}
        # Do an invoice and a payment and unreconcile. The amount will be nullified
        # By default, the partner wouldn't appear in this report.
        # The context key allow it to appear
        periods = {}

        start = datetime.strptime(self.date_to, "%Y-%m-%d")
        period_length=self.period_length
        res={}
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
                    
        start = datetime.strptime(date_from, "%Y-%m-%d")
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length)
            periods[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)

        res = []
        total = []
        cr = self.env.cr
        company_ids = self.env.context.get('company_ids', (self.env.user.company_id.id,))
        move_state = ['draft', 'posted']
        if target_move == 'posted':
            move_state = ['posted']
        arg_list = (tuple(move_state), tuple(account_type))
        #build the reconciliation clause to see what partner needs to be printed
        reconciliation_clause = '(l.reconciled IS FALSE)'
        cr.execute('SELECT debit_move_id, credit_move_id FROM account_partial_reconcile where create_date > %s', (date_from,))
        reconciled_after_date = []
        for row in cr.fetchall():
            reconciled_after_date += [row[0], row[1]]
        if reconciled_after_date:
            reconciliation_clause = '(l.reconciled IS FALSE OR l.id IN %s)'
            arg_list += (tuple(reconciled_after_date),)
        arg_list += (date_from, tuple(company_ids))
        query = '''
            SELECT DISTINCT l.partner_id, UPPER(res_partner.name)
            FROM account_move_line AS l left join res_partner on l.partner_id = res_partner.id, account_account, account_move am
            WHERE (l.account_id = account_account.id)
                AND (l.move_id = am.id)
                AND (am.state IN %s)
                AND (account_account.internal_type IN %s)
                AND ''' + reconciliation_clause + '''
                AND (l.date <= %s)
                AND l.company_id IN %s
            ORDER BY UPPER(res_partner.name)'''
        cr.execute(query, arg_list)

        partners = cr.dictfetchall()
        # put a total of 0
        for i in range(7):
            total.append(0)

        # Build a string like (1,2,3) for easy use in SQL query
        partner_ids = [partner['partner_id'] for partner in partners if partner['partner_id']]
        lines = dict((partner['partner_id'] or False, []) for partner in partners)
        if not partner_ids:
            return [], [], []

        # This dictionary will store the not due amount of all partners
        undue_amounts = {}
        query = '''SELECT l.id
                FROM account_move_line AS l, account_account, account_move am
                WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                    AND (am.state IN %s)
                    AND (account_account.internal_type IN %s)
                    AND (COALESCE(l.date_maturity,l.date) > %s)\
                    AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                AND (l.date <= %s)
                AND l.company_id IN %s'''
        cr.execute(query, (tuple(move_state), tuple(account_type), date_from, tuple(partner_ids), date_from, tuple(company_ids)))
        aml_ids = cr.fetchall()
        aml_ids = aml_ids and [x[0] for x in aml_ids] or []
        for line in self.env['account.move.line'].browse(aml_ids):
            partner_id = line.partner_id.id or False
            if partner_id not in undue_amounts:
                undue_amounts[partner_id] = 0.0
            line_amount = line.balance
            if line.balance == 0:
                continue
            for partial_line in line.matched_debit_ids:
                if partial_line.all_max_date <= date_from:
                    line_amount += partial_line.amount
            for partial_line in line.matched_credit_ids:
                if partial_line.all_max_date <= date_from:
                    line_amount -= partial_line.amount
            if not self.env.user.company_id.currency_id.is_zero(line_amount):
                undue_amounts[partner_id] += line_amount
                lines[partner_id].append({
                    'line': line,
                    'amount': line_amount,
                    'period': 6,
                })

        # Use one query per period and store results in history (a list variable)
        # Each history will contain: history[1] = {'<partner_id>': <partner_debit-credit>}
        history = []
        for i in range(5):
            args_list = (tuple(move_state), tuple(account_type), tuple(partner_ids),)
            dates_query = '(COALESCE(l.date_maturity,l.date)'

            if periods[str(i)]['start'] and periods[str(i)]['stop']:
                dates_query += ' BETWEEN %s AND %s)'
                args_list += (periods[str(i)]['start'], periods[str(i)]['stop'])
            elif periods[str(i)]['start']:
                dates_query += ' >= %s)'
                args_list += (periods[str(i)]['start'],)
            else:
                dates_query += ' <= %s)'
                args_list += (periods[str(i)]['stop'],)
            args_list += (date_from, tuple(company_ids))

            query = '''SELECT l.id
                    FROM account_move_line AS l, account_account, account_move am
                    WHERE (l.account_id = account_account.id) AND (l.move_id = am.id)
                        AND (am.state IN %s)
                        AND (account_account.internal_type IN %s)
                        AND ((l.partner_id IN %s) OR (l.partner_id IS NULL))
                        AND ''' + dates_query + '''
                    AND (l.date <= %s)
                    AND l.company_id IN %s'''
            cr.execute(query, args_list)
            partners_amount = {}
            aml_ids = cr.fetchall()
            aml_ids = aml_ids and [x[0] for x in aml_ids] or []
            for line in self.env['account.move.line'].browse(aml_ids):
                partner_id = line.partner_id.id or False
                if partner_id not in partners_amount:
                    partners_amount[partner_id] = 0.0
                line_amount = line.balance
                if line.balance == 0:
                    continue
                for partial_line in line.matched_debit_ids:
                    if partial_line.all_max_date <= date_from:
                        line_amount += partial_line.amount
                for partial_line in line.matched_credit_ids:
                    if partial_line.all_max_date <= date_from:
                        line_amount -= partial_line.amount

                if not self.env.user.company_id.currency_id.is_zero(line_amount):
                    partners_amount[partner_id] += line_amount
                    lines[partner_id].append({
                        'line': line,
                        'amount': line_amount,
                        'period': i + 1,
                        })
            history.append(partners_amount)

        for partner in partners:
            if partner['partner_id'] is None:
                partner['partner_id'] = False
            at_least_one_amount = False
            values = {}
            undue_amt = 0.0
            if partner['partner_id'] in undue_amounts:  # Making sure this partner actually was found by the query
                undue_amt = undue_amounts[partner['partner_id']]

            total[6] = total[6] + undue_amt
            values['direction'] = undue_amt
            if not float_is_zero(values['direction'], precision_rounding=self.env.user.company_id.currency_id.rounding):
                at_least_one_amount = True

            for i in range(5):
                during = False
                if partner['partner_id'] in history[i]:
                    during = [history[i][partner['partner_id']]]
                # Adding counter
                total[(i)] = total[(i)] + (during and during[0] or 0)
                values[str(i)] = during and during[0] or 0.0
                if not float_is_zero(values[str(i)], precision_rounding=self.env.user.company_id.currency_id.rounding):
                    at_least_one_amount = True
            values['total'] = sum([values['direction']] + [values[str(i)] for i in range(5)])
            ## Add for total
            total[(i + 1)] += values['total']
            values['partner_id'] = partner['partner_id']
            if partner['partner_id']:
                browsed_partner = self.env['res.partner'].browse(partner['partner_id'])
                values['name'] = browsed_partner.name and len(browsed_partner.name) >= 45 and browsed_partner.name[0:40] + '...' or browsed_partner.name
                values['trust'] = browsed_partner.trust
            else:
                values['name'] = _('Unknown Partner')
                values['trust'] = False

            if at_least_one_amount or self._context.get('include_nullified_amount'):
                res.append(values)
#         print 'lines123 ',lines
        return res, total, lines


    @api.model
    def get_report_values(self, data=None):
        total = []
#         model = self.env.context.get('active_model')
#         docs = self.env[model].browse(self.env.context.get('active_id'))

        target_move = self.target_move
        date_from = self.date_to
        account_type = ['payable']
#             account_type = ['payable', 'receivable']

        movelines, total, dummy = self._get_partner_move_lines(account_type, date_from, target_move, self.period_length)
        return {
            'doc_ids': self.ids,
#             'doc_model': model,
            'data': self,
#             'docs': docs,
            'time': time,
            'get_partner_lines': movelines,
            'get_direction': total,
        }
        
        
    def check_report(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
       '''
#          datas = data
        company_obj = self.env['res.company']

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        y=int(self.date_to.split('-')[0])
        m=int(self.date_to.split('-')[1])
        d=int(self.date_to.split('-')[2])
        six_months = date(y,m,d) + relativedelta(months=-6)
        sheet = workbook.add_worksheet('payable')
        num_format = '# ##0,00_);(# ##0,00)'#wizard.company_currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 24})
                

        def _header_sheet(sheet):
            sheet.write(0, 3, u'Account payable', report_format)
            sheet.write(2, 0, _(u'Компани:'), bold)
            sheet.write(3, 0, self.company_id.name,)
            sheet.write(4, 0, _('Print on %s') % time.strftime('%Y-%m-%d'))#report.print_time)
        rowx = 5
        _header_sheet(sheet)
        
        accounts=self.env['account.account'].search([('internal_type','=','payable')])
#         partner_ids = self.get_partner_ids({
# #                                     'date_from':date_from,
# #                                     'date_to':date_to,
#                                     'target_move':'posted'
#                                                     })
#         print 'partner_ids ',partner_ids
        date_from = str(self.date_to.split('-')[0])+'-'+str(self.date_to.split('-')[1])+'-01'
        #Дуусах огнооны үеийн үлдэгдэлтэй харилцагчид
#         report_datas = self.create_report_data({
#                                                     'date_from':date_from,
#                                                     'date_to':self.date_to,
#                                                     })
        report_datas = self.get_report_values()
        
        
#         print 'report_datas1234 ',report_datas

        start = datetime.strptime(self.date_to, "%Y-%m-%d")
        period_length=self.period_length
        res={}
        for i in range(5)[::-1]:
            stop = start - relativedelta(days=period_length - 1)
            res[str(i)] = {
                'name': (i!=0 and (str((5-(i+1)) * period_length) + '-' + str((5-i) * period_length)) or ('+'+str(4 * period_length))),
                'stop': start.strftime('%Y-%m-%d'),
                'start': (i!=0 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop - relativedelta(days=1)
        data_dict={}
        head = [
            {'name': _(u'Account'),
             'larg': 10,
             'col': {}},
            {'name': _(u'Name'),
             'larg': 25,
             'col': {}},
            {'name': _(u'Not due'),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}},
            {'name': str(res['4']['stop']),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}},
            {'name': str(res['3']['stop']),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}},
            {'name': str(res['2']['stop']),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}},
            {'name': str(res['1']['stop']),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}},
            {'name': str(res['0']['stop']),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}},
            {'name': _(u'Total'),
             'larg': 17,
            'col':  {'total_function': 'sum', 'format': currency_format}},
                 ]        
            
#         for data in report_datas['get_partner_lines']:
#             print 'data ',data
#             print 'data_dict ',data_dict[data]
#             head.append({'name': str(data),
#              'larg': 17,
#             'col':  {'total_function': 'sum', 'format': currency_format}})
        table = []
        for h in head:
                col = {'header': h['name']}
                col.update(h['col'])
                table.append(col)
        colm=2
        rowx = 6
        i=6
        data_2 = {}
        categ_ids = self.env['res.partner.category'].search([])
#         print 'categ_ids ',categ_ids
        for categ in categ_ids:
            start_row = rowx
            sheet.write(rowx, 0, categ.name)
#             sheet.write(rowx, 1, '')
#             sheet.write(rowx, colm, '')
#             rowx+=1
            for data in report_datas['get_partner_lines']:
#                 print 'data ',data
        
# #         print 'data_2 ',data_2               
#         for data in data_dict:
# #             print 'data222 ' ,data
#             for  k in data_2:
                def _set_line(line):
#                     print 'iiiiiiii ',i
#                     print 'line ',line
                    sheet.write(i, 0, '')
                    sheet.write(i, 0, line['partner_ref'])
                    sheet.write(i, 1, line['name'])
                    sheet.write(i, 2, line['direction'])
                    sheet.write(i, 3, line['4'])
                    sheet.write(i, 4, line['3'])
                    sheet.write(i, 5, line['2'])
                    sheet.write(i, 6, line['1'])
                    sheet.write(i, 7, line['0'])
                    sheet.write(i, 8, line['total'])
                    
                def _set_table(start_row, rowx):
                    
                    sheet.add_table(start_row - 1, 0, rowx + 1, len(head) - 1,
                                    {'total_row': 1,
                                     'columns': table,
                                     'style': 'Table Style Light 9',
                                     })
                    
        #         start_row = rowx
#                 sheet.write(rowx, 0, partner_cat.name)
#                 sheet.write(rowx, 1, '')
#                 sheet.write(rowx, colm, '')
                partner_dat = self.env['res.partner'].browse(data['partner_id'])
                if partner_dat and partner_dat.category_id and partner_dat.category_id.id==categ.id:
                    rowx+=1
                    n=1
                    i = rowx
                    data.update({'partner_ref':partner_dat.ref})
                    _set_line(data)
                
#                 for line in data_dict[data]:
#                     if line['category_id'] ==k:
#                         rowx+=1
#                         n=1
#                         i = rowx
#                         _set_line(line)
#                         n+=1
            #         _set_table(start_row, rowx)
            rowx +=1
            _set_table(start_row, rowx)
            rowx += 3
    #             rowx += 1
    
        for j, h in enumerate(head):
            sheet.set_column(j, j, h['larg'])
            
#             colm+=1
                
        workbook.close()

        out = base64.encodestring(output.getvalue())
        file_name='payable_report.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

