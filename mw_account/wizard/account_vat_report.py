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

_logger = logging.getLogger(__name__)

class account_vat_report(models.TransientModel):
    
    _name = "account.vat.report"
    _description = "Account vat Report"
    
    date_from = fields.Date(required=True, default=lambda self: self._context.get('Start date', fields.Date.context_today(self)))
    date_to = fields.Date(required=True, default=lambda self: self._context.get('End date', fields.Date.context_today(self)))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    branch_ids = fields.Many2many('res.branch', string='Branches')
    account_ids = fields.Many2many('account.account', string='Accounts')
    is_sale = fields.Boolean('Sale')
    journal_ids = fields.Many2many('account.journal', string='Journals')
    is_all = fields.Boolean('All?')
    
    def _print_report(self, data):
        # print "guilgee balancee   23165465464654654654",data
        data['form'].update(self._build_contexts(data))
        return self._make_excel(data)
                    
    @api.model
    def get_vat_list(self,data):
        _logger.info("------ vat -----get_vat_so_list %s  %s", str(data), type(data))
        internal, external = [], []
        totals = [[0,0,0],[0,0,0]]
#         duration = self.duration
        
        initial_bal_where = ''
#         if duration['initial_bal_journal'] :
#             initial_bal_where = "AND m.journal_id <> "+str(duration['initial_bal_journal'])
            
        in_where = ''
        #Харилцагч.
#         if data['tax_partner_ids']:
#             if int(len(data['tax_partner_ids'])) == 1:
#                 in_where += ' AND m.partner_id = '+str(data['tax_partner_ids'][0])
#             else:
#                 in_where += ' AND m.partner_id in '+str(tuple(data['tax_partner_ids']))
        #Данс

        if data['account_ids'] :
            if int(len(data['account_ids'])) == 1:
                in_where += ' AND l.account_id = '+str(data['account_ids'][0])
            else:
                in_where += ' AND l.account_id in '+str(tuple(data['account_ids']))
        if self.journal_ids:
            if int(len(self.journal_ids)) == 1:
                in_where = ' AND l.journal_id = '+str(self.journal_ids.ids[0])
            else:
                in_where = ' AND l.journal_id in '+str(tuple(self.journal_ids.ids))
        #Журнал
#         if data['account_journal']:
#                 in_where += ' AND m.journal_id = '+str(data['account_journal'][0])
        print ('in_where ',in_where)
        self._cr.execute("SELECT m.id FROM account_move AS m \
        LEFT JOIN account_move_line AS l ON m.id = l.move_id \
        WHERE m.state IN ('posted','done') AND m.company_id = "+str(self.company_id.id)+in_where+" \
         " + initial_bal_where  +" AND l.date >= '"+str(data['date_from'])+"' AND l.date <= '"+str(data['date_to'])+"' GROUP BY m.id")
        fech = self._cr.fetchall()
        print ('fech ',fech)
        if fech:
            for move_id in self.env['account.move'].browse(map(lambda x:x[0], fech)):
                total = tax = 0
                is_purchase_vat = False
                partner_name = {'name':'','ref':''}
                is_mongolia=True
                if self.is_all:
                    for line in move_id.line_ids:
                        if self.is_sale:
                            if line.account_id.id in data['account_ids'] and line.credit > 0:
                                tax = line.credit
                                is_purchase_vat = True
    #                             partner_name['name'] = line.partner_id.name
    #                             partner_name['ref'] = line.partner_id.vat
                            if line.account_id.id not in data['account_ids'] and line.debit > 0:
                                partner_name['name'] = (line.partner_id and line.partner_id.name) or (line.move_id.partner_id and line.move_id.partner_id.name)
                                partner_name['ref'] = line.partner_id.vat
                            total += line.credit
                            if line.debit > 0:
        #                         partner_name['name'] = line.partner_id.name
        #                         partner_name['ref'] = line.partner_id.vat
        
        #                         if line.partner_id and line.partner_id.category_id.id in (4,7):
                                if line.partner_id and line.partner_id.country_id and line.partner_id.country_id.id != 147:
                                    is_mongolia =False
                        else:
                            if line.account_id.id in data['account_ids'] and line.debit > 0:
                                tax = line.debit
                                is_purchase_vat = True
    #                             partner_name['name'] = line.partner_id.name
    #                             partner_name['ref'] = line.partner_id.vat
                            if line.account_id.id not in data['account_ids'] and line.credit > 0:
                                partner_name['name'] = (line.partner_id and line.partner_id.name) or (line.move_id.partner_id and line.move_id.partner_id.name)
                                partner_name['ref'] = line.partner_id.vat
    
                            total += line.credit
                            if line.credit > 0:
        #                         partner_name['name'] = line.partner_id.name
        #                         partner_name['ref'] = line.partner_id.vat
        
        #                         if line.partner_id and line.partner_id.category_id.id in (4,7):
                                if line.partner_id and line.partner_id.country_id and line.partner_id.country_id.id != 147:
                                    is_mongolia =False
                            
                        if line.account_id.id in data['account_ids']:
                            if is_purchase_vat:
                                total=tax*1.1*10
                                row = {
                                    'date': move_id.date,
                                    'number': move_id.name or '',
                                    'partner': (partner_name['name']!='' and partner_name['name']) or (line.partner_id and line.partner_id.name) or (line.move_id.partner_id and line.move_id.partner_id.name) or '',
                                    'vat_no': partner_name['ref'] or '',
                                    'total': total,
                                    'cost': total - tax,
                                    'tax': tax
                                }
                                
                                if is_mongolia:                        
                                        internal.append(row)
                                        totals[0][0] += row['total']
                                        totals[0][1] += row['tax']
                                        totals[0][2] += row['cost']
                                else :
                                        external.append(row)
                                        totals[1][0] += row['total']
                                        totals[1][1] += row['tax']
                                        totals[1][2] += row['cost']
                        elif line.journal_id.id in self.journal_ids.ids:#НӨАТ гүй
                            if line.credit>0:
                                total=line.credit
                                tax=0
                                row = {
                                    'date': move_id.date,
                                    'number': move_id.name or '',
                                    'partner': (partner_name['name']!='' and partner_name['name']) or (line.partner_id and line.partner_id.name) or (line.move_id.partner_id and line.move_id.partner_id.name) or '',
                                    'vat_no': partner_name['ref'] or '',
                                    'total': total,
                                    'cost': total - tax,
                                    'tax': tax
                                }
                                
                                if is_mongolia:                        
                                        internal.append(row)
                                        totals[0][0] += row['total']
                                        totals[0][1] += row['tax']
                                        totals[0][2] += row['cost']
                                else :
                                        external.append(row)
                                        totals[1][0] += row['total']
                                        totals[1][1] += row['tax']
                                        totals[1][2] += row['cost']                            
                                        
                else:
                    for line in move_id.line_ids:
                        if self.is_sale:
                            if line.account_id.id in data['account_ids'] and line.credit > 0:
                                tax = line.credit
                                is_purchase_vat = True
    #                             partner_name['name'] = line.partner_id.name
    #                             partner_name['ref'] = line.partner_id.vat
                            if line.account_id.id not in data['account_ids'] and line.debit > 0:
                                partner_name['name'] = line.partner_id.name
                                partner_name['ref'] = line.partner_id.vat
                            total += line.credit
                            if line.debit > 0:
        #                         partner_name['name'] = line.partner_id.name
        #                         partner_name['ref'] = line.partner_id.vat
        
        #                         if line.partner_id and line.partner_id.category_id.id in (4,7):
                                if line.partner_id and line.partner_id.country_id and line.partner_id.country_id.id != 147:
                                    is_mongolia =False
                        else:
                            if line.account_id.id in data['account_ids'] and line.debit > 0:
                                tax = line.debit
                                is_purchase_vat = True
    #                             partner_name['name'] = line.partner_id.name
    #                             partner_name['ref'] = line.partner_id.vat
                            if line.account_id.id not in data['account_ids'] and line.credit > 0:
                                partner_name['name'] = line.partner_id.name
                                partner_name['ref'] = line.partner_id.vat
    
                            total += line.credit
                            if line.credit > 0:
        #                         partner_name['name'] = line.partner_id.name
        #                         partner_name['ref'] = line.partner_id.vat
        
        #                         if line.partner_id and line.partner_id.category_id.id in (4,7):
                                if line.partner_id and line.partner_id.country_id and line.partner_id.country_id.id != 147:
                                    is_mongolia =False
    
                    if is_purchase_vat:
                        row = {
                            'date': move_id.date,
                            'number': move_id.name or '',
                            'partner': partner_name['name'] or '',
                            'vat_no': partner_name['ref'] or '',
                            'total': total,
                            'cost': total - tax,
                            'tax': tax
                        }
                        
                        if is_mongolia:                        
                                internal.append(row)
                                totals[0][0] += row['total']
                                totals[0][1] += row['tax']
                                totals[0][2] += row['cost']
                        else :
                                external.append(row)
                                totals[1][0] += row['total']
                                totals[1][1] += row['tax']
                                totals[1][2] += row['cost']                    
                        
        return internal, external, totals    
        
    def check_report(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        internals, externals, totals  = self.get_vat_list({
                                                'date_from':self.date_from,
                                                'date_to':self.date_to,
                                                'account_ids':self.account_ids.ids})
        company_obj = self.env['res.company']

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet(u'vats')
        
        num_format = '# ##0,00_);(# ##0,00)'#wizard.company_currency_id.excel_format
        bold = workbook.add_format({'bold': True})
        middle = workbook.add_format({'bold': True, 'top': 1})
        left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
        right = workbook.add_format({'right': 1, 'top': 1})
        top = workbook.add_format({'top': 1})
        currency_format = workbook.add_format({'num_format': num_format})
        date_format = workbook.add_format({'num_format': 'YYYY-MM-DD'})
        c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
        report_format = workbook.add_format({'font_size': 24})
        
        def _header_sheet(sheet):
            sheet.write(0, 4, u'НӨАТ ТАЙЛАН', report_format)
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
            {'name': _(u'Огноо'),
             'larg': 10,
             'col': {}},
            {'name': _(u'Дугаар'),
             'larg': 10,
             'col': {}},
            {'name': _(u'Боруулагчийн нэр'),
             'larg': 40,
             'col': {}},
            {'name': _(u'Боруулагчийн ТТД'),
             'larg': 12,
             'col': {}},
            {'name': _(u'Худалдан авсан нийт дүн (НӨТ-тэй)'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
            {'name': _(u'Ногдуулсан НӨТ'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
            {'name': _(u'Цэвэр дүн'),
             'larg': 15,
             'col': {'total_function': 'sum', 'format': currency_format}},
        ]
        table = []
        for h in head:
            col = {'header': h['name']}
            col.update(h['col'])
            table.append(col)
                    
        def _set_line(line):
            serial = line['date']
            date= line['date']
#             print ('serial ',serial)
#             seconds = (serial - 25569) * 86400.0
#             date=datetime.utcfromtimestamp(seconds)
            
            sheet.write(rowx, 0, n)
            sheet.write(rowx, 1, date,date_format)
            sheet.write(rowx, 2, line['number'])
            sheet.write(rowx, 3, line['partner'])
            sheet.write(rowx, 4, line['vat_no'])
            sheet.write(rowx, 5, line['total'], currency_format)
            sheet.write(rowx, 6, line['tax'],currency_format)
            sheet.write(rowx, 7, line['cost'],currency_format)
            
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
        if self.is_sale:
            if externals:
                sheet.write(rowx, 1, '' )
                sheet.write(rowx, 2, '')
                sheet.write(rowx, 3, '')
                sheet.write(rowx, 4, u'A.Импортын борлуулалт авалт')
                sheet.write(rowx, 5, '')
                sheet.write(rowx, 6, '')
                sheet.write(rowx, 7, '')
                sheet.write(rowx, 8, '')
                rowx += 1
                for line in externals:
                    _set_line(line)
                    rowx += 1
                    n+=1
            if internals:
                sheet.write(rowx, 1, '' )
                sheet.write(rowx, 2, '')
                sheet.write(rowx, 3, '')
                sheet.write(rowx, 4, u'Б.Дотоодын борлуулалт авалт')
                sheet.write(rowx, 5, '')
                sheet.write(rowx, 6, '')
                sheet.write(rowx, 7, '')
                sheet.write(rowx, 8, '')
                rowx += 1
                for line in internals:
                    _set_line(line)
                    rowx += 1
                    n+=1      
        else:
            if externals:
                sheet.write(rowx, 1, '' )
                sheet.write(rowx, 2, '')
                sheet.write(rowx, 3, '')
                sheet.write(rowx, 4, u'A.Импортын худалдан авалт')
                sheet.write(rowx, 5, '')
                sheet.write(rowx, 6, '')
                sheet.write(rowx, 7, '')
                sheet.write(rowx, 8, '')
                rowx += 1
                for line in externals:
                    _set_line(line)
                    rowx += 1
                    n+=1
            if internals:
                sheet.write(rowx, 1, '' )
                sheet.write(rowx, 2, '')
                sheet.write(rowx, 3, '')
                sheet.write(rowx, 4, u'Б.Дотоодын худалдан авалт')
                sheet.write(rowx, 5, '')
                sheet.write(rowx, 6, '')
                sheet.write(rowx, 7, '')
                sheet.write(rowx, 8, '')
                rowx += 1
                for line in internals:
                    _set_line(line)
                    rowx += 1
                    n+=1                                 
        for j, h in enumerate(head):
            sheet.set_column(j, j, h['larg'])

        _set_table(start_row, rowx)
        rowx += 2
            
        workbook.close()

        out = base64.encodestring(output.getvalue())
        file_name='vat_report.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

