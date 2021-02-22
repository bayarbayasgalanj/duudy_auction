# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections
from calendar import monthrange
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd

class account_move_import(models.Model):
    _name = 'account.move.import'
    _inherit = ['mail.thread']
    _description = 'account move import'
    _order = 'date desc,name'

    name = fields.Char('Нэр')
    date = fields.Date('Огноо', required=True)
#     line_ids = fields.One2many('account.move.import.line','parent_id','Мөрүүд')
    state = fields.Selection([('draft','Ноорог'), ('done','Дууссан')], default='draft', string='Төлөв')
    import_data = fields.Binary('Импортлох эксел', copy=False)
    export_data = fields.Binary('Export excel file')
    line_ids = fields.Many2many('account.move','account_move_import_move_res','import_id','move_id','Moves')
    journal_id = fields.Many2one('account.journal','Journal')

    
    def action_done(self):
        self.write({'state':'done'})

    
    def action_draft(self):
        self.write({'state':'draft'})

    
    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'moves')
        
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(9)
        h1.set_align('center')
        h1.set_font_name('Arial')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#9ad808')
        header.set_text_wrap()
        header.set_font_name('Arial')
        
        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(11)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        # header_wrap.set_fg_color('#6495ED')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_font_name('Arial')

        cell_format2 = workbook.add_format({
        'border': 1,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,####0'
        })

        
        row = 0
        last_col = 9
        worksheet.write(row, 0, u"Move", header)
        worksheet.write(row, 1, u"Date", header)
        worksheet.write(row, 2, u"Account", header)
        worksheet.write(row, 3, u"Partner name", header)
        worksheet.write(row, 4, u"Transaction text", header)
        worksheet.write(row, 5, u"debit", header)
        worksheet.write(row, 6, u"Credit", header)
        worksheet.write(row, 7, u"Currency", header)
        worksheet.write(row, 8, u"Currency amount", header)
        worksheet.write(row, 9, u"Analytic account", header)
        worksheet.write(row, 10, u"Equipment", header)
        worksheet.write(row, 11, u"VAT?", header)
        
        # inch = 3000
        # worksheet.col(0).width = int(0.7*inch)
        # worksheet.col(1).width = int(0.7*inch)
        # worksheet.col(2).width = int(0.7*inch)

        workbook.close()

        out = base64.encodestring(output.getvalue())
        excel_id = self.write({'export_data': out})

        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=account.move.import&id=" + str(self.id) + "&filename_field=filename&download=true&field=export_data&filename=" + self.name+'.xlsx',
             'target': 'new',
        }

    
    def action_import(self):
        if not self.import_data:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

#         fileobj = NamedTemporaryFile('w+')
#         fileobj.write(base64.decodestring(self.import_data))
#         fileobj.seek(0)
#         if not os.path.isfile(fileobj.name):
#             raise osv.except_osv(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.decodestring(self.import_data))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        

#         book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        
        rowi = 1
        move_obj = self.env['account.move']
        analytic_obj = self.env['account.analytic.account']
        account_obj = self.env['account.account']
#         technic_obj = self.env['technic.equipment']
        partner_obj = self.env['res.partner']
        moves={}
        line_vals=[]
        debit_sum=credit_sum=0
        for item in range(rowi,nrows):
            row = sheet.row(item)
            move_id = row[0].value
            excel_date = row[1].value
            account_code = row[2].value
            partner_name = row[3].value
            name = row[4].value
            debit = row[5].value
            credit = row[6].value
            currency = row[7].value
            currency_amount = row[8].value
            analytic_code = row[9].value
            technic_code = row[10].value
            is_vat = row[11].value
            is_vat = str(is_vat).split('.')[0]
                
#             print 'account_code ',account_code
            account_code = str(account_code).split('.')[0]
            analytic_code = str(analytic_code).split('.')[0]
#             print 'technic_code1 ',technic_code
            technic_code = str(technic_code).split('.')[0]
#             print 'technic_code ',technic_code
#             tech_id = technic_obj.search([('program_code','=',technic_code)], limit=1)
            analytic_id = analytic_obj.search([('code','=',analytic_code)], limit=1)
            account_id = account_obj.search([('code','=',account_code)], limit=1)
#             date = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)
            if not self.date:
                raise UserError(_(u'Огноо оруулана уу.'))
            date=self.date
            partner_id=partner_obj.search([('name','=',partner_name)])
#             print 'partner_id ',partner_id
            if account_id:
                account_id=account_id.id
            if analytic_id:
                analytic_id=analytic_id.id
#             if tech_id:
#                 tech_id=tech_id.id
            if len(partner_id)==1:
                partner_id=partner_id.id
            elif len(partner_id)>1:
                raise UserError(_(u'Дараах харилцагч олон үүссэн байна {0}.'.format(partner_id[0].name)))
            if moves.get(move_id):
                moves[move_id]={''}
#             print 'move_id ',move_id
#             if tech_id:
#             print 'analytic_id2 ',analytic_id
            if is_vat and int(is_vat)==1:
                vat=0
                is_debit=True
                if debit:
                    vat=round(debit/1.1,2)
                    debit=debit-vat
                elif credit:
                    vat=round(credit/1.1,2)
                    credit=credit-vat
                    is_debit=False
                    
                line_vals.append([0,0,{
                    'name': name,
                    'ref': self.name,
                    'account_id': account_id,
                    'debit':debit and debit or 0,
                    'credit':  credit and credit or 0,
                    'journal_id': self.journal_id.id,
    #                 'currency_id': asset.currency_id.id,
#                     'technic_id':tech_id,
                    'date': date,
                    'partner_id': partner_id,
                    'analytic_account_id': analytic_id
                }])
                tax_account_id=self.env['account.tax'].search([('account_id','!=','')], limit=1).account_id
                line_vals.append([0,0,{
                    'name': name+u' НӨАТ',
                    'ref': self.name+u' НӨАТ',
                    'account_id': tax_account_id.id,
                    'debit':is_debit and vat or 0,
                    'credit':  not is_debit and vat or 0,
                    'journal_id': self.journal_id.id,
    #                 'currency_id': asset.currency_id.id,
#                     'technic_id':tech_id,
                    'date': date,
                    'partner_id': partner_id,
                    'analytic_account_id': analytic_id
                }])                                
            else:
                line_vals.append([0,0,{
                    'name': name,
                    'ref': self.name,
                    'account_id': account_id,
                    'debit':debit and debit or 0,
                    'credit':  credit and credit or 0,
                    'journal_id': self.journal_id.id,
    #                 'currency_id': asset.currency_id.id,
#                     'technic_id':tech_id,
                    'date': date,
                    'partner_id': partner_id,
                    'analytic_account_id': analytic_id
                }])
            credit_sum+=credit and credit or 0
            debit_sum+=debit and debit or 0
            
        new_name = '/'
        journal = self.journal_id
        if journal.sequence_id:
                # If invoice is actually refund and journal has a refund_sequence then use that one or use the regular one
                sequence = journal.sequence_id
                new_name = sequence.with_context(ir_sequence_date=self.date).next_by_id()
        else:
            raise UserError(_('Please define a sequence on the journal.'))

        move_vals = {
            'name': new_name,#self.name+'/'+str(datetime.strptime(self.date, '%Y-%m-%d').year),
            'date': self.date,
            'ref': self.name,
            'journal_id': self.journal_id.id,
            'line_ids': line_vals
        }
        move_id = move_obj.create(move_vals)
        self.env.cr.execute("insert into account_move_import_move_res(import_id,move_id) values({0},{1})".format(self.id,move_id.id))  
#             if asset.category_id.journal_id.auto_approve:
#         move_id.post()
        return move_id            
         
    
