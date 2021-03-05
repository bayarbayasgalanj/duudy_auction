# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.osv import expression
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    sched_date = fields.Date('Товлогдсон өдөр', compute='_comute_sched_date', store=True)
    printed_count = fields.Integer('Хэвлэгдсэн тоо', default=0)
    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=False,
        readonly=True, required=True,
        states={'draft': [('readonly', False)]})

    date_not_equal = fields.Boolean(string='Батлагдсан Огноо Зөрүүтэй', compute='_compute_date_not_equal', store=True)
    month_not_equal = fields.Boolean(string='Батлагдсан Сар Зөрүүтэй', compute='_compute_date_not_equal', store=True)
    date_done = fields.Datetime('Date of Transfer', copy=False, readonly=True, help="Completion Date of Transfer", track_visibility='onchange')
    view_from_loc_on_hand = fields.Boolean(related='picking_type_id.view_from_loc_on_hand', readonly=True)
    
    move_product_view_on_hand = fields.Boolean(string='Зөвхөн Үлдэгдэлтэй Барааг харах', copy=False, default=False)
    
    def copy_qty_to_done(self):
        self.ensure_one()
        if self.state not in ['done','cancel']:
            if self.show_operations:
                for line in self.move_line_ids_without_package:
                    if not line.qty_done:
                        line.qty_done = line.product_uom_qty
            else:
                for line in self.move_lines:
                    if not line.quantity_done:
                        line._set_quantity_done(line.reserved_availability)
    
    def copy_uom_qty_to_done(self):
        self.ensure_one()
        if self.state not in ['done','cancel']:
            for line in self.move_lines:
                if not line.quantity_done:
                    line._set_quantity_done(line.product_uom_qty)

    def get_now_date(self, ids):
        now_date = (datetime.now() + timedelta(hours=8)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return str(now_date)

    @api.depends('scheduled_date','date_done')
    def _compute_date_not_equal(self):
        for item in self:
            if item.date_done and item.scheduled_date:
                scheduled_date = item.scheduled_date+timedelta(hours=8)
                date_done = item.date_done+timedelta(hours=8)
                
                if scheduled_date.strftime( "%Y-%m-%d")!=date_done.strftime( "%Y-%m-%d"):
                    item.date_not_equal = True
                else:
                    item.date_not_equal = False

                if scheduled_date.strftime( "%Y-%m")!=date_done.strftime( "%Y-%m"):
                    item.month_not_equal = True
                else:
                    item.month_not_equal = False
            else:
                item.date_not_equal = False
                item.month_not_equal = False
                
    # Nemelt medeeleld shoshgo hevleh button
    
    def action_barcode_print(self):
        p_ids =  self.move_lines.mapped('product_id')
        move_ids =  self.move_lines
        move_lines = []
        for line in self.move_lines:
            temp = (0,0,{
                'product_id': line.product_id.id,
                'qty': line.product_uom_qty,
            })
            move_lines.append(temp)
        print_obj = self.env['stock.barcode.print'].create({
                                        'custom_date': self.scheduled_date,
                                        'custom_partner': self.partner_id.id or False,
                                        'line_ids': move_lines,
                                        # 'product_ids':[(6,0,p_ids.ids)],
                                        'stock_move_ids':[(6,0,move_ids.ids)],
                                        'name':'fff'
                                    })
        print_obj.onchange_type_size()
        mod_obj = self.env['ir.model.data']
        form_res = mod_obj.get_object_reference('mw_stock', 'stock_barcode_print_form')
        form_id = form_res and form_res[1] or False

        return {
                'name': _('Report'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.barcode.print',
                'view_id': False,
                'res_id':print_obj.id,
                'views': [(form_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
    
    @api.depends('scheduled_date')
    def _comute_sched_date(self):
        for item in self:
            if item.scheduled_date:
                scheduled_date = item.scheduled_date+timedelta(hours=8)
                item.sched_date = scheduled_date.strftime( "%Y-%m-%d")
            
    @api.onchange('picking_type_id', 'partner_id')
    def onchange_picking_type(self):
        res = super(StockPicking, self).onchange_picking_type()
        if self.picking_type_id.code=='internal':
            self.location_dest_id = False
        
        return res

    
    def get_picking_type_name(self, ids):
        
        report_id = self.browse(ids)
        if report_id.picking_type_id.code=='outgoing':
            return u'ЗАРЛАГЫН БАРИМТ:'
        elif report_id.picking_type_id.code=='internal':
            return u'ДОТООД ШИЛЖҮҮЛЭГ ЗАРЛАГЫН БАРИМТ:'
        elif report_id.picking_type_id.code=='incoming' and report_id.backorder_id:
            return u'БУЦААЛТЫН ОРЛОГЫН БАРИМТ:'
        else:
            return u'ОРЛОГЫН БАРИМТ:'
    
    # Picking ноорог болгох
    
    def action_to_draft(self):
        if self.state in ['cancel']:
            for line in self.move_lines:
                line.state = 'draft'
            self.is_locked = False

    def action_to_force_unreverse(self):
        if self.move_line_ids:
            query = ("""UPDATE stock_move_line set product_qty=0 where picking_id=%s;"""% (self.id))
            self.env.cr.execute(query)
            self.do_unreserve()
    
    def get_company_logo(self, ids):    
        report_id = self.browse(ids)
        image_buf = report_id.company_id.logo_web.decode('utf-8')
        image_str = '';
        if len(image_buf)>10:
            image_str = '<img alt="Embedded Image" width="100" src="data:image/png;base64,%s" />'%(image_buf)
        return image_str
  
    def get_user_signature_wo(self,ids):
        report_id = self.browse(ids)
        html = '<table>'
        image_str = '________________________'
        user_id = report_id.maintenance_workorder_id.validator_id
        image_str = ''
        if user_id.digital_signature:
            image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
        user_str =  '________________________'
        if user_id:
            user_str = user_id.name
        html += u'<tr><td><p>Мастер </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

        user_id = report_id.maintenance_workorder_id.parts_user_id
        image_str = ''
        if user_id.digital_signature:
            image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
        user_str =  '________________________'
        if user_id:
            user_str = user_id.name
        html += u'<tr><td><p>Сэлбэг батласан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

        user_id = report_id.maintenance_workorder_id.senior_user_id
        image_str = ''
        if user_id.digital_signature:
            image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'
        user_str =  '________________________'
        if user_id:
            user_str = user_id.name
        html += u'<tr><td><p>Ахлах батласан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

        user_id = report_id.maintenance_workorder_id.chief_user_id
        image_str = ''
        if user_id.digital_signature:
            image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,'+user_id.digital_signature+'" />'

        user_str =  '________________________'
        if user_id:
            user_str = user_id.name
        html += u'<tr><td><p>Батласан </p></td><td>'+image_str+u'</td><td> <p>/'+user_str+u'/</p></td></tr>'

        html += '</table>'   
        return html

    def get_user_signature(self,ids):
        report_id = self.browse(ids)
        expense_id = self.env['stock.product.other.expense'].search([('expense_picking_id','=',report_id.id)])
        if expense_id:
            return expense_id.get_user_signature(expense_id.id)
        else:
            return ''
    
    def get_price_unit(self, move_id):
        return move_id.price_unit

    def get_move_product_line(self, ids):
        datas = []
        report_id = self.browse(ids)

        i = 1
        lines = []
        move_print = True
        if report_id.state in ['done','assigned']:
            lines = report_id.move_line_ids
            move_print = False
        else:
            lines = report_id.move_lines
        sum1 = 0
        sum2 = 0
        sum3 = 0
        sum4 = 0
        sum5 = 0
        nbr = 1
        print_lot = False
        if report_id.move_lines.filtered(lambda r:r.product_id.tracking in ['serial','lot']):
            print_lot = True
        for line in lines:
            if not move_print:
                location_name = line.location_id.name
                location_dest_name = line.location_dest_id.name
                product_uom_id = line.product_uom_id
                product_uom_qty = line.product_uom_qty
                qty_done = line.qty_done
                if line.qty_done==0:
                    qty_done = line.product_uom_qty
                lot_text = line.lot_id.name or ''
            else:
                location_name = ''
                location_dest_name = ''
                product_uom_id = line.product_uom
                product_uom_qty = line.product_uom_qty
                qty_done = 0
                lot_text = ', '.join(line.move_line_ids.mapped('lot_id.name')) or ''

            sum2 += product_uom_qty
            sum3 += qty_done

            r_product_name = line.product_id.name
            product_code = line.product_id.product_code or ''
            default_code = line.product_id.default_code or ''
            temp = [
                u'<p style="text-align: center;">'+str(nbr)+u'</p>',
                u'<p style="text-align: center;">'+(product_code)+u'</p>',
                u'<p style="text-align: center;">'+(default_code)+u'</p>',
                u'<p style="text-align: left;">'+(r_product_name)+u'</p>', 
                "{0:,.2f}".format(product_uom_qty) or '',
                "{0:,.2f}".format(qty_done) or '',
                u'<p style="text-align: center;">'+(product_uom_id.name)+u'</p>', 
            ]
            if report_id.picking_type_id.with_print_on_hand:
                if not move_print:
                    on_hand_from_loc = sum(line.product_id.stock_quant_ids.filtered(lambda r: r.location_id.id==line.location_id.id).mapped('quantity'))
                else:
                    on_hand_from_loc = sum(line.product_id.stock_quant_ids.filtered(lambda r: r.location_id.id==line.location_id.id).mapped('quantity'))
                sum5 += on_hand_from_loc
                temp.insert(4, "{0:,.2f}".format(on_hand_from_loc) or '')
            if report_id.picking_type_id.with_print_location:
                temp.insert(4, u'<p style="text-align: left;">'+(location_name)+u'</p>')
                temp.insert(5, u'<p style="text-align: left;">'+(location_dest_name)+u'</p>')
            if print_lot:
                temp.insert(4, lot_text)

            if report_id.picking_type_id.code=='outgoing' and report_id.picking_type_id.last_expense_out:
                last_expense_date =  self.env['stock.picking'].search([
                    ('id','!=',report_id.id),('state','=','done'),
                    ('move_lines.product_id','=',line.product_id.id),
                    ('picking_type_id','=',report_id.picking_type_id.id)
                    ], limit=1, order='date_done desc').date_done
                last_date = ''
                if not last_expense_date:
                    last_expense_date = ''
                    last_date = ''
                else:
                    date = fields.Datetime.from_string(last_expense_date)
                    timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
                    last_date = str(date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19]
                temp.append(last_date)
                
            if report_id.picking_type_id.with_print_cost:
                if move_print:
                    price_unit = self.get_price_unit(line)
                else:
                    price_unit = self.get_price_unit(line.move_id)
                sum_price_unit = price_unit*qty_done
                sum4+=sum_price_unit
                temp.append("{0:,.2f}".format(price_unit) or '')
                temp.append("{0:,.2f}".format(sum_price_unit) or '')

            nbr += 1
            datas.append(temp)
            i += 1
        temp = [
            u'',
            u'<p style="text-align: center;">Нийт дүн</p>', 
            u'',
            u'',
            "{0:,.2f}".format(sum2) or '',
            "{0:,.2f}".format(sum3) or '',
            u'',
        ]
        
        if report_id.picking_type_id.with_print_on_hand:
            temp.insert(4, "{0:,.2f}".format(sum5) or '',)
        if report_id.picking_type_id.with_print_location:
            temp.insert(4, u'')
            temp.insert(5, u'')
        if print_lot:
            temp.insert(4, u'')
        
        if report_id.picking_type_id.code=='outgoing' and report_id.picking_type_id.last_expense_out:
            temp.append('')

        if report_id.picking_type_id.with_print_cost:
            temp.append('')
            temp.append("{0:,.2f}".format(sum4) or '')

        if not datas:
            return False
        datas.append(temp)
        return datas

    
    def get_move_line(self, ids):
        report_id = self.browse(ids)
        header_qty = 'Олгосон'
        if report_id.picking_type_id.code in ['incoming']:
            header_qty = 'Авсан'
        headers = [
            u'Д/д',
            u'Код',
            u'Эдийн дугаар',
            u'Барааны нэр',
            u'<p style="padding-left: 10px;">Тоо хэмжээ</p>',
            u'<p style="padding-left: 10px;">'+header_qty+'</p>',
            u'Хэмжих Нэгж',
            ]
        if report_id.picking_type_id.with_print_on_hand:
            headers.insert(4, u'Үлдэгдэл')
        if report_id.picking_type_id.with_print_location:
            headers.insert(4, u'Гарах')
            headers.insert(5, u'Хүрэх')
        if report_id.move_lines.filtered(lambda r:r.product_id.tracking in ['serial','lot']):
            headers.insert(4, u'Лот/Сериал')

        if report_id.picking_type_id.code in ['outgoing'] and report_id.picking_type_id.last_expense_out:
            headers.append(u'Сүүлд зарлага огноо')
        if report_id.picking_type_id.with_print_cost:
            headers.append(u'Нэгж Дүн')
            headers.append(u'Нийт Дүн')

        datas = self.get_move_product_line(ids)
        if not datas:
            return ''
        res = {'header': headers, 'data':datas}
        return res

    def do_print_picking(self):
        html = ''
        counter = 1
        line_ids = self.env['stock.picking'].search([('id','in',self.ids)])
        first_picking = line_ids[0]

        for item in line_ids:
            item.write({'printed': True, 'printed_count': item.printed_count+1})

            template = False
            model_id = self.env['ir.model'].sudo().search([('model','=','stock.picking')], limit=1)
            if item.picking_type_id.code == 'outgoing':
                template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','stock_picking_outgoing')], limit=1)
            elif item.picking_type_id.code == 'incoming':
                template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','stock_picking_outgoing')], limit=1)
            elif item.picking_type_id.code == 'internal':
                template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','stock_picking_outgoing')], limit=1)
            
            if template:
                pttrn_name='<th '
                template_html = template.sudo().get_template_data_html(item.id)
                if template_html:
                    template_html = template_html.replace(pttrn_name, '<th style="font-weight: normal;" ')

                pttrn_name = 'border: 1px solid #dddddd;'
                if template_html:
                    template_html = template_html.replace(pttrn_name, 'border: 1px solid #777777;')
                    if item.state in ['done','assigned']:
                        back_html = ''
                    else:
                        back_html = u"""
    <div id="background" style="
    position:absolute;
    z-index:0;
    background:white;
    display:block;
    min-height:100%; 
    min-width:100%;
   ">
  <p id="bg-text" style="
    color:lightgrey;
    font-size:160px;
    transform:rotate(300deg);
    -webkit-transform:rotate(300deg);">DRAFT</p>
    </div>
"""
                    html += back_html+u'<div class="break_page" style="z-index: 1; position:absolute;">'+template_html+'</div>'
                    first_picking = item
                    # html += u'<div class="break_page">'+template_html+'</div>'
                    counter+=1

            else:
                raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))
        return template.sudo().print_template_html(html)

    def get_sign_doned_user(self, ids):
        report_id = self.browse(ids)
        image_str = '';
        if report_id.doned_user_id.digital_signature:
            image_buf = (report_id.doned_user_id.digital_signature).decode('utf-8')
            image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />'%(image_buf)
        return image_str

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    count_picking_incoming = fields.Integer(compute='_compute_picking_count_imcoming')
    last_expense_out = fields.Boolean(string='Сүүлд зарлагадсан огноог хэвлэх', default=False)
    with_print_cost = fields.Boolean(string='Өртөгтэй хэвлэх', default=False)
    with_print_location = fields.Boolean(string='Байршилтай Хэвлэх', default=False)
    with_print_on_hand = fields.Boolean(string='Үлдэгдэлтэй Хэвлэх', default=False)
    view_from_loc_on_hand = fields.Boolean(string='Үлдэгдэл харуулах', default=False)
    view_from_loc_only_on_hand = fields.Boolean(string='Үлдэгдэлтэй Барааг харуулах Товч', default=False)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|','|', ('name', operator, name), ('warehouse_id.name', operator, name), ('warehouse_id.code', operator, name)]
        picking_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(picking_ids).with_user(name_get_uid))

    def _compute_picking_count_imcoming(self):
        picking_obj = self.env['stock.picking']
        for item in self:
            cnt = 0
            if item.code=='internal':
                query = """select count(distinct sp.id) from stock_picking sp
left join stock_move sm on (sp.id=sm.picking_id and sm.state not in ('done','cancel'))
left join stock_move_line sml on (sp.id=sml.picking_id and sml.state not in ('done','cancel') )
left join stock_picking_type spt on (spt.id=sp.picking_type_id)
left join stock_location sl on (sl.id=sp.location_id or sp.location_dest_id=sl.id 
or sm.location_dest_id=sl.id or sm.location_id=sl.id or sml.location_dest_id=sl.id or sml.location_id=sl.id)
where  sl.set_warehouse_id={0} and spt.code='internal' and sp.picking_type_id!={1} and sp.state not in ('done','cancel')

    """.format(item.warehouse_id.id, item.id)
                # print ('query2 ',query)
                self.env.cr.execute(query)
                # so_ids = 
                result = self.env.cr.fetchone()
                cnt = result[0] if result else 0
                
            item.count_picking_incoming = cnt
    
    
    
    def get_action_incoming_transfer_picking_view(self):
        picking_obj = self.env['stock.picking']
        context = dict(self._context)
        context['create']= False
        context['search_default_not_done']= '1'
        query = """select sp.id from stock_picking sp
left join stock_move sm on (sp.id=sm.picking_id and sm.state not in ('done','cancel'))
left join stock_move_line sml on (sp.id=sml.picking_id and sml.state not in ('done','cancel') )
left join stock_picking_type spt on (spt.id=sp.picking_type_id)
left join stock_location sl on (sl.id=sp.location_id or sp.location_dest_id=sl.id 
or sm.location_dest_id=sl.id or sm.location_id=sl.id or sml.location_dest_id=sl.id or sml.location_id=sl.id)
where  sl.set_warehouse_id={0} and spt.code='internal' and sp.picking_type_id!={1} and sp.state not in ('done','cancel')
    """.format(self.warehouse_id.id, self.id)
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        pick_ids = [x[0] for x in result]
        print ('result',result)
        tree_view_id = self.env.ref('stock.vpicktree').id
        form_view_id = self.env.ref('stock.view_picking_form').id
        
        action = {
                'name': self.warehouse_id.name +u': Ирж Буй Шилжүүлэг',
                'view_type': 'form',
                'view_mode': 'tree',
                'res_model': 'stock.picking',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_id': tree_view_id,
                'domain': [('id','in',pick_ids)],
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current'
            }
        return action

class stock_return_picking(models.TransientModel):
    _inherit = "stock.return.picking"

    return_desc = fields.Char('Буцаалтын тайлбар')

    
    def _create_returns(self):
        new_picking_id, pick_type_id = super(stock_return_picking, self)._create_returns()
        if new_picking_id and self.return_desc:
            pick_id = self.env['stock.picking'].browse(new_picking_id)
            pick_id.origin = str(pick_id.origin)+u' '+self.return_desc
        return new_picking_id, pick_type_id 
        

