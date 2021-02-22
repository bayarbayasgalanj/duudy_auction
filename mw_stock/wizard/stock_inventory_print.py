# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError, ValidationError
import pytz

class stock_inventory_print(models.TransientModel):
    _name = "stock.inventory.print"
    _description = 'stock inventory print'

    location_ids = fields.Many2many('stock.location',string='Байрлалууд', domain=[('usage','=','internal')])
    filter_inv = fields.Selection(string='Хэвлэх сонголт', selection='_selection_filter',)
    many_categ_ids = fields.Many2many('product.category', string=u'Ангилалууд')

    @api.model
    def _selection_filter(self):
        res_filter = [
            ('category_child_of', 'Дэд ангилалд тоолох'),
            ('category_many', 'Олон ангилалаар тоолох'),
            ]
        return res_filter

    def action_print(self):
        model_id = self.env['ir.model'].search([('model','=','stock.inventory.print')], limit=1)
        template = self.env['pdf.template.generator'].search([
            ('model_id','=',model_id.id),
            ('name','=','stock_inventory')], limit=1)
        if template:
            res = template.print_template(self.id)
            return res
        else:
            raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

    def get_move_line(self, ids):
        report_id = self.browse(ids)
        loc_name = 'Бүх Байрлал'
        domain = []
        if report_id.location_ids:
            loc_name = ', '.join(report_id.location_ids.mapped('display_name'))
            domain.append(('location_id','in',report_id.location_ids.ids))
        timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
        now_date = str(fields.Datetime.now().replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19] or ''
        
        if report_id.filter_inv=='category_child_of':
            domain.append(('product_id.categ_id','child_of',report_id.many_categ_ids.ids))
        elif report_id.filter_inv=='category_many':
            domain.append(('product_id.categ_id','in',report_id.many_categ_ids.ids))
        
        stock_quants = self.env['stock.quant'].search(domain, order='product_id')
        
        categ_ids = stock_quants.mapped('product_id.categ_id')
        filter_inv = 'Бүгд'
        if report_id.filter_inv=='category_child_of':
            filter_inv = 'Дэд ангилалд тоолох'
        elif report_id.filter_inv=='category_many':
            filter_inv = 'Олон ангилалаар тоолох'
        html = """
        <div style="page-break-after:always;">
        <table style="font-size: 12pt;  border:1px solid #4c4c4c; border-collapse:collapse; width: 100%;">
            <tr>
                <td style="border: 1px solid #4c4c4c; font-weight:bold;">Байрлалууд:</td>
                <td style="border: 1px solid #4c4c4c;"> """+str(loc_name)+""" </td>
                <td style="border: 1px solid #4c4c4c; font-weight:bold;">Хэвлэгдсэн Огноо:</td>
                <td style="border: 1px solid #4c4c4c;"> """+str(now_date)+""" </td>
            </tr>
             <tr>
                <td style="border: 1px solid #4c4c4c; font-weight:bold;">Хэвлэх сонголт:</td>
                <td style="border: 1px solid #4c4c4c;">"""+str(filter_inv)+"""</td>
                <td></td>
                <td></td>
            </tr>
        </table>
        """
        one_loc = ''
        if len(report_id.location_ids)>1:
            one_loc = '<td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 20%;">Байрлал</td>'
        lot_toi = ''
        if stock_quants.filtered(lambda r: r.lot_id):
            lot_toi = '<td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 15%;">Цуврал</td>'
        for item in categ_ids:
            c_name = item.display_name
            html += """
            <span style="font-size: 12pt; font-weight:bold;">"""+c_name+"""</span>
            <table style="page-break-inside:avoid; font-size: 9pt; width: 100%; border:1px solid #4c4c4c; border-collapse:collapse">
            <tr>
                <td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 5%;">№</td>
                <td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 10%;">Код</td>
                <td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 40%;">Барааны нэр</td>
                <td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 15%;">Хэмжих Нэгж</td>
                """+one_loc+""" """+lot_toi+"""
                <td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 10%;"><p style="padding-left: 10px;">Үлдэгдэл</p></td>
                <td style="page-break-inside:avoid; border: 1px solid #4c4c4c; width: 10%;"><p style="padding-left: 10px;">Тоолсон</p></td>
            </tr>
            """
            quants = stock_quants.filtered(lambda r: r.product_id.categ_id==item)
            nbr = 1
            for item in quants:
                default_code = item.product_id.default_code or ''
                r_product_name = item.product_id.name or ''
                product_uom_qty = item.quantity
                product_uom_name = item.product_id.uom_id.name
                location_name = ''
                if one_loc:
                    location_name = '<td style="page-break-inside:avoid; border: 1px solid #4c4c4c;">%s</td>'%(item.location_id.display_name)
                lot_name = ''
                if lot_toi:
                    lot_name = '<td style="page-break-inside:avoid; border: 1px solid #4c4c4c;">%s</td>'%(item.lot_id.display_name)
                ltemp = """<tr>
                    <td style="page-break-inside:avoid; border: 1px solid #4c4c4c;"><p style="text-align: center;">%s</p></td>
                    <td style="page-break-inside:avoid; border: 1px solid #4c4c4c;"><p style="text-align: center;">%s</p></td>
                    <td style="page-break-inside:avoid; border: 1px solid #4c4c4c;"><p style="text-align: left;">%s</p></td>
                    <td style="page-break-inside:avoid; border: 1px solid #4c4c4c;">%s</td>
                    %s
                    %s
                    <td style="page-break-inside:avoid; border: 1px solid #4c4c4c;"><p style="text-align: center;">%s</p></td>
                    <td style="page-break-inside:avoid; border: 1px solid #4c4c4c;"></td>
                """%(str(nbr), default_code, r_product_name, product_uom_name, location_name, lot_name, "{0:,.2f}".format(product_uom_qty))
                ltemp+='</tr>'
                html += ltemp
                nbr+=1

            html+="""</table>"""

        html+="""
        <br/>
        <table style="page-break-inside:avoid; font-size: 10pt; width: 100%;">
        <tr>
            <td style="page-break-inside:avoid; text-align:right; width: 60%;">Тоолсон:</td>
            <td style="page-break-inside:avoid; border-bottom: 1px solid #4c4c4c; width: 40%;"></td>
        </tr>
        <tr>
            <td style="page-break-inside:avoid; text-align:right; ">Хүлээлцсэн:</td>
            <td style="page-break-inside:avoid; border-bottom: 1px solid #4c4c4c;"></td>
        </tr>
        </table>
        </div>"""
        return html
