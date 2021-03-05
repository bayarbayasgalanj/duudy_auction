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
from io import BytesIO
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

from operator import itemgetter
import collections
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
import xlsxwriter

import logging

_logger = logging.getLogger(__name__)

class account_bank_report(models.TransientModel):
    _inherit = "account.common.report"
    _name = "account.bank.report"
    _description = "Account bank report"
 
    date_from = fields.Date('date from',required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_to =  fields.Date('date to',required=True,default=lambda *a: time.strftime('%Y-%m-%d') )
    by_month=fields.Boolean(u'Үлдэгдэл сараар',default=False)
#     target_move = fields.Selection([('done', 'All Posted Entries'),
#                                          ('all', 'All Entries'),
#                                         ], 'Target Moves')
                                        
                                        
    def print_report_window(self):

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        file_name = 'Cash_report.xlsx'

        # CELL styles тодорхойлж байна
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(14)
        h1.set_align('center')
        h1.set_align('vcenter')

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#E6E6E6')

        content_right = workbook.add_format()
        content_right.set_text_wrap()
        content_right.set_font_size(9)
        content_right.set_border(style=1)
        content_right.set_align('right')

        content_left_bold = workbook.add_format({'bold': 1})
        content_left_bold.set_text_wrap()
        content_left_bold.set_font_size(9)
        content_left_bold.set_border(style=1)
        content_left_bold.set_align('left')

        content_left = workbook.add_format()
        content_left.set_text_wrap()
        content_left.set_font_size(9)
        content_left.set_border(style=1)
        content_left.set_align('left')

        content_date_left = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        content_date_left.set_text_wrap()
        content_date_left.set_font_size(9)
        content_date_left.set_border(style=1)
        content_date_left.set_align('left')

        
        content_left_no = workbook.add_format()
#         content_left_no.set_text_wrap()
        content_left_no.set_font_size(9)
#         content_left_no.set_border(style=1)
        content_left_no.set_align('left')

        p12 = workbook.add_format()
#         content_left_no.set_text_wrap()
        p12.set_font_size(10)
#         content_left_no.set_border(style=1)
        p12.set_align('left')

        bold_amount = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
        bold_amount.set_text_wrap()
        bold_amount.set_font_size(10)
        bold_amount.set_align('left')

        bold_amount_str=workbook.add_format()
        bold_amount_str.set_font_size(10)
        bold_amount_str.set_align('right')        

        right_no = workbook.add_format()
        right_no.set_font_size(10)
        right_no.set_align('right')
     
        center = workbook.add_format({'num_format': '###,###,###.##'})
        center.set_text_wrap()
        center.set_font_size(9)
        center.set_align('right')
        center.set_border(style=1)
        
        center_bold = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
        center_bold.set_text_wrap()
        center_bold.set_font_size(9)
        center_bold.set_align('right')
        center_bold.set_border(style=1)

        content_left_noborder = workbook.add_format()
        content_left_noborder.set_text_wrap()
        content_left_noborder.set_font_size(9)
        content_left_noborder.set_align('left')

        content_right_noborder = workbook.add_format()
        content_right_noborder.set_text_wrap()
        content_right_noborder.set_font_size(9)
        content_right_noborder.set_align('right')

        center_noborder = workbook.add_format()
        center_noborder.set_text_wrap()
        center_noborder.set_font_size(9)
        center_noborder.set_align('center')  
        
        payment_request = self.env['account.bank.statement']
        payment_line = self.env['account.bank.statement.line']
#         req_ids = payment_request.search(cr, 1, [('id','in',ids)], order="bank_account_id desc")
        context=self._context
        request_obj = payment_request.browse(context['active_ids'])
        self_br=self       
#         lines=payment_line.search([('statement_id','in',context['active_ids']),('date','>=',self_br.date_from),
#                                                                             ('date','<=',self_br.date_to)],order="date asc, id asc")
        lines=payment_line.search([('journal_id','=',request_obj[0].journal_id.id),('date','>=',self_br.date_from),
                                                                            ('date','<=',self_br.date_to)],order="date asc, id asc")

#         print 'lines ',lines
        start_=0
        account_name=''
        account_code=''
        report_name=''
        start_obj=payment_request.search([('journal_id','=',request_obj[0].journal_id.id),('date','=',self_br.date_from)])
        start=0
        if start_obj:
            start= start_obj.balance_start
        for s in request_obj:
            account_name=s.journal_id.default_debit_account_id.name    
            account_code=s.journal_id.default_debit_account_id.code
            if self.by_month:
                start=s.balance_start
                for l in s.line_ids:
                    if l.date<self_br.date_from:
                        start+=l.amount
                    
            if s.journal_id.type=='bank':
                report_name =u'Харилцахын гүйлгээний тайлан'
            else:
                report_name =u'Бэлэн мөнгөний гүйлгээний тайлан'
        verbose_total = ''
        currency = {}
        verbose_total_dict = {}
        amounts = {}
        amount = 0.0
        curr_amount = 0.0
        total_amounts = 0.0
        confirm = ''
        amount_in=0
        amount_out=0

        sheet = workbook.add_worksheet(u'ЕД')

        
        row = 8
        
        sheet.merge_range(0, 0, 1, 7, report_name, h1)
#         sheet.write_merge(4,4,8,9, u'Огноо: %s - %s '%(data['form']['date_from'],data['form']['date_to']), styledict['text_xf'])
        sheet.merge_range(2, 0,2,2, u'Байгууллагын нэр: %s'%(request_obj[0].company_id.name), p12)
        sheet.merge_range(3, 0,3,2, u'', p12)
        sheet.merge_range(4, 0,4,1, u'Дансны дугаар: ', right_no)
        sheet.merge_range(4, 2,4,4, u'%s'%account_code, p12)
        sheet.merge_range(5, 0,5,1, u'Дансны нэр: ', right_no)
        sheet.merge_range(5, 2,5,3, u'%s'%account_name, p12)
        sheet.merge_range(4, 5,4,6, u'Тайлант үе: %s - %s '%( self_br.date_from ,self_br.date_to), content_left_no)
        sheet.merge_range(5, 4,5,5, u'Эхний үлдэгдэл:', bold_amount_str)
        sheet.merge_range(5, 6,5,7, start, bold_amount)
        

        rowx=5
        #sheet.merge_range(rowx, 0,rowx+1,0, u'Дд', theader),
        #sheet.merge_range(rowx,1,rowx,2, u'Баримтын', theader),
        #sheet.merge_range(rowx,3,rowx+1,4, u'Гүйлгээний утга', theader),
        #sheet.merge_range(rowx,4,rowx+1,4, u'Харилцагч', theader),
        #sheet.merge_range(rowx,5,rowx,6, u'Мөнгөн дүн', theader),
        #sheet.merge_range(rowx,7,rowx+1,7, u'Үлдэгдэл', theader),
#         sheet.merge_range(rowx,6,rowx+1,6, u'Аналитик данс', theader),
        sheet.write(rowx+1,0, u'Д/д', theader),
        sheet.write(rowx+1,1, u'Огноо', theader),
        sheet.write(rowx+1,2, u'Дугаар', theader),
        sheet.write(rowx+1,3, u'Харилцагч', theader),
        sheet.write(rowx+1,4, u'Гүйлгээний утга', theader),
        sheet.write(rowx+1,5, u'Орлого', theader),
        sheet.write(rowx+1,6, u'Зарлага', theader),
        sheet.write(rowx+1,7, u'Үлдэгдэл', theader),
#         sheet.write(rowx,0, n, content_left_bold)
        
#         sheet.merge_range(rowx,10,rowx+1,10, u'Хэрэглэгч', theader),
        account_obj = self.pool.get('account.account')
        
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 19)
        sheet.set_column('D:D', 20)
        #sheet.set_column('E:E', 25)
        sheet.set_column('E:E', 25)
        sheet.set_column('F:F', 13)
        sheet.set_column('G:H', 13)
        rowx+=2
        n=1
        sheet.write(rowx,0, '', content_left)
        sheet.write(rowx,1, '', content_left)
        #sheet.write(rowx,2, u'Эхний үлдэгдэл', content_left)
        sheet.write(rowx,3, '', content_left)
        #sheet.write(rowx,4, '', content_left)
        sheet.write(rowx,4, '', center)
        sheet.write(rowx,5, '', center)
        #sheet.write(rowx,6, start, center)
        rowx += 1

        total_in_a=0
        total_out=0
        
#         for request in request_obj:
#             for line in request.line_ids:
        for line in lines:
                start+=line.amount
                total_amounts+=line.amount
                if line.amount>0:
                    amount_in+=line.amount
                else:
                    amount_out+=abs(line.amount)
                in_a=0
                out=0
                if line.amount>0:
                    in_a=line.amount
                else:
                    out=-line.amount
                sheet.write(rowx-1,0, n, content_left)
                sheet.write(rowx-1,1, line.date, content_date_left)
                sheet.write(rowx-1,2, line.ref, content_left)
                sheet.write(rowx-1,3, line.partner_id and line.partner_id.name or '', content_left)
                sheet.write(rowx-1,4, line.name, content_left)
         #       sheet.write(rowx,4, line.partner_id and line.partner_id.name or '', content_left)
                sheet.write(rowx-1,5, in_a, center)
                sheet.write(rowx-1,6, out, center)
                sheet.write(rowx-1,7, start, center)
                rowx += 1
                n+=1
                total_in_a+=in_a
                total_out+=out
                
        sheet.write(rowx-1,0, '', content_left)
        sheet.write(rowx-1,1, '', content_left)
        sheet.write(rowx-1,2, u'Дүн', content_left)
        sheet.write(rowx-1,3, '', content_left)
        sheet.write(rowx-1,4, '', content_left)
        #sheet.write(rowx,4, '', content_left)
        sheet.write(rowx-1,5, total_in_a, center)
        sheet.write(rowx-1,6, total_out, center)
        sheet.write(rowx-1,7, '', center)
        rowx += 1                
#            
        total_amounts = abs(total_amounts)
        
        
        sheet.merge_range(rowx, 1, rowx, 5, u'Орлогын ...... зарлагын ...... ширхэг баримтыг шалгаж хүлээн авсан болно.', p12)
        sheet.merge_range(rowx+1, 2, rowx+1, 5, u'', content_left_no)
        sheet.merge_range(rowx+2, 2, rowx+2, 5, u'Нягтлан бодогч:  __________________________', p12)
        sheet.merge_range(rowx+3, 2, rowx+3, 5, u'', content_left_no)
        sheet.merge_range(rowx+4, 2, rowx+4, 5, u'Мөнгөний нярав: __________________________', p12)
        
#        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.fit_to_pages(1, 100)        

#         workbook.close()
# 
#         out = base64.encodestring(output.getvalue())
#         excel_id = self.pool.get('report.excel.output').create(cr, uid,{'data': out, 'name': file_name}, context=context)
# 
#         return {
#             'name': 'Export Result',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'report.excel.output',
#             'res_id': excel_id,
#             'view_id': False,
#             'context': context,
#             'type': 'ir.actions.act_window',
#             'target': 'new',
#             'nodestroy': True,
#         }

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
# 
#         from StringIO import StringIO
#         buffer = StringIO()
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
#         form_res = mod_obj.get_object_reference('mn_base', 'action_excel_output_view')
#         form_id = form_res and form_res[1] or False
#         return {
#              'type' : 'ir.actions.act_url',
#              'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
#              'target': 'new',
#         }
        
                         
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
