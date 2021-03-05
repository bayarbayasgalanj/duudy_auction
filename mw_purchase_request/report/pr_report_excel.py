# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import tools
from odoo import api, fields, models
from xlsxwriter.utility import xl_rowcol_to_cell
import pytz

class PrReportExcel(models.TransientModel):
    _name = 'pr.report.excel'
    _description = 'Pr report Excel'

    date_start = fields.Date(required=True, string=u'Эхлэх огноо')
    date_end = fields.Date(required=True, string=u'Дуусах огноо')
    date_range_id = fields.Many2one('date.range',string='Огнооны хязгаар')
    attachment_ids = fields.Many2many('ir.attachment', 'pr_report_excel_ir_attachment_rel', 'report_id', 'attach_id','Export excel files')
    date_type = fields.Selection([('pr','Хүсэлтийн огноо'),('po','Худалдан авалтын огноо'),('stock','Агуулахын огноо')], string='Огнооны төрөл', default='pr')

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_start = self.date_range_id.date_start
        self.date_end = self.date_range_id.date_end


    def get_tech_name(self, pr_line_id):
        return ''
    # Excel ээр харах
    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'delivery report')

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

        header_center = workbook.add_format()
        header_center.set_text_wrap()
        header_center.set_font_size(9)
        header_center.set_align('center')
        header_center.set_align('vcenter')
        header_center.set_border(style=1)
        header_center.set_font_name('Arial')
        header_center.set_bg_color('yellow')

        cell_format2 = workbook.add_format({
        'border': 1,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,####0'
        })


        row = 0
        last_col = 15
        worksheet.write(row, 10, u"Delivery reports", header_wrap)

        row += 1

        worksheet.write(row, 0, u"PR number", header_center)
        worksheet.write(row, 1, u"PR date", header_center)
        worksheet.write(row, 2, u"Item description", header_center)
        worksheet.write(row, 3, u"Source document", header_center)
        worksheet.write(row, 4, u"PO number", header_center)
        worksheet.write(row, 5, u"PO date", header_center)
        worksheet.write(row, 6, u"Deliver to [warehouse]", header_center)

        worksheet.write(row, 7, u"PR part number", header_center)
        worksheet.write(row, 8, u"PR item description", header_center)
        worksheet.write(row, 9, u"PO part number", header_center)
        worksheet.write(row, 10, u"PO item description", header_center)
        worksheet.write(row, 11, u"Received part number", header_center)
        worksheet.write(row, 12, u"Received item description", header_center)
        worksheet.write(row, 13, u"UOM", header_center)

        worksheet.write(row, 14, u"PR quantity", header_center)
        worksheet.write(row, 15, u"PO quantity", header_center)
        worksheet.write(row, 16, u"Received quantity", header_center)
        worksheet.write(row, 17, u"Outstanding delivery", header_center)
        worksheet.write(row, 18, u"PO status", header_center)
        worksheet.write(row, 19, u"Equipment", header_center)

        worksheet.write(row, 20, u"Scheduled date", header_center)
        worksheet.write(row, 21, u"PO approved date", header_center)
        worksheet.write(row, 22, u"Delivery day", header_center)
        worksheet.write(row, 23, u"Received date", header_center)
        worksheet.write(row, 24, u"Delay", header_center)

        worksheet.write(row, 25, u"Unit price", header_center)
        worksheet.write(row, 26, u"Vat", header_center)
        worksheet.write(row, 27, u"PO amount", header_center)
        worksheet.write(row, 28, u"Received amount", header_center)
        worksheet.write(row, 29, u"Outstanding amount", header_center)

        worksheet.write(row, 30, u"Vendor", header_center)



        pr_report = self.env['pr.report']
        where = ''
        order_by = ''

        if self.date_type=='pr':
            where = "pr.date>='%s' and pr.date<='%s'"%(self.date_start,self.date_end)
            order_by = " order by 4, 3 "
        elif self.date_type=='po':
            where = "pr.po_date_in>='%s' and pr.po_date_in<='%s'"%(self.date_start,self.date_end)
            order_by = " order by 6 "
        elif self.date_type=='stock':
            where = "pr.stock_date>='%s' and pr.stock_date<='%s'"%(self.date_start,self.date_end)
            order_by = " order by 5 "

        query = """
            SELECT
            pr.pr_line_id,
            pr.po_id,
            pr.request_id,
            max(pr.date) as date,
            max(pr.stock_date) as stock_date,
            max(pr.po_date_in) as po_date_in,
            max(pr.product_id) as product_id,
            max(pr.product_id_pr) as product_id_pr,
            max(pr.product_id_po) as product_id_po,
            max(pr.product_id_st) as product_id_st,
            max(pr.picking_id) as picking_id,
            sum(pr.qty) as qty,
            sum(pr.qty_po) as qty_po,
            sum(pr.qty_received) as qty_received,
            sum(pr.qty_invoiced) as qty_invoiced
            FROM pr_report pr
            WHERE {0}
            group by 1,2,3
            {1}
            """.format(where, order_by)
        self.env.cr.execute(query)
        # print'==========',query
        query_result = self.env.cr.dictfetchall()


        # row += 1
        worksheet.freeze_panes(row+1, 7)
        # Open order
        for item in query_result:

            row+=1
            pr_line_id = False
            if item['pr_line_id']:
                pr_line_id = self.env['purchase.request.line'].browse(item['pr_line_id'])
            po_id = False
            po_line_id = False
            po_date_planned = ''
            if item['po_id']:
                po_id = self.env['purchase.order'].browse(item['po_id'])
                domain = [('order_id', '=', po_id.id), ('product_id', '=', item['product_id'])]
                if pr_line_id:
                    domain+=[('pr_line_many_ids','in',[pr_line_id.id])]
                po_line_id = self.env['purchase.order.line'].search(domain, limit=1)
                po_date_order = fields.Datetime.from_string(po_id.date_order)
                timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
                po_date_order = str(po_date_order.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19]
                if po_id.date_planned:
                    po_date_planned = fields.Datetime.from_string(po_id.date_planned)
                    timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
                    po_date_planned = str(po_date_planned.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19]

            picking_id = False
            picking_id_date_done = False
            if item['picking_id']:
                picking_id = self.env['stock.picking'].browse(item['picking_id'])
                picking_id_date_done = fields.Datetime.from_string(picking_id.date_done)
                timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
                picking_id_date_done = str(picking_id_date_done.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19] if picking_id_date_done else False
            product_id = self.env['product.product'].browse(item['product_id'])
            qty = item['qty']
            qty_po = item['qty_po']
            qty_received = item['qty_received']

            product_id_pr = self.env['product.product'].browse(item['product_id_pr']) if item['product_id_pr'] else False
            product_id_po = self.env['product.product'].browse(item['product_id_po']) if item['product_id_po'] else False
            product_id_st = self.env['product.product'].browse(item['product_id_st']) if item['product_id_st'] else False

            worksheet.write(row, 0, pr_line_id.request_id.name if pr_line_id else '', contest_center)
            worksheet.write(row, 1, pr_line_id.request_id.date if pr_line_id else '', contest_center)
            worksheet.write(row, 2, po_line_id.name if po_line_id else '', contest_center)
            worksheet.write(row, 3, po_id.origin if po_id else '', contest_center)
            worksheet.write(row, 4, po_id.name if po_id else '', contest_left)
            worksheet.write(row, 5, po_date_order if po_id else '', contest_left)

            worksheet.write(row, 6, po_id.picking_type_id.warehouse_id.name if po_id else '', contest_center)

            worksheet.write(row, 7, product_id_pr.default_code if product_id_pr else '', contest_center)
            worksheet.write(row, 8, product_id_pr.name if product_id_pr else '', contest_center)
            worksheet.write(row, 9, product_id_po.default_code if product_id_po else '', contest_center)
            worksheet.write(row, 10, product_id_po.name if product_id_po else '', contest_center)
            worksheet.write(row, 11, product_id_st.default_code if product_id_st else '', contest_center)
            worksheet.write(row, 12, product_id_st.name if product_id_st else '', contest_center)
            worksheet.write(row, 13, product_id.uom_id.name if product_id else '', contest_center)

            worksheet.write(row, 14, qty, contest_center)
            worksheet.write(row, 15, qty_po, contest_center)
            worksheet.write(row, 16, qty_received, contest_center)
            worksheet.write_formula(row, 17,'{=('+xl_rowcol_to_cell(row, 16)+'-'+xl_rowcol_to_cell(row, 14)+')}', contest_center)
            worksheet.write(row, 18, po_id.flow_line_id.name if po_id else '', contest_center)
            worksheet.write(row, 19, self.get_tech_name(pr_line_id), contest_center)

            worksheet.write(row, 20, str(po_date_planned)[:10] if po_id else '', contest_center)
            worksheet.write(row, 21, po_id.date_approve if po_id and po_id.date_approve else '', contest_center)
            worksheet.write_formula(row, 22,'{=(IF(OR( ISBLANK('+xl_rowcol_to_cell(row, 21)+'),ISBLANK('+xl_rowcol_to_cell(row, 20)+')),0,'+xl_rowcol_to_cell(row, 21)+'-'+xl_rowcol_to_cell(row, 20)+'))}', cell_format2)
            # worksheet.write_formula(row, 22,'{=(IFERROR(DATEDIF('+xl_rowcol_to_cell(row, 21)+','+xl_rowcol_to_cell(row, 20)+',"d"),0))}', cell_format2)
            worksheet.write(row, 23, picking_id_date_done if picking_id_date_done else '', contest_center)
            # worksheet.write_formula(row, 24,'{=(IFERROR(DATEDIF('+xl_rowcol_to_cell(row, 23)+','+xl_rowcol_to_cell(row, 20)+',"d"),0))}', cell_format2)
            worksheet.write_formula(row, 24,'{=(IF(OR( ISBLANK('+xl_rowcol_to_cell(row, 23)+'),ISBLANK('+xl_rowcol_to_cell(row, 20)+')),0,'+xl_rowcol_to_cell(row, 23)+'-'+xl_rowcol_to_cell(row, 20)+'))}', cell_format2)

            worksheet.write(row, 25, po_line_id.price_unit if po_line_id else '', cell_format2)
            worksheet.write(row, 26, po_line_id.price_tax if po_line_id else '', cell_format2)
            worksheet.write_formula(row, 27,'{=('+xl_rowcol_to_cell(row, 15)+'*'+xl_rowcol_to_cell(row, 25)+')}', cell_format2)
            worksheet.write_formula(row, 28,'{=('+xl_rowcol_to_cell(row, 16)+'*'+xl_rowcol_to_cell(row, 25)+')}', cell_format2)
            worksheet.write_formula(row, 29,'{=('+xl_rowcol_to_cell(row, 17)+'*'+xl_rowcol_to_cell(row, 25)+')}', cell_format2)
            worksheet.write(row, 30, po_id.partner_id.name if po_id else 'N/A', contest_center)


        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:D', 54)
        # worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 15)

        worksheet.set_column('I:I', 17)
        worksheet.set_column('K:K', 17)
        worksheet.set_column('M:M', 17)

        # worksheet.set_column('M:M', 10)
        # worksheet.set_column('N:N', 10)
        # worksheet.set_column('O:O', 15)
        # worksheet.set_column('P:P', 15)

        # worksheet.set_column('V:V', 20)
        # worksheet.set_column('W:W', 25)
        worksheet.set_column('AB:AD', 13)
        worksheet.set_column('AE:AE', 23)

        workbook.close()

        file_name = u'Delivery reports.xlsx'
        out = base64.encodestring(output.getvalue())
        attachment_value = {
            'name': file_name,
            'datas': out,
            'store_fname': file_name,
            'res_model': 'pr.report.excel',
            'res_id': self.id,
        }
        attachment_id = self.env['ir.attachment'].sudo().create(attachment_value)
        self.write({'attachment_ids': False})
        self.write({'attachment_ids': [(6,0,[attachment_id.id])]})

        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=ir.attachment&id=" + str(attachment_id.id) + "&filename_field=filename&download=true&field=datas&filename="+attachment_id.store_fname,
             'target': 'new',
        }

