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
import calendar
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
import collections
_logger = logging.getLogger(__name__)

class account_cash_payment_report(models.TransientModel):
    
    _name = "account.cash.payment.report"
    _description = "Account Payment list Report"
    
    date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
    date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User',  default=lambda self: self.env.user.id)#readonly=True,
    branch_ids = fields.Many2many('res.branch', string='Branches')
    user_ids = fields.Many2many('res.users', string='Users')
    only_bank = fields.Boolean('Only bank?',default=True)

#     user_get_so = fields.Boolean(u'Жолоочийн тохиргоог SO с авах?')

    @api.model
    def get_payment_list(self,data):
        _logger.info("------ payment -----get_payment_list %s  %s", str(data), type(data))
        sale_orders = []
        acc_pay_obj=self.env['account.payment']
        bank_statement_obj=self.env['account.bank.statement.line']
        if self.only_bank:
            bsl=bank_statement_obj.search([('date','>=',data['date_from']),
                                   ('date','<=',data['date_to']),
                                   ('journal_id.type','=','bank'),
                                   ])
        else:
            bsl=bank_statement_obj.search([('date','>=',data['date_from']),
                                   ('date','<=',data['date_to']),
                                   ])
            
        payments={}
        for line in bsl:
#             print 'line ',line
            #desc
            if line.amount<0:
                name=''
                if line.partner_id:
                    if line.partner_id.ref:
                        name=line.partner_id.ref
                    else:
                        name=line.partner_id.name
                else:
                    name=line.name
                #amount
                amount_mnt=0
                amount_cur=0
                rate=0
                amount=0
                vat=0
                if line.journal_entry_ids:
                    for l in line.journal_entry_ids:
                        if l.currency_id and l.currency_id.name=='USD' and l.amount_currency!=0:
                            if l.debit>0:
                                rate=l.debit/l.amount_currency
                            else:
                                rate=l.credit/l.amount_currency
                        if l.statement_id.journal_id.default_debit_account_id and \
                                l.account_id.id==l.statement_id.journal_id.default_debit_account_id.id:
                            amount+=abs(l.debit)+abs(l.credit)
                        if l.tax_line_id:
                            vat=l.debit
                    amount_mnt=amount
                else:
                    amount_mnt=abs(line.amount)                    
    
    #                         else:
    #             print 'rate1 ',rate
                if not rate:
                    rate_id = self.env['res.currency.rate'].search([('currency_id','=',3), ('name','<=',line.date)], order='name desc')
                    if rate_id:
                        rate = rate_id[0].rate                            
    #                 print 'rate2 ',rate
                tmp={'date':line.date,
                     'name':name,
                     'amount_mnt':amount_mnt,
                     'amount_usd':amount_mnt/rate,
                     'rate':rate,
                     'vat':vat and vat or ''}
                if payments.has_key(line.date):
                    payments[line.date].append(tmp)
                else:
                    payments[line.date]=[tmp]
#         print 'payments++++++++++++++++++: ',payments
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
#          datas = data
        company_obj = self.env['res.company']

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        if int(self.date_from.split('-')[1])<int(self.date_to.split('-')[1]):
            m1=int(self.date_from.split('-')[1])
            m2=int(self.date_to.split('-')[1])
        else:
            m1=int(self.date_from.split('-')[1])
            m2=int(self.date_from.split('-')[1])
        for i in range (m1,m2+1): 
#            print 'i',i
           if i>0: 
            if int(self.date_from.split('-')[1])==i:
                date_from=self.date_from
            else:
                date_from=self.date_from.split('-')[0]+'-'+'{0:02d}'.format(i)+'-01'
            if int(self.date_to.split('-')[1])==i:
                date_to=self.date_to
            else:
#                 last_day=calendar.monthrange(int(self.date_to.split('-')[0]),int(self.date_to.split('-')[1]))
                last_day=calendar.monthrange(int(self.date_to.split('-')[0]),i)

                date_to=self.date_from.split('-')[0]+'-'+'{0:02d}'.format(i)+'-'+str(last_day[1])
            sheet = workbook.add_worksheet('{0:02d}'.format(i))
            report_datas = self.get_payment_list({
                                                    'date_from':date_from,
                                                    'date_to':date_to
                                                    })
            report_datas=collections.OrderedDict(sorted(report_datas.items()))
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
                sheet.write(0, 3, u'PAYMENT LIST', report_format)
                sheet.write(2, 0, _(u'Компани:'), bold)
                sheet.write(3, 0, self.company_id.name,)
                sheet.write(4, 0, _('Print on %s') % time.strftime('%Y-%m-%d'))#report.print_time)
    
    #             sheet.write(2, 2, _(u'Эхлэх огноо : %s ') % self.date_from if self.date_from else '')
    #             sheet.write(3, 2, _(u'Дуусах огноо : %s ') % self.date_to if self.date_to else '')
            
            rowx = 5
            _header_sheet(sheet)
            
            head = [
                {'name': _(u'Date'),
                 'larg': 10,
                 'col': {}},
                {'name': _(u'№'),
                 'larg': 6,
                 'col': {}},
                {'name': _(u'Vendor Account'),
                 'larg': 40,
                 'col': {}},
                {'name': _(u'Amount MNT'),
                 'larg': 15,
                 'col':  {'total_function': 'sum', 'format': currency_format}},
                {'name': _(u'Rate'),
                 'larg': 12,
                 'col':  {'total_function': 'sum', 'format': currency_format}},
                {'name': _(u'Amount USD'),
                 'larg': 15,
                 'col':  {'total_function': 'sum', 'format': currency_format}},
                {'name': _(u'VAT'),
                 'larg': 10,
                 'col':  {'total_function': 'sum', 'format': currency_format}},
            ]
            table = []
            for h in head:
                col = {'header': h['name']}
                col.update(h['col'])
                table.append(col)
                        
            def _set_line(l,line):
                sheet.write(i, 0, line)
                sheet.write(i, 1, n)
                sheet.write(i, 2, l['name'])
                sheet.write(i, 3, abs(l['amount_mnt']),currency_format)
                sheet.write(i, 4, abs(l['rate']),currency_format)
                sheet.write(i, 5, abs(l['amount_usd']))
                sheet.write(i, 6, l['vat'])
                
            def _set_table(start_row, rowx):
                
                sheet.add_table(start_row - 1, 0, rowx + 1, len(head) - 1,
                                {'total_row': 1,
                                 'columns': table,
                                 'style': 'Table Style Light 9',
                                 })
                
            rowx = 6
    
    #         start_row = rowx
            cash_amount=0
            for line in report_datas:
    #             print 'line--- ',line
    #             print 'ss ',report_datas[line]
                start_row = rowx
                rowx+=1
                n=1
                for i,l in enumerate(report_datas[line]):
    #                 print 'l++++ ',l
    #                 print 'iii ',i
                    i += rowx
                    _set_line(l,line)
                    n+=1
                    cash_amount+=l['amount_mnt']
                rowx = i
                rowx+=1
                for j, h in enumerate(head):
                    sheet.set_column(j, j, h['larg'])
        
        #         _set_table(start_row, rowx)
    
                _set_table(start_row, rowx)
                rowx += 3
    #             rowx += 1
    
                
                
            sheet.write(rowx, 2, u'Нийт ')
            sheet.write(rowx, 3, cash_amount, currency_format)
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


        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

