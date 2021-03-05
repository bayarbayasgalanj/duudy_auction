# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.addons import decimal_precision as dp
from datetime import datetime
from io import BytesIO
import base64
import pdfkit
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
from collections import defaultdict
from odoo.exceptions import UserError, ValidationError
import pytz
from odoo.tools.float_utils import float_is_zero

class stock_inventory(models.Model):
    _name = "stock.inventory"
    _inherit = ["stock.inventory", "mail.thread"]

    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'In Progress'),
        ('done', 'Validated')],
        copy=False, index=True, readonly=True,
        default='draft', tracking=True)
    filter_inv = fields.Selection(string='Тоолох сонголт', selection='_selection_filter',)
    import_data_ids = fields.Many2many('ir.attachment', 'stock_inventory_attach_import_data_rel', 'inventory_id', 'attachment_id', 'Импортлох эксел', copy=False)
    price_diff_total = fields.Float(string=u'Нийт Зөрүү',
        readonly=True, compute='_compute_diff_total_in_out', store=True)
    price_diff_total_in = fields.Float(string=u'Нийт Дутаа',
        readonly=True, compute='_compute_diff_total_in_out', store=True)
    price_diff_total_out = fields.Float(string=u'Нийт Илүү',
        readonly=True, compute='_compute_diff_total_in_out', store=True)
    is_barcode_reader = fields.Boolean('Offline Баркод уншигчаар', default=False, copy=False)
    many_categ_ids = fields.Many2many('product.category', string=u'Ангилалууд')
    warning_messages = fields.Html('Warning Message', compute='_compute_wc_messages')
    outdated_mw = fields.Boolean(string="outdated_mw", readonly=True, compute='_compute_outdated_mw')

    @api.depends('line_ids.outdated')
    def _compute_outdated_mw(self):
        for item in self:
            if item.line_ids.filtered(lambda r: r.outdated):
                item.outdated_mw = True
            else:
                item.outdated_mw = False

    def action_view_related_move_lines_mw(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('mw_stock.stock_inventory_line_tree2_mw_real').id, 'tree')],
            'view_mode': 'tree',
            'name': _('Inventory Lines'),
            'res_model': 'stock.inventory.line',
        }
        domain = [
            ('inventory_id', '=', self.id),
            ('location_id.usage', 'in', ['internal', 'transit'])
        ]
        
        # action['context'] = context
        action['domain'] = domain
        return action

    @api.depends('line_ids')
    def _compute_wc_messages(self):
        for item in self:
            message = []
            picking_names = False
            location_ids = item.line_ids.mapped('location_id').ids
            product_ids = item.line_ids.mapped('product_id').ids
            move_ids = self.env['stock.move'].search([('picking_id','!=',False),('state','not in',['done','cancel']),
            ('product_id','in',product_ids)
            ,'|',('location_id','in',location_ids),('location_dest_id','in',location_ids)])
            if move_ids:
                picking_names = ', '.join(move_ids.mapped('picking_id.name'))
            if picking_names:
                message = u'Батлагдаагүй хөдөлгөөнүүд: %s'%(picking_names)
            else:
                message = False
            item.warning_messages = message

    @api.model
    def _selection_filter(self):
        res_filter = [
            ('category_child_of', 'Дэд ангилалд тоолох'),
            ('category_many', 'Олон ангилалаар тоолох'),
            ('manual', 'Барааг гараар сонгох /Хоосон эхлэнэ/'),
            ]
        return res_filter

    def action_reset_product_qty_mw(self):
        self.line_ids.action_reset_product_qty()
        
    @api.onchange('filter_inv','many_categ_ids')
    def onchange_filter_inv(self):
        product_ids = False
        if self.filter_inv=='category_child_of' and self.many_categ_ids:
            product_ids = self.env['product.product'].search([('type','in',['product','consu']),('categ_id','child_of',self.many_categ_ids.ids)]).ids
        elif self.filter_inv=='category_many' and self.many_categ_ids:
            product_ids = self.env['product.product'].search([('type','in',['product','consu']),('categ_id','in',self.many_categ_ids.ids)]).ids
        self.product_ids = product_ids
    
    def _get_inventory_lines_values(self):
        res = super(stock_inventory, self)._get_inventory_lines_values()
        if self.filter_inv=='manual':
            return []
        return res
    @api.depends('line_ids.price_diff_subtotal')
    def _compute_diff_total_in_out(self):
        for item in self:
            item.price_diff_total = sum(item.line_ids.mapped('price_diff_subtotal'))
            item.price_diff_total_in = sum(item.line_ids.filtered(lambda r: r.price_diff_subtotal<0).mapped('price_diff_subtotal'))
            item.price_diff_total_out = sum(item.line_ids.filtered(lambda r: r.price_diff_subtotal>0).mapped('price_diff_subtotal'))
    
    def get_inv_header(self,row, wo_sheet, cell_style):
        wo_sheet.write(row, 0, "Баркод", cell_style)
        wo_sheet.write(row, 1, "Дотоод Код", cell_style)
        wo_sheet.write(row, 2, "Бараа", cell_style)
        wo_sheet.write(row, 3, "Хэжих нэгж", cell_style)
        wo_sheet.write(row, 4, "Байх ёстой", cell_style)
        wo_sheet.write(row, 5, "Тоолсон тоо", cell_style)
        wo_sheet.write(row, 6, "Зөрүү", cell_style)
        wo_sheet.write(row, 7, "Зөрүү Дүнгээр", cell_style)
        wo_sheet.write(row, 8, u"Байрлал", cell_style)
        wo_sheet.write(row, 9, u"Барааны Код", cell_style)
        wo_sheet.write(row, 10, u"Лот/Цуврал дугаар", cell_style)
        return wo_sheet

    def get_inv_print_cel(self, row, wo_sheet, item, contest_left, cell_format2, contest_center):
        wo_sheet.write(row, 0, item.product_id.barcode, contest_left)
        wo_sheet.write(row, 1, item.product_id.default_code, contest_left)
        p_name = item.product_id.name
        if item.product_id.product_template_attribute_value_ids:
            p_name +=u' ('+u', '.join(item.product_id.product_template_attribute_value_ids.mapped('name'))+u')'
        wo_sheet.write(row, 2, p_name, contest_left)
        wo_sheet.write(row, 3, item.product_id.uom_id.name, contest_center)
        wo_sheet.write(row, 4, item.theoretical_qty, cell_format2)
        wo_sheet.write(row, 5, item.product_qty, cell_format2)
        wo_sheet.write_formula(row, 6,'{=('+xl_rowcol_to_cell(row, 5)+'-'+xl_rowcol_to_cell(row, 4)+')}', cell_format2)
        if self.user_has_groups('mw_stock.group_stock_inv_diff_view'):
            wo_sheet.write(row, 7, item.price_diff_subtotal, cell_format2)
        else:
            wo_sheet.write(row, 7, 0, cell_format2)
        wo_sheet.write(row, 8, item.location_id.name, cell_format2)
        
        wo_sheet.write(row, 9, item.product_id.product_code, cell_format2)
        wo_sheet.write(row, 10, item.prod_lot_id.name if item.prod_lot_id else '' , cell_format2)
        return wo_sheet
    
    def get_last_col(self):
        return 10

    def action_print_inventory(self):
        context = self.env.context
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        file_name = u'Inventory'
        worksheet = workbook.add_worksheet('Total')
        worksheet_diff = workbook.add_worksheet('Diffrence')
        # worksheet_not_diff = workbook.add_worksheet(u'Зөрүүгүй')

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(9)
        h1.set_align('center')
        h1.set_font_name('Arial')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#D3D3D3')
        header.set_text_wrap()
        header.set_font_name('Arial')

        header_wrap = workbook.add_format()
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(9)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        header_wrap.set_font_name('Arial')
        header_wrap.set_color('red')
        header_wrap.set_bold(True)

        contest_right_no_bor = workbook.add_format()
        contest_right_no_bor.set_text_wrap()
        contest_right_no_bor.set_font_size(9)
        contest_right_no_bor.set_align('right')
        contest_right_no_bor.set_align('vcenter')
        contest_right_no_bor.set_font_name('Arial')

        contest_left_no_bor = workbook.add_format()
        contest_left_no_bor.set_text_wrap()
        contest_left_no_bor.set_font_size(9)
        contest_left_no_bor.set_align('left')
        contest_left_no_bor.set_align('vcenter')
        contest_left_no_bor.set_font_name('Arial')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)
        contest_left.set_font_name('Arial')

        contest_left_bold = workbook.add_format()
        contest_left_bold.set_bold(True)
        contest_left_bold.set_text_wrap()
        contest_left_bold.set_font_size(9)
        contest_left_bold.set_align('left')
        contest_left_bold.set_align('vcenter')
        contest_left_bold.set_border(style=1)
        contest_left_bold.set_font_name('Arial')
        contest_left_bold.set_bg_color('#B9CFF7')

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_font_name('Arial')

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
        'num_format':'#,##0.00'
        })

        cell_format_no_border = workbook.add_format({
        'border': 0,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,##0.00'
        })

        tz = self.env['res.users'].sudo().browse(self.env.user.id).tz or 'Asia/Ulaanbaatar'
        timezone = pytz.timezone(tz)
        f_date = ''
        if self.date:
            f_date = self.date
            f_date = str(f_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[0:20]
            
        row = 0
        last_col = self.get_last_col()
        worksheet.merge_range(row, 0, row, last_col, _('Material inventory sheet'), contest_center)
        row += 1
        worksheet.write(row, 0,_("Warehouse:"), contest_right)
        worksheet.merge_range(row, 1, row, 2, ', '.join(self.location_ids.mapped('name')), contest_left)
        worksheet.write(row, 5, _("Date:"), contest_right)
        worksheet.merge_range(row, 6, row, last_col, f_date, contest_left)
        row += 1
        worksheet = self.get_inv_header(row, worksheet, header)
        
        row += 1

        row_diff = 0
        worksheet_diff.merge_range(row_diff, 0, row_diff, last_col, _('Material inventory sheet'), contest_center)
        row_diff += 1
        worksheet_diff.write(row_diff, 0, _("Warehouse:"), contest_right)
        worksheet_diff.merge_range(row_diff, 1, row_diff, 2, ', '.join(self.location_ids.mapped('name')), contest_left)
        worksheet_diff.write(row_diff, 5, _("Date:"), contest_right)
        worksheet_diff.merge_range(row_diff, 6, row_diff, last_col, f_date, contest_left)
        row_diff += 1
        worksheet_diff = self.get_inv_header(row_diff, worksheet_diff, header)
        row_diff += 1

        categ_ids = self.line_ids.mapped('product_id.categ_id')
        save_row=row
        save_row_diff=row_diff
        for item_cat in categ_ids:
            lines = self.line_ids.filtered(lambda r: r.product_id.categ_id.id==item_cat.id)
            if lines:
                worksheet.merge_range(row, 0, row, last_col, item_cat.name, contest_left_bold)
                row+=1
            if self.line_ids.filtered(lambda r: r.product_id.categ_id.id==item_cat.id and r.difference_qty!=0):
                worksheet_diff.merge_range(row_diff, 0, row_diff, last_col, item_cat.name, contest_left_bold)
                row_diff+=1
                
            for item in lines:
                worksheet = self.get_inv_print_cel(row, worksheet, item, contest_left, cell_format2, contest_center)
                row+=1
                if item.difference_qty!=0:
                    worksheet_diff = self.get_inv_print_cel(row_diff, worksheet_diff, item, contest_left, cell_format2, contest_center)
                    row_diff+=1
                
        worksheet.merge_range(row, 0, row, 3, 'Нийт', contest_center)
        worksheet.write_formula(row, 4, 
                    '{=SUM('+xl_rowcol_to_cell(save_row+1, 4)+':'+xl_rowcol_to_cell(row-1, 4)+')}', cell_format2)
        worksheet.write_formula(row, 5, 
                    '{=SUM('+xl_rowcol_to_cell(save_row+1, 5)+':'+xl_rowcol_to_cell(row-1, 5)+')}', cell_format2)
        worksheet.write_formula(row, 6, 
                    '{=SUM('+xl_rowcol_to_cell(save_row+1, 6)+':'+xl_rowcol_to_cell(row-1, 6)+')}', cell_format2)
        worksheet.write_formula(row, 7, 
                    '{=SUM('+xl_rowcol_to_cell(save_row+1, 7)+':'+xl_rowcol_to_cell(row-1, 7)+')}', cell_format2)
        worksheet.merge_range(row, 8, row, last_col, '', contest_center)
        worksheet_diff.merge_range(row_diff, 0, row_diff, 2, 'Нийт', contest_center)
        worksheet_diff.write_formula(row_diff, 4, 
                    '{=SUM('+xl_rowcol_to_cell(save_row_diff+1, 4)+':'+xl_rowcol_to_cell(row_diff-1, 4)+')}', cell_format2)
        worksheet_diff.write_formula(row_diff, 5, 
                    '{=SUM('+xl_rowcol_to_cell(save_row_diff+1, 5)+':'+xl_rowcol_to_cell(row_diff-1, 5)+')}', cell_format2)
        worksheet_diff.write_formula(row_diff, 6, 
                    '{=SUM('+xl_rowcol_to_cell(save_row_diff+1, 6)+':'+xl_rowcol_to_cell(row_diff-1, 6)+')}', cell_format2)
        worksheet_diff.write_formula(row_diff, 7, 
                    '{=SUM('+xl_rowcol_to_cell(save_row_diff+1, 7)+':'+xl_rowcol_to_cell(row_diff-1, 7)+')}', cell_format2)
        worksheet_diff.merge_range(row, 8, row, last_col, '', contest_center)
        # Тооллого хийсэн
        # Хүлээн зөвшөөрсөн
        # Тооцоо хийсэн нягтлан хийсэн
        row_diff+=1
        row+=1

        worksheet.write(row, 1,u'Нийт Зөрүү',contest_left_no_bor)
        worksheet.write_formula(row, 2, '{=SUM('+xl_rowcol_to_cell(save_row+1, 9)+':'+xl_rowcol_to_cell(row-2, 9)+')}',cell_format_no_border)
        worksheet.write(row+1, 1,u'Нийт Дутуу',contest_left_no_bor)
        worksheet.write(row+1, 2, self.price_diff_total_in ,cell_format_no_border)
        worksheet.write(row+2, 1,u'Нийт Илүү',contest_left_no_bor)
        worksheet.write(row+2, 2, self.price_diff_total_out ,cell_format_no_border)
    
        worksheet.merge_range(row+3, 0, row+3, 1,u'Тооллогын баг',contest_left_no_bor)
        worksheet.merge_range(row+3, 2, row+3, 5,u'.........................../___________________/',contest_left_no_bor)
        worksheet.merge_range(row+4, 0,row+4, 1,u'Зөвшөөрсөн',contest_left_no_bor)
        worksheet.merge_range(row+4, 2, row+4, 5,u'.........................../___________________/',contest_left_no_bor)
        worksheet.merge_range(row+5, 0,row+5, 1,u'Тооллого Хийсэн Нягтлан',contest_left_no_bor)
        worksheet.merge_range(row+5, 2, row+5, 5,u'.........................../___________________/',contest_left_no_bor)
        
        worksheet_diff.merge_range(row_diff, 0, row_diff, 1,u'Тооллогын баг',contest_left_no_bor)
        worksheet_diff.merge_range(row_diff, 2, row_diff, 5,u'.........................../____________________/',contest_left_no_bor)
        worksheet_diff.merge_range(row_diff+1, 0, row_diff+1, 1,u'Зөвшөөрсөн',contest_left_no_bor)
        worksheet_diff.merge_range(row_diff+1, 2, row_diff+1, 5,u'.........................../___________________/',contest_left_no_bor)
        worksheet_diff.merge_range(row_diff+2, 0,row_diff+2, 1,u'Тооллого Хийсэн Нягтлан',contest_left_no_bor)
        worksheet_diff.merge_range(row_diff+2, 2, row_diff+2, 5,u'.........................../___________________/',contest_left_no_bor)

        # Resize
        worksheet.set_column('A:B', 11)
        worksheet.set_column('C:C', 27)
        worksheet.set_margins(0.2,0.2,0,0)
        worksheet.set_paper(9)
        worksheet.freeze_panes(3, 3)

        worksheet_diff.set_column('A:B', 11)
        worksheet_diff.set_column('C:C', 27)
        worksheet_diff.set_margins(0.2,0.2,0,0)
        worksheet_diff.set_paper(9)
        worksheet_diff.freeze_panes(3, 3)

        workbook.close()

        out = base64.encodestring(output.getvalue())
        file_name = self.name+'.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
    
    def create_inv_line(self, inv_id, product_id, product_qty, loc_id=False, lot_id=False):
        line_obj = self.env['stock.inventory.line']

        line_obj.create({
                'product_id': product_id.id,
                'inventory_id': inv_id.id,
                'product_qty': product_qty,
                'location_id': loc_id.id if loc_id else self.location_id.id,
                'prod_lot_id': lot_id.id if lot_id else False,
                })

    def get_value_text(self, value):
        if isinstance(value, float) or isinstance(value, int):
            if value==0:
                return False
            return str(value)
        value = value.encode("utf-8")
        value = value.decode('utf-8')
        
        return value

    
    def action_import_inventory_update(self, barcode, product_qty, location_name=False, lot_name=False):
        if isinstance(barcode, float):
            barcode = int(barcode)
        else:
            barcode = barcode
        location_obj = self.env['stock.location']
        lot_obj = self.env['stock.production.lot']
        product_id = self.env['product.product'].search(['|',('barcode','=',barcode),('default_code','=',barcode)], limit=1)
        loc_id = False
        lot_id = False
        if location_name:
            loc_id = location_obj.search([('name','=',location_name),('usage','=','internal')], limit=1)
            if not loc_id and product_id:
                raise UserError(u'%s Байрлал олдсонгүй'%(location_name))

        if lot_name:
            lot_id = lot_obj.search([('name','=',lot_name),('product_id','=',product_id.id)], limit=1)
            if not lot_id and product_id:
                raise UserError(u'%s Нэртэй лот/сериал олдсонгүй'%(lot_name))

        line_id = self.line_ids.filtered(lambda r: r.product_id.id==product_id.id)
        if line_id:
            if loc_id:
                line_id = line_id.filtered(lambda r: r.location_id.id==loc_id.id)
            
            if lot_id:
                line_id = line_id.filtered(lambda r: r.prod_lot_id.id==lot_id.id)
            
            if not line_id:
                self.create_inv_line(self,product_id,product_qty,loc_id,lot_id)
            else:
                line_id.product_qty = product_qty
            # if len(line_id)>1:
            #     raise UserError(u'%s Бараа давхардаж байна'%(line_id.mapped('product_id.display_name')))
            # print 'line_id',line_id
            # if not line_id:
            #     raise UserError(u'%s энэ БАЙРЛАЛ дээр бараа алга'%(location_name))
            
        elif product_id:
            self.create_inv_line(self,product_id,product_qty,loc_id,lot_id)
            
    
    def action_import_inventory(self):
        
        if not self.import_data_ids:
            raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodestring(self.import_data_ids[0].datas))
        fileobj.seek(0)
        if self.is_barcode_reader:
            myreader = fileobj.read().splitlines()
            for row in myreader:
                row_data = row.split(',')
                barcode = row_data[0]
                qty = row_data[1]
                self.action_import_inventory_update(barcode, qty)
        else:
            
            if not os.path.isfile(fileobj.name):
                raise osv.except_osv(_('Error'),_('Reading file error.\nChecking for excel file!'))
            book = xlrd.open_workbook(fileobj.name)
            
            try :
                sheet = book.sheet_by_index(0)
            except:
                raise osv.except_osv(_('Error'), _("Sheet's number error"))
            nrows = sheet.nrows
            
            rowi = 2
            data = []
            r=0
            for item in range(0,nrows):
                row = sheet.row(item)
                barcode = row[0].value
                barcode = self.get_value_text(barcode)
                if not barcode:
                    barcode = row[1].value
                elif barcode.lower()=='false':
                    barcode = row[1].value
                
                product_qty = row[5].value
                location_name = row[8].value
                lot_name = row[10].value
                self.action_import_inventory_update(barcode, product_qty, location_name, lot_name)
                       
    def action_update_inventory(self):
        for item in self.line_ids:
            item.action_refresh_quantity()

    def get_inv_header_pdf(self):
        headers = [
            '№',
            'Баркод',
            'Барааны нэр',
            'Хэмжих нэгж',
            'Үлдэгдэл',
            'Тоолсон тоо',
        ]
        if self.get_stock_inv_pdf_lot_ok():
            headers.insert(3, 'Цуврал')
        return headers
    
    def get_stock_inv_pdf_lot_ok(self):
        if self.line_ids.filtered(lambda r: r.product_id.tracking in ['lot','serial']):
            return True
        return False

    def get_inv_data_pdf(self, number, line, qty_total):
        if line:
            datas = [
                    '<p style="text-align: center;">'+str(number)+'</p>',
                    '<p style="text-align: left;">'+(line.product_id.barcode or '')+'</p>',
                    '<p style="text-align: left;">'+(line.product_id.name[:50])+'</p>', 
                    '<p style="text-align: center;">'+(line.product_uom_id.name)+'</p>', 
                    '<p style="text-align: right;">'+"{0}".format(line.theoretical_qty)+"</p>",
                    '<p style="text-align: right;"></p>',
                ]
            if self.get_stock_inv_pdf_lot_ok():
                datas.insert(3, '<p style="text-align: left;">' + (line.prod_lot_id and line.prod_lot_id.name or '') + '</p>')
        else:
            datas = [
                '<p style="text-align: center;"></p>',
                '<p style="text-align: left;">Нийт</p>',
                '<p style="text-align: left;"></p>', 
                '<p style="text-align: center;"></p>', 
                '<p style="text-align: right;">'+"{0}".format(qty_total)+"</p>",
                '<p style="text-align: right;"></p>',
            ]
            if self.get_stock_inv_pdf_lot_ok():
                datas.insert(3, '')
        return datas
    def get_inv_lines_for_print(self, ids):
        inventory = self.browse(ids)
        headers = inventory.get_inv_header_pdf()
        datas = []
        number = 1
        lines = inventory.line_ids.sorted(key=lambda l: (l.product_id, l.theoretical_qty))
        for line in lines:
            datas.append(inventory.get_inv_data_pdf(number, line, 0))
            number += 1
        if datas:
            qty_total = sum(lines.mapped('theoretical_qty'))
            datas.append(inventory.get_inv_data_pdf(number, False, qty_total))
        else:
            return ''
        res = {'header': headers, 'data':datas}
        return res

    def get_location_names(self, ids):
        inventory = self.browse(ids)
        name = ''
        if inventory.location_ids:
            name = ', '.join(inventory.location_ids.mapped('name'))
        else:
            name = ', '.join(inventory.line_ids.mapped('location_id').mapped('name'))
        return name
    
    def get_category_names(self, ids):
        inventory = self.browse(ids)
        name = 'Бүх'
        if inventory.filter_inv == 'category_child_of' or inventory.filter_inv == 'category_many':
            name = ''
            for cat in inventory.many_categ_ids:
                if cat == inventory.many_categ_ids[0]:
                    name = cat.name_get()[0][1]
                else:
                    name += ', %s' % cat.name_get()[0][1]
        return name
    
    def do_print_inventory_sheet(self):
        self.ensure_one()
        template = False
        model_id = self.env['ir.model'].sudo().search([('model','=','stock.inventory')], limit=1)
        template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','inventory_sheet')], limit=1)
        if not template:
            raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))
        
        html = ''
        if template:
            html = template.sudo().get_template_data_html(self.id)

        return template.sudo().print_template_html(html)

class stock_inventory_line(models.Model):
    _inherit = "stock.inventory.line"
    _order = "product_id, inventory_id, location_id, prod_lot_id, categ_id"

    difference_qty = fields.Float('Difference', compute='_compute_difference',
        help="Indicates the gap between the product's theoretical quantity and its newest quantity.",
        readonly=True, digits='Product Unit of Measure', search="_search_difference_qty", store=True)
    diff_price_unit = fields.Float('Нэгж Үнэ/Өртөг', compute='_compute_diff_qty', store=True, readonly=True)
    sum_qty_price_unit = fields.Float('Нийт Нэгж Үнэ/Өртөг', compute='_compute_diff_qty', store=True, readonly=True)
    price_diff_subtotal = fields.Float(string='Нийт Зөрүү Үнэ',
        readonly=True, compute='_compute_diff_qty', store=True)
    product_name = fields.Char(
        'Product Name', related='product_id.name', store=True, readonly=True)
    product_code = fields.Char(
        'Product Code', related='product_id.default_code', store=True, readonly=True)
    location_name = fields.Char(
        'Location Name', related='location_id.complete_name', store=True, readonly=True)
    prod_barcode = fields.Char('Баркод', compute='set_prod_barcode', readonly=True)

    @api.depends('product_id')
    def set_prod_barcode(self):
      for item in self:
        item.prod_barcode = item.product_id.barcode

    @api.depends('theoretical_qty','product_qty','difference_qty')
    def _compute_diff_qty(self):
        for item in self:
            st_price = item.product_id.standard_price
            if item.product_id.cost_method =='fifo' and item.product_qty!=0:
                quantity = item.product_qty
                company = item.company_id
                fifo_vals = item.product_id._run_fifo(abs(quantity), company)
                average_cost = 0
                if fifo_vals.get('unit_cost', False):
                    average_cost = abs(fifo_vals.get('unit_cost', False))
                
                st_price = abs(average_cost)
            item.diff_price_unit = st_price if item.product_id.list_price<=10 else item.product_id.list_price
            item.sum_qty_price_unit = item.diff_price_unit*item.product_qty
            item.price_diff_subtotal = item.diff_price_unit * item.difference_qty


