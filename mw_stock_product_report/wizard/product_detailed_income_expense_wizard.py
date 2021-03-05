# -*- coding: utf-8 -*-

import time
from odoo import _, tools
from datetime import datetime, timedelta
from odoo import api, fields, models
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)

class ProductDetailedIncomeExpenseReport(models.TransientModel):
    _name = "product.detailed.income.expense"  
    _description = "product detailed income expense"
    
    date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
    date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
    product_tmpl_ids = fields.Many2many('product.template', string=u'Бараа/Template', help=u"Тайланд гарах бараануудыг сонгоно")
    warehouse_id = fields.Many2many('stock.warehouse', string=u'Агуулах',required=True, )
    location_ids = fields.Many2many('stock.location', string=u'Байрлал',)
    product_ids = fields.Many2many('product.product', string=u'Бараанууд', help=u"Тайланд гарах барааг сонгоно")
    categ_ids = fields.Many2many('product.category', string=u'Барааны ангилал', help=u"Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
    date_range_id = fields.Many2one('date.range',string='Огнооны хязгаар')
    assigned_user_id = fields.Many2one('res.users', string=u'Нөөцөлсөн хэрэглэгч' )
    included_internal = fields.Boolean(string=u'Дотоод хөдөлгөөн оруулахгүй', default=False)
    move_type = fields.Selection([
            ('income', u'Орлого'), 
            ('expense', u'Зарлага'),
            ('only_in_out', u'Орлого/Зарлага'),
            ('income_expense', u'Эхний/Орлого/Зарлага/Үлдэгдэл'),
            ('balance', u'Үлдэгдэл'),
        ], default='income', string=u'Төрөл')
    move_state = fields.Selection([
            ('cancel', u'Бүгд'),
            ('assigned_done', u'Бэлэн болон Дууссан'), 
            ('confirmed', u'Бэлэн болохыг хүлээж байгаа'), 
            ('assigned', u'Бэлэн'),
            ('done', u'Дууссан'),
        ], default='done', string=u'Төлөв',)

    tz = fields.Integer(u'Цагийн бүсийн зөрүү', required=True, default=8)
    import_wh = fields.Boolean(u'Бүх агуулах ОРУУЛАХ/АРИЛГАХ', default=False)
    see_value = fields.Boolean(string=u'Өртөгтэй Харах', default=False, groups="mw_stock_product_report.group_stock_see_price_unit")
    no_category_total = fields.Boolean(string=u'Ангилалгүй гаргах', default=False)
    with_attribute = fields.Boolean(string=u'Аттрибуттай', default=False)
    
    @api.onchange('import_wh')
    def onchange_all_wh_import(self):
        if self.import_wh:
            self.warehouse_id = self.env['stock.warehouse'].search([])
        else:
            self.warehouse_id = False
    
    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_start = self.date_range_id.date_start
        self.date_end = self.date_range_id.date_end
    def get_tuple(self, obj, categ_is=False):
        if categ_is:
            obj = self.env['product.category'].search([('id','child_of',obj)]).ids
            
        if len(obj) > 1:
            return str(tuple(obj))
        else:
            return " ("+str(obj[0])+") "
    def get_domain(self, domain, donwload=False):
        domain_val = ''
        if donwload:
            if self.product_ids:
                domain_val +=" and rep.product_id in %s "%(self.get_tuple(self.product_ids.ids))
            if self.product_tmpl_ids:
                domain_val +=" and rep.product_tmpl_id in %s "%(self.get_tuple(self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain_val +=" and rep.categ_id in %s "%(self.get_tuple(self.categ_ids.ids, True))
            if self.move_state =='cancel':
                domain_val +=" and rep.state != '%s' "%(self.move_state)
            elif self.move_state == 'assigned_done':
                domain_val +=" and rep.state in ('done','assigned') "
            else:
                domain_val +=" and rep.state = '%s' "%(self.move_state)
            if self.location_ids:
                domain_val +=" and rep.location_id in %s "%(self.get_tuple(self.location_ids.ids))
            elif self.warehouse_id:
                domain_val +=" and rep.warehouse_id in %s "%(self.get_tuple(self.warehouse_id.ids))
            if self.included_internal:
                domain_val +=" and rep.transfer_type != 'internal' "
            domain_val +=" and (rep.date_balance < '%s' or (rep.date_expected>='%s' and rep.date_expected<= '%s')) "%(self.date_start,self.date_start,self.date_end)
            return domain_val
        if self.move_type =='expense':
            print('============',domain)
            domain.append(('date_expected','>=',self.date_start))
            domain.append(('date_expected','<=',self.date_end))
            if self.product_ids:
                domain.append(('product_id','in',self.product_ids.ids))
            if self.product_tmpl_ids:
                domain.append(('product_tmpl_id','in',self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain.append(('categ_id','child_of',self.categ_ids.ids))
            if self.move_state =='cancel':
                domain.append(('state','!=',self.move_state))
            elif self.move_state == 'assigned_done':
                domain.append(('state','in',['done','assigned']))
            else:
                domain.append(('state','=',self.move_state))
            if self.location_ids:
                domain.append(('location_id','in',self.location_ids.ids))
            elif self.warehouse_id:
                domain.append(('warehouse_id','in',self.warehouse_id.ids))
            if self.included_internal:
                domain.append(('transfer_type','!=','internal'))
        if self.move_type =='income':
            domain.append(('date_expected','>=',self.date_start))
            domain.append(('date_expected','<=',self.date_end))
            if self.product_ids:
                domain.append(('product_id','in',self.product_ids.ids))
            if self.product_tmpl_ids:
                domain.append(('product_tmpl_id','in',self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain.append(('categ_id','child_of',self.categ_ids.ids))
            if self.move_state =='cancel':
                domain.append(('state','!=',self.move_state))
            elif self.move_state == 'assigned_done':
                domain.append(('state','in',['done','assigned']))
            else:
                domain.append(('state','=',self.move_state))
            if self.location_ids:
                domain.append(('location_dest_id','in',self.location_ids.ids))
            elif self.warehouse_id:
                domain.append(('warehouse_dest_id','in',self.warehouse_id.ids))
            if self.included_internal:
                domain.append(('transfer_type','!=','internal'))
        if self.move_type == 'only_in_out':
            domain.append(('date_expected','>=',self.date_start))
            domain.append(('date_expected','<=',self.date_end))
            if self.product_ids:
                domain.append(('product_id','in',self.product_ids.ids))
            if self.product_tmpl_ids:
                domain.append(('product_tmpl_id','in',self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain.append(('categ_id','child_of',self.categ_ids.ids))
            if self.move_state =='cancel':
                domain.append(('state','!=',self.move_state))
            elif self.move_state == 'assigned_done':
                domain.append(('state','in',['done','assigned']))
            else:
                domain.append(('state','=',self.move_state))
            if self.location_ids:
                domain.append(('location_dest_id','in',self.location_ids.ids))
            elif self.warehouse_id:
                domain.append(('warehouse_dest_id','in',self.warehouse_id.ids))
            if self.included_internal:
                domain.append(('transfer_type','!=','internal'))

        if self.move_type == 'income_expense':
            if self.product_ids:
                domain.append(('product_id','in',self.product_ids.ids))
            if self.product_tmpl_ids:
                domain.append(('product_tmpl_id','in',self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain.append(('categ_id','child_of',self.categ_ids.ids))
            if self.move_state =='cancel':
                domain.append(('state','!=',self.move_state))
            elif self.move_state == 'assigned_done':
                domain.append(('state','in',['done','assigned']))
            else:
                domain.append(('state','=',self.move_state))
            if self.location_ids:
                domain.append(('location_id','in',self.location_ids.ids))
            elif self.warehouse_id:
                domain.append(('warehouse_id','in',self.warehouse_id.ids))
            if self.included_internal:
                domain.append(('transfer_type','!=','internal'))
            domain.append('|')
            domain.append(('date_balance','<',self.date_start))
            domain.append('&')
            domain.append(('date_expected','<=',self.date_end))
            domain.append(('date_expected','>=',self.date_start))
            
        if self.move_type == 'balance':
            if self.product_ids:
                domain.append(('product_id','in',self.product_ids.ids))
            if self.product_tmpl_ids:
                domain.append(('product_tmpl_id','in',self.product_tmpl_ids.ids))
            if self.categ_ids:
                domain.append(('categ_id','child_of',self.categ_ids.ids))
            if self.move_state =='cancel':
                domain.append(('state','!=',self.move_state))
            elif self.move_state == 'assigned_done':
                domain.append(('state','in',['done','assigned']))
            else:
                domain.append(('state','=',self.move_state))
            if self.location_ids:
                domain.append(('location_id','in',self.location_ids.ids))
            elif self.warehouse_id:
                domain.append(('warehouse_id','in',self.warehouse_id.ids))
            domain.append(('date_expected','<=',self.date_end))
            if self.included_internal:
                domain.append(('transfer_type','!=','internal'))
        return domain
    def open_analyze_view(self):
        domain = []
        if self.move_type=='income':
            action = self.env.ref('mw_stock_product_report.action_product_income_expense_report_in')
        elif self.move_type=='expense':
            action = self.env.ref('mw_stock_product_report.action_product_income_expense_report_out')
        elif self.move_type=='income_expense':
            action = self.env.ref('mw_stock_product_report.action_stock_report_detail')
        elif self.move_type=='only_in_out':
            action = self.env.ref('mw_stock_product_report.action_product_both_income_expense_report')
        elif self.move_type=='balance':
            action = self.env.ref('mw_stock_product_report.action_product_balance_pivot_report')
        vals = action.read()[0]
        vals['domain'] = self.get_domain(domain)
        print('====--------',self.get_domain(domain))
        return vals

    
    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        worksheet = workbook.add_worksheet(u'Бараа материалын тайлан')
        file_name = 'БМ тайлан.xlsx'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#6495ED')

        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(9)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        header_wrap.set_bg_color('#6495ED')

        footer = workbook.add_format({'bold': 1})
        footer.set_text_wrap()
        footer.set_font_size(9)
        footer.set_align('right')
        footer.set_align('vcenter')
        footer.set_border(style=1)
        footer.set_bg_color('#6495ED')
        footer.set_num_format('#,##0.00')

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_right_red = workbook.add_format()
        contest_right_red.set_text_wrap()
        contest_right_red.set_font_size(9)
        contest_right_red.set_align('right')
        contest_right_red.set_align('vcenter')
        contest_right_red.set_font_color('red')
        contest_right_red.set_num_format('#,##0.00')

        contest_right_green = workbook.add_format()
        contest_right_green.set_text_wrap()
        contest_right_green.set_font_size(9)
        contest_right_green.set_align('right')
        contest_right_green.set_align('vcenter')
        contest_right_green.set_font_color('green')
        contest_right_green.set_num_format('#,##0.00')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)
        contest_left.set_num_format('#,##0.00')

        contest_left0 = workbook.add_format()
        contest_left0.set_font_size(9)
        contest_left0.set_align('left')
        contest_left0.set_align('vcenter')

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)

        categ_name = workbook.add_format({'bold': 1})
        categ_name.set_font_size(9)
        categ_name.set_align('left')
        categ_name.set_align('vcenter')
        categ_name.set_border(style=1)
        categ_name.set_bg_color('#B9CFF7')

        categ_right = workbook.add_format({'bold': 1})
        categ_right.set_font_size(9)
        categ_right.set_align('right')
        categ_right.set_align('vcenter')
        categ_right.set_border(style=1)
        categ_right.set_bg_color('#B9CFF7')
        categ_right.set_num_format('#,##0.00')

        # ======= GET Filter, Conditions
        domain = self.get_domain([], True)
        order_by = ' ORDER BY rep.categ_id  '
        group_by = ''
        left_join = ''
        select_from = ''
        if not self.no_category_total:
            order_by = ' ORDER BY pc.complete_name, pt.name  '
            group_by += ' ,pc.complete_name '
            left_join += 'left join product_category as pc on (pc.id=rep.categ_id)'
            select_from += ' pc.complete_name, '
        if self.with_attribute:
            left_join += """ left join product_attribute_value_product_product_rel val_rel on (val_rel.product_product_id=rep.product_id)
                left join product_attribute_value attr on (val_rel.product_attribute_value_id=attr.id) """
            select_from += """ case when NULLIF(count(distinct attr.name),0)>0  then pt.name||' ('||coalesce(STRING_AGG(distinct attr.name,','),'')||')' else pt.name end as product_name, 
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_first)/NULLIF(count(distinct attr.name),1) else sum(rep.qty_first) end as qty_first,
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_first)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_first) end as total_price_first,
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_last)/NULLIF(count(distinct attr.name),1)  else sum(rep.qty_last) end as qty_last,
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_last)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_last) end as total_price_last,
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_income)/NULLIF(count(distinct attr.name),1)  else sum(rep.qty_income) end as qty_income,
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_income)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_income) end as total_price_income,
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_expense)/NULLIF(count(distinct attr.name),1)  else sum(rep.qty_expense) end as qty_expense,
                    case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_expense)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_expense) end as total_price_expense"""
        else:
            select_from += """ pt.name as product_name,
                    sum(rep.qty_first) as qty_first,
                    sum(rep.total_price_first) as total_price_first,
                    sum(rep.qty_last) as qty_last,
                    sum(rep.total_price_last) as total_price_last,
                    sum(rep.qty_income) as qty_income,
                    sum(rep.total_price_income) as total_price_income,
                    sum(rep.qty_expense) as qty_expense,
                    sum(rep.total_price_expense) as total_price_expense """
        query1 = """
                SELECT 
                    rep.product_id,
                    rep.default_code,
                    rep.barcode,
                    pu.name as uom_name,
                    rep.categ_id,
                    {4}
                    
                FROM stock_report_detail as rep
                left join product_template as pt on (pt.id=rep.product_tmpl_id)
                left join uom_uom as pu on (pu.id=rep.uom_id)
                {3}
                WHERE 
                    1=1 {0}
                GROUP BY 1,2,3,4,5,pt.name {2}
                {1}
             """.format(domain, order_by, group_by, left_join, select_from)
        
        self.env.cr.execute(query1)
        query_result = self.env.cr.dictfetchall()
        w_names = ', '.join(self.warehouse_id.mapped('name'))

        worksheet.write(1,3, u"Бараа материалын дэлгэрэнгүй тайлан", h1)
        worksheet.write(2,0, u"Агуулах: " + w_names, contest_left0)
        worksheet.write(3,0, u"Тайлан бэлдсэн: " + str(datetime.now()), contest_left0)
        worksheet.write(4,0, u"Тайлант үеийн хугацаа: " + str(self.date_start) +" ~ "+ str(self.date_end), contest_left0)
        worksheet.write(5,0, u"Дотоод хөдөлгөөн: Оруулахгүй" if self.included_internal else u"Дотоод хөдөлгөөн: Орсон", contest_left0)
        
        get_cost = self.sudo().see_value
        row = 6
        col = 0
        worksheet.write(row, col, u"№", header)
        worksheet.write(row, col+1, u"Код", header_wrap)
        worksheet.write(row, col+2, u"Бараа", header_wrap)
        worksheet.write(row, col+3, u"Хэмжих нэгж", header_wrap)
        worksheet.write(row, col+4, u"Баркод", header_wrap)
        worksheet.write(row, col+5, u"Эхний үлдэгдэл", header_wrap)
        if get_cost:
            worksheet.write(row, col+6, u"Өртөг Эхний үлдэгдэл", header_wrap)
            col+=1
        worksheet.write(row, col+6, u"Орлого", header_wrap)
        if get_cost:
            worksheet.write(row, col+7, u"Өртөг Орлого", header_wrap)
            col+=1
        worksheet.write(row, col+7, u"Зарлага", header_wrap)
        if get_cost:
            worksheet.write(row, col+8, u"Өртөг Зарлага", header_wrap)
            col+=1
        worksheet.write(row, col+8, u"Эцсийн үлдэгдэл", header_wrap)
        if get_cost:
            worksheet.write(row, col+9, u"Өртөг Эцсийн үлдэгдэл", header_wrap)
            col+=1
        sum_col = col+9
        worksheet.freeze_panes(7, 4)
        row+=1
        categ_ids = []
        number=1
        first_categ = 0
        save_rows = []
        first_first_row = row
        first_row = row
        for item in query_result:
            if not self.no_category_total and first_categ!=item['categ_id']:
                categ_name_print = item['complete_name'] or ''
                worksheet.write(row, 0, categ_name_print, categ_name)
                for cc in range(1, sum_col):
                    worksheet.write(row, cc, '', categ_name)
                first_categ = item['categ_id']
                last_row = row
                if len(save_rows)>0:
                    last_row = save_rows[len(save_rows)-1]['current_row']
                save_rows.append({'last_row': last_row,'first_row': first_row , 'row_1': row-1, 'current_row': row})
                row += 1
                first_row = row
            product_name = item['product_name'] or ''
            # product_name = self.env['product.product'].browse(item['product_id']).display_name
            uom_name = item['uom_name'] or ''
            default_code = item['default_code'] or ''
            barcode = item['barcode'] or ''
            col = 0
            worksheet.write(row, col, number, contest_center)
            worksheet.write(row, col+1, default_code, contest_center)
            worksheet.write(row, col+2, product_name, contest_left)
            worksheet.write(row, col+3, uom_name, contest_center)
            worksheet.write(row, col+4, barcode, contest_center)
            worksheet.write(row, col+5, item['qty_first'], contest_right)
            if get_cost:
                worksheet.write(row, col+6, item['total_price_first'], contest_right)
                col+=1
            worksheet.write(row, col+6, item['qty_income'], contest_right)
            if get_cost:
                worksheet.write(row, col+7, item['total_price_income'], contest_right)
                col+=1
            worksheet.write(row, col+7, item['qty_expense'], contest_right)
            if get_cost:
                worksheet.write(row, col+8, item['total_price_expense'], contest_right)
                col+=1
            worksheet.write(row, col+8, item['qty_last'], contest_right)
            if get_cost:
                worksheet.write(row, col+9, item['total_price_last'], contest_right)
                col+=1
            row += 1
            number += 1
        sum_val1 = ''
        sum_val2 = ''
        sum_val3 = ''
        sum_val4 = ''
        sum_val5 = ''
        sum_val6 = ''
        sum_val7 = ''
        sum_val8 = ''
        if not self.no_category_total:
            last_row = row
            if len(save_rows)>0:
                last_row = save_rows[len(save_rows)-1]['current_row']
            save_rows.append({'last_row': last_row,'first_row': first_row , 'row_1': row-1, 'current_row': False})
            for cc in save_rows:
                last_row = cc['last_row']
                first_row = cc['first_row']
                row_1 = cc['row_1']
                current_row = cc['current_row']
                col = 0
                sum_val1 += '+'+(self._symbol(current_row, col+5) if current_row else '0')
                worksheet.write_formula(last_row, col+5,'{=sum('+ self._symbol(first_row, col+5)+':'+ self._symbol(row_1,col+5) +')}', categ_right)
                if get_cost:
                    sum_val2 += '+'+(self._symbol(current_row, col+6) if current_row else '0')
                    worksheet.write_formula(last_row, col+6,'{=sum('+ self._symbol(first_row, col+6)+':'+ self._symbol(row_1,col+6) +')}', categ_right)
                    col+=1
                sum_val3 += '+'+(self._symbol(current_row, col+6) if current_row else '0')
                worksheet.write_formula(last_row, col+6,'{=sum('+ self._symbol(first_row, col+6)+':'+ self._symbol(row_1,col+6) +')}', categ_right)
                if get_cost:
                    sum_val4 += '+'+(self._symbol(current_row, col+7) if current_row else '0')
                    worksheet.write_formula(last_row, col+7,'{=sum('+ self._symbol(first_row, col+7)+':'+ self._symbol(row_1,col+7) +')}', categ_right)
                    col+=1
                sum_val5 += '+'+(self._symbol(current_row, col+7) if current_row else '0')
                worksheet.write_formula(last_row, col+7,'{=sum('+ self._symbol(first_row, col+7)+':'+ self._symbol(row_1,col+7) +')}', categ_right)
                if get_cost:
                    sum_val6 += '+'+(self._symbol(current_row, col+8) if current_row else '0')
                    worksheet.write_formula(last_row, col+8,'{=sum('+ self._symbol(first_row, col+8)+':'+ self._symbol(row_1,col+8) +')}', categ_right)
                    col+=1
                sum_val7 += '+'+(self._symbol(current_row, col+8) if current_row else '0')
                worksheet.write_formula(last_row, col+8,'{=sum('+ self._symbol(first_row, col+8)+':'+ self._symbol(row_1,col+8) +')}', categ_right)
                if get_cost:
                    sum_val8 += '+'+(self._symbol(current_row, col+9) if current_row else '0')
                    worksheet.write_formula(last_row, col+9,'{=sum('+ self._symbol(first_row, col+9)+':'+ self._symbol(row_1,col+9) +')}', categ_right)
                    col+=1
                
        else:
            col = 0
            sum_val1 = self._symbol(first_first_row, col+5)+':'+ self._symbol(row-1,col+5)
            if get_cost:
                sum_val2 = self._symbol(first_first_row, col+6)+':'+ self._symbol(row-1,col+6)
                col+=1
            sum_val3 = self._symbol(first_first_row, col+6)+':'+ self._symbol(row-1,col+6)
            if get_cost:
                sum_val4 = self._symbol(first_first_row, col+7)+':'+ self._symbol(row-1,col+7)
                col+=1
            sum_val5 = self._symbol(first_first_row, col+7)+':'+ self._symbol(row-1,col+7)
            if get_cost:
                sum_val6 = self._symbol(first_first_row, col+8)+':'+ self._symbol(row-1,col+8)
                col+=1
            sum_val7 = self._symbol(first_first_row, col+8)+':'+ self._symbol(row-1,col+8)
            if get_cost:
                sum_val8 = self._symbol(first_first_row, col+9)+':'+ self._symbol(row-1,col+9)
                col+=1
        col = 0
        worksheet.write_formula(row, col+5,'{=sum('+ sum_val1 +')}', footer)
        if get_cost:
            worksheet.write_formula(row, col+6,'{=sum('+ sum_val2 +')}', footer)
            col+=1
        worksheet.write_formula(row, col+6,'{=sum('+ sum_val3 +')}', footer)
        if get_cost:
            worksheet.write_formula(row, col+7,'{=sum('+ sum_val4 +')}', footer)
            col+=1
        worksheet.write_formula(row, col+7,'{=sum('+ sum_val5 +')}', footer)
        if get_cost:
            worksheet.write_formula(row, col+8,'{=sum('+ sum_val6 +')}', footer)
            col+=1
        worksheet.write_formula(row, col+8,'{=sum('+ sum_val7 +')}', footer)
        if get_cost:
            worksheet.write_formula(row, col+9,'{=sum('+ sum_val8 +')}', footer)
            col+=1
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 13)
        worksheet.set_column('C:C', 35)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:M', 14)

        # CLOSE
        workbook.close()
        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
                'type' : 'ir.actions.act_url',
                'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
                'target': 'new',
        }

    def _symbol(self, row, col):
        return self._symbol_col(col) + str(row+1)
    def _symbol_col(self, col):
        excelCol = str()
        div = col+1
        while div:
            (div, mod) = divmod(div-1, 26)
            excelCol = chr(mod + 65) + excelCol
        return excelCol
