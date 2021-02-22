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

import logging
from odoo import api, fields, models, _
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import UserError

import time
import datetime
from datetime import timedelta
from lxml import etree

from odoo.tools.translate import _

import xlwt
from xlwt import *
# from odoo.addons.c2c_reporting_tools.c2c_helper import *
from operator import itemgetter
# from odoo.addons.mn_base import report_helper
import xlsxwriter
from io import BytesIO
logger = logging.getLogger('odoo')

class account_general_journal(models.TransientModel):
    """
        Өглөгийн дансны товчоо
    """
    
#     _inherit = "abstract.report.excel"
    _name = "account.general.journal"
    _description = "General journal"
    
    
    company_id = fields.Many2one('res.company', 'Company')
    account_id = fields.Many2one('account.account', 'Account', domain=[('user_type_id.type','in',['payable','receivable'])])
    date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))
    target_move = fields.Selection([('all', 'All Entries'),
                                    ('posted', 'All Posted Entries')], 'Target Moves', required=True,default='posted')
    partner_id = fields.Many2one('res.partner', 'Partner', help="If empty, display all partners")
        

    def print_report(self):

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        file_name = 'general_journal.xlsx'

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

        content_right = workbook.add_format({'num_format': '###,###,###.##'})
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
        

#         print 'lines ',lines
        start_=0
        account_name=''
        account_code=''
        report_name=u'ЕРӨНХИЙ ЖУРНАЛ'

        sheet = workbook.add_worksheet(u'ЕЖ')

        
        row = 8
        
        sheet.merge_range(0, 0, 1, 5, report_name, h1)
#         sheet.write_merge(4,4,8,9, u'Огноо: %s - %s '%(data['form']['date_from'],data['form']['date_to']), styledict['text_xf'])
        sheet.merge_range(2, 0,2,2, u'Байгууллагын нэр: %s'%(self.company_id.name), p12)
        sheet.merge_range(3, 0,3,2, u'', p12)
#         sheet.merge_range(4, 0,4,1, u'Дансны дугаар: ', right_no)
#         sheet.merge_range(4, 2,4,4, u'%s'%account_code, p12)
#         sheet.merge_range(5, 0,5,1, u'Дансны нэр: ', right_no)
#         sheet.merge_range(5, 2,5,3, u'%s'%account_name, p12)
        sheet.merge_range(4, 4,4,5, u'Тайлант үе: %s - %s '%( self.date_from ,self.date_to), content_left_no)
#         sheet.merge_range(5, 4,5,5, u'Эхний үлдэгдэл:', bold_amount_str)
#         

        rowx=5
        sheet.write(rowx+1,0, u'№', theader),
        sheet.write(rowx+1,1, u'Огноо', theader),
        sheet.write(rowx+1,2, u'Дугаар', theader),
        sheet.write(rowx+1,3, u'Гүйлгээний утга', theader),
        sheet.write(rowx+1,4, u'Дебет', theader),
        sheet.write(rowx+1,5, u'Кредит', theader),
#         sheet.write(rowx+1,6, u'Кредит', theader),
#         sheet.write(rowx+1,7, u'Үлдэгдэл', theader),
        
        account_obj = self.pool.get('account.account')
        
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 10)
        sheet.set_column('C:C', 19)
        sheet.set_column('D:D', 30)
        #sheet.set_column('E:E', 25)
        sheet.set_column('E:E', 13)
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
        account_where=""
        if self.account_id:
            account_where+=" and l.account_id={0} ".format(self.account_id.id)
        total_debit=0
        total_credit=0
        self.env.cr.execute("SELECT m.id "
                   "FROM account_move m left join "
                   "     account_move_line l on l.move_id=m.id "
                   "WHERE m.state = 'posted' "+" "+ account_where+ " "
                   "AND m.date >= %s and m.date <= %s and m.company_id = %s group by m.id order by m.date",
            (self.date_from,self.date_to, self.company_id.id))
        mids = self.env.cr.fetchall()
#         print ('mids ',mids)  
        ids=[]
        for id in mids:
            ids.append(id[0])
        lines=self.env['account.move'].get_order_line_xl(ids)
#         print ('lineslineslines ',lines)
        
        number=1
        for k in lines['data']:#sorted(data.iterkeys()):
#             sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
#             sheet.write(rowx, 1, k[1], styledict['text_xf'])
#             sheet.write(rowx, 2, k[2], styledict['text_xf'])
#             sheet.write(rowx, 3, k[3], styledict['text_xf'])
#             sheet.write(rowx, 4, k[4].replace('<p style="text-align: right;">','').replace('</p>',''), styledict['number_xf'])
#             sheet.write(rowx, 5, k[5].replace('<p style="text-align: right;">','').replace('</p>',''), styledict['number_xf'])
            
            sheet.write(rowx-1,0, n, content_left)
            sheet.write(rowx-1,1, k[1], content_date_left)
            sheet.write(rowx-1,2, k[2], content_left)
            sheet.write(rowx-1,3, k[3], content_left)
            sheet.write(rowx-1,4, k[4], content_right)
            sheet.write(rowx-1,5, k[5], content_right)
            total_debit+=k[4]
            total_credit+=k[5]
            rowx += 1
            n+=1
                
        sheet.write(rowx-1,0, '', content_left)
        sheet.write(rowx-1,1, '', content_left)
        sheet.write(rowx-1,2, u'Дүн', content_left)
        sheet.write(rowx-1,3, '', content_left)
        sheet.write(rowx-1,4, total_debit, center)
        sheet.write(rowx-1,5, total_credit, center)
        rowx += 1                
# #            
#         total_amounts = abs(total_amounts)
        
        
        sheet.merge_range(rowx, 1, rowx, 5, u'Орлогын ...... зарлагын ...... ширхэг баримтыг шалгаж хүлээн авсан болно.', p12)
        sheet.merge_range(rowx+1, 2, rowx+1, 5, u'', content_left_no)
        sheet.merge_range(rowx+2, 2, rowx+2, 5, u'Хөтөлсөн нягтлан бодогч:  __________________________', p12)
        sheet.merge_range(rowx+3, 2, rowx+3, 5, u'', content_left_no)
        sheet.merge_range(rowx+4, 2, rowx+4, 5, u'Хянасан: __________________________', p12)
        
#        sheet.set_landscape()
        sheet.set_paper(9)
        sheet.fit_to_pages(1, 100)        


        workbook.close()

        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }


    def print_report_html(self):
        self.ensure_one()
        result_context=dict(self._context or {})
        
#         data['form'].update(self._build_contexts(data))
        account_where=""
        if self.account_id:
            account_where+=" and l.account_id={0} ".format(self.account_id.id)
        total_debit=0
        total_credit=0
        self.env.cr.execute("SELECT m.id "
                   "FROM account_move m left join "
                   "     account_move_line l on l.move_id=m.id "
                   "WHERE m.state = 'posted' "+" "+ account_where+ " "
                   "AND m.date >= %s and m.date <= %s and m.company_id = %s group by m.id order by m.date",
            (self.date_from,self.date_to, self.company_id.id))
        mids = self.env.cr.fetchall()
#         print ('mids ',mids)  
        ids=[]
        for id in mids:
            ids.append(id[0])
        lines=self.env['account.move'].get_order_line_xl(ids)
        
        ir_model_obj = self.env['ir.model.data']
        report_id = self.env['mw.account.report'].with_context(data=lines).create({'name':'report1',
#                                                                     'account_id':self.account_id.id,
                                                                    'date_from':self.date_from,
                                                                    'date_to':self.date_to
                                                                    })
        result_context.update({'data':lines})
        model, action_id = ir_model_obj.get_object_reference('mw_account', 'action_mw_account_general_journal_report')
        [action] = self.env[model].browse(action_id).read()
#         print ('result_context ',result_context)
        action['context'] = result_context
        action['res_id'] = report_id.id
#         print ('action ',action)
        return action



    def print_report_2003(self):
#         data = self.prepare_data(cr, uid, ids, context=context)
#         user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        company = self.company_id
        
#         pretty = c2c_helper.comma_me # Тоог мянгатын нарийвчлалтай болгодог method
        styledict = self.env['abstract.report.excel'].get_easyxf_styles()
        
        ezxf = xlwt.easyxf
        book = xlwt.Workbook(encoding='utf8')
        sheet = book.add_sheet(u'Payable Receivable Ledger')
        sheet_act = book.add_sheet(u'Төлбөр тогтоосон акт')
        sheet.portrait = False
        date_str = '%s-%s' % (
            self.date_from.strftime('%Y.%m.%d'),
            self.date_to.strftime('%Y.%m.%d')
        )
        title = u'Сангийн сайдын 2018 оны 100 дугаар тушаалын хавсралт'
        report_name = u'ЕРӨНХИЙ ЖУРНАЛ '
        
        sheet.write(0, 5, title, xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz right;font: height 180'))
        sheet.write(0, 0, u'Байгууллагын нэр: %s' % company.name, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
        sheet.write(2, 2, report_name, xlwt.easyxf('font:bold on, height 200;align:wrap off,vert centre,horiz left;'))
         

        if self.account_id:
            a = self.account_id
            sheet.write(3, 0, u'Дансны дугаар: %s' % a.code, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz left;font: height 180'))
            sheet.write(3, 6, u'Дансны нэр: %s' % a.name, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
            
        sheet.write(4, 5, u'Тайлант хугацаа: %s' % date_str, xlwt.easyxf('font:bold on;align:wrap off,vert centre,horiz right;font: height 180'))
        rowx = 7
#         if self.account_id:
        self.env.cr.execute("SELECT id "
                   "FROM account_move "
                   "WHERE state = 'posted' "
                   "AND date >= %s and date <= %s and company_id = %s ",
            (self.date_from,self.date_to, self.company_id.id))
        mids = self.env.cr.fetchall()
#         print ('mids ',mids)  
        ids=[]
        for id in mids:
            ids.append(id[0])
        lines=self.env['account.move'].get_order_line(ids)
        print ('lineslineslines ',lines)
        sheet.write_merge(rowx, rowx+2, 0, 0, u'№', styledict['heading_xf'])
        sheet.write_merge(rowx, rowx+2, 1, 1, u'Огноо', styledict['heading_xf'])
        sheet.write_merge(rowx, rowx+2, 2, 2, u'Дугаар', styledict['heading_xf'])
        sheet.write_merge(rowx, rowx+2, 3, 3, u'Гүйлгээний утга', styledict['heading_xf'])
        sheet.write_merge(rowx, rowx+2, 4, 4, u'Дебет', styledict['heading_xf'])
        sheet.write_merge(rowx, rowx+2, 5, 5, u'Кредит', styledict['heading_xf'])
#         sheet.write_merge(rowx, rowx+2, 6, 6, u'Эцсийн үлдэгдэл', styledict['heading_xf'])
            
        rowx += 3
        
#             lines = report_service.get_report_data(cr, uid, data, context=context)
        data = {}
        sums = {}
        debit_sum=credit_sum=0
        cur_data = {}
        a = {}
        number=1
        for k in lines['data']:#sorted(data.iterkeys()):
            sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
            sheet.write(rowx, 1, k[1], styledict['text_xf'])
            sheet.write(rowx, 2, k[2], styledict['text_xf'])
            sheet.write(rowx, 3, k[3], styledict['text_xf'])
            sheet.write(rowx, 4, k[4].replace('<p style="text-align: right;">','').replace('</p>',''), styledict['number_xf'])
            sheet.write(rowx, 5, k[5].replace('<p style="text-align: right;">','').replace('</p>',''), styledict['number_xf'])
#             sheet.write(rowx, 6, line['balance'], styledict['number_xf'])

#             debit_sum+=float(k[4].replace('<p style="text-align: right;">','').replace('</p>',''))
#             credit_sum+=float(k[5].replace('<p style="text-align: right;">','').replace('</p>',''))
            
            number += 1
            rowx += 1
    
        if number < 10:
            while number <= 10:
                sheet.write(rowx, 0, str(number), styledict['text_center_xf'])
                sheet.write(rowx, 1, '', styledict['text_xf'])
                sheet.write(rowx, 2, '', styledict['text_xf'])
                sheet.write(rowx, 3, '', styledict['text_xf'])
                sheet.write(rowx, 4, '', styledict['number_xf'])
                sheet.write(rowx, 5, '', styledict['number_xf'])
#                 sheet.write(rowx, 6, '', styledict['number_xf'])
#                 sheet.write(rowx, 7, '', styledict['number_xf'])
#                 sheet.write(rowx, 8, '', styledict['number_xf'])
                number += 1
                rowx += 1
        
        sheet.write_merge(rowx,rowx, 0,3, u'Нийт дүн', styledict['heading_xf'])
        sheet.write(rowx, 4, debit_sum, styledict['gold_number_bold_xf'])
        sheet.write(rowx, 5, credit_sum, styledict['gold_number_bold_xf'])
        
        rowx += 1
        inch = 1200
        sheet.col(0).width = int(1*inch)
        sheet.col(1).width = int(2*inch)
        sheet.col(2).width = int(3*inch)
        sheet.col(3).width = int(5*inch)
        sheet.col(4).width = int(3*inch)
        sheet.col(5).width = int(3*inch)
        sheet.col(6).width = int(3*inch)

        sheet.write(rowx, 0, u'Хэвлэсэн огноо: %s' % (time.strftime('%Y-%m-%d'),), ezxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 160'))
        
        sheet.write(rowx+4, 2, u"Боловсруулсан: Нягтлан бодогч ......................................... /                                         /",
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
        sheet.write(rowx+6, 2, u"Хянасан: Ерөнхий нягтлан бодогч .............................................../                                         /", 
                    xlwt.easyxf('font:bold off;align:wrap off,vert centre,horiz left;font: height 180'))
        
#         return {'data':book, 'attache_name':report_service.attache_name}
        from io import BytesIO
        buffer = BytesIO()
        book.save(buffer)
        buffer.seek(0)
        
        filename = "general_journal_%s.xls" % (time.strftime('%Y%m%d_%H%M'),)
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
