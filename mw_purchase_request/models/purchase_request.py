
# -*- coding: utf-8 -*-
from datetime import date, datetime,timedelta

import odoo
from odoo import SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import odoo.addons.decimal_precision as dp

class purchase_request(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase request'
    _inherit = ['mail.thread']
    _order = 'name desc'

    @api.model
    def create(self, val):
        res  =  super(purchase_request,self).create(val)
        for item in res:
            if item.flow_id:
                search_domain = [('flow_id','=',item.flow_id.id)]
                re_flow =  self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
                item.flow_line_id = re_flow
        return res

    @api.model
    def default_get(self, field_list):
        result = super(purchase_request, self).default_get(field_list)
        if 'employee_id' in field_list:
            result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1).id
        return result

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = []
        search_domain.append(('model_id.model','=','purchase.request'))
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    name = fields.Char('Хүсэлтийн Дугаар',readonly=True, copy=False)
    company_id = fields.Many2one('res.company','Компани', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('res.branch','Салбар', default=lambda self: self.env.user.branch_id)

    date = fields.Date('Хэрэгцээт Огноо', required=True, default=fields.Date.context_today)
    approved_date = fields.Datetime(string=u'Батлагдсан огноо')

    employee_id = fields.Many2one('hr.employee','Ажилтан')
    department_id = fields.Many2one('hr.department','Хэлтэс', compute='_compute_department', store=True, readonly=True)
    line_ids = fields.One2many('purchase.request.line','request_id','Product request line', copy=True)
    desc = fields.Text('Тайлбар')
    desc_done = fields.Char('Батлагчийн тайлбар')
    purchase_ids = fields.Many2many('purchase.order','purchase_order_purchase_request_rel','pur_id','rec_id','Худалдан Авалт')
    refund_ids = fields.One2many('request.refund.history','request_id','Refund')
    internal_ids = fields.Many2many('stock.picking','purchase_request_stock_rel','stock_id','rec_id','Баримтууд')

    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', track_visibility='onchange',
        default=_get_default_flow_id,
         copy=True, required=True, domain="[('model_id.model', '=', 'purchase.request')]")

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', track_visibility='onchange', index=True,
        default=_get_dynamic_flow_line_id,
         copy=False, domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'purchase.request')]")


    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)

    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
    next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
    flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах')
    categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
    visible_categ_ids = fields.Many2many('product.category', compute='_compute_visible_categ_ids', string='Харагдах ангилал')
    product_id = fields.Many2one('product.product',related='line_ids.product_id')
    purchase_order_ids = fields.One2many('purchase.order', string='Худалдан авалтын захиулгууд', compute='compute_purchase_order')
    history_ids = fields.One2many('purchase.flow.history', 'request_id', 'Түүхүүд')
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True)
    is_view_expense = fields.Boolean(compute='_compute_is_view_expense')
    expense_picking_id = fields.Many2one('stock.picking', string='Зарлагын хөдөлгөөн', copy=False)

    warning_messages = fields.Html('Анхааруулага', compute='_compute_wc_messages')

    confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True)
    priority = fields.Selection([('need1','1. НЭН ЯАРАЛТАЙ'),('need2','2. ЯАРАЛТАЙ'),('need3','3. ШААРДЛАГАТАЙ')], string='Зэрэглэл')

    @api.depends('flow_line_id','flow_id.line_ids')
    def _compute_user_ids(self):
        for item in self:
            temp_users = []
            for w in item.flow_id.line_ids:
                temp = []
                try:
                    temp = w._get_flow_users(item.branch_id, item.sudo().employee_id.department_id, item.sudo().employee_id.user_id).ids
                except:
                    pass
                temp_users+=temp
            item.confirm_user_ids = temp_users

    @api.depends('line_ids.product_id','line_ids.qty')
    def _compute_wc_messages(self):
        for item in self:
            message = []
            product_ids = item.line_ids.mapped('product_id').ids
            if item.id and product_ids and item.branch_id:
                if len(product_ids)>1:
                    p_ids = str(tuple(product_ids))
                elif len(product_ids)==1:
                    p_ids = "("+str(product_ids[0])+")"

                sql_query = """SELECT prl.product_id,pr.date,pr.employee_id,sum(prl.qty) as qty,pr.name
                        FROM purchase_request_line prl
                        left join purchase_request pr on (pr.id=prl.request_id)
                        left join product_product pp on (prl.product_id=pp.id)
                        left join product_template pt on (pt.id=pp.product_tmpl_id)
                        WHERE prl.product_id in %s and pr.id!=%s and pr.state_type='done' and pr.branch_id=%s
                        and pr.company_id=%s and pr.date<='%s' and pt.type!='service'
                        group by 1,2,3,5
                """% (p_ids,item.id, item.branch_id.id, item.company_id.id, item.date)
                self.env.cr.execute(sql_query)
                query_result = self.env.cr.dictfetchall()

                for qr in query_result:
                    val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"""%(self.env['product.product'].browse(qr['product_id']).display_name,qr['date'],self.env['hr.employee'].browse(qr['employee_id']).display_name,qr['qty'],qr['name'])
                    message.append(val)

            if message==[]:
                message = False
            else:
                message = u'<table style="width: 100%;"><tr><td colspan="4" style="text-align: center;">ӨМНӨ ЗАХИАЛГА ХИЙСЭН</td></tr><tr style="width: 40%;"><td>Бараа</td><td style="width: 15%;">Огноо</td><td style="width: 20%;">Ажилтан</td><td style="width: 10%;">Тоо Хэмжээ</td><td style="width: 15%;">Дугаар</td></tr>'+u''.join(message)+u'</table>'
            item.warning_messages = message

    @api.depends('employee_id')
    def _compute_department(self):
        for item in self:
            item.department_id = item.sudo().employee_id.department_id.id

    @api.depends('line_ids.diff_qty')
    def _compute_is_view_expense(self):
        for item in self:
            if item.line_ids.filtered(lambda r: r.diff_qty>0):
                item.is_view_expense = True
            else:
                item.is_view_expense = False

    @api.depends('flow_id.categ_ids')
    def _compute_visible_categ_ids(self):
        for item in self:
            cat_ids = self.env['product.category'].search([('id','child_of',item.flow_id.categ_ids.ids)])
            item.visible_categ_ids = cat_ids.ids
            if not cat_ids:
                item.visible_categ_ids = self.env['product.category'].search([]).ids

    @api.depends('flow_line_id.stage_id')
    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    @api.depends('flow_line_id.is_not_edit')
    def _compute_is_not_edit(self):
        for item in self:
            item.is_not_edit = item.flow_line_id.is_not_edit

    @api.depends('flow_line_id')
    def _compute_state_type(self):
        for item in self:
            item.state_type = item.flow_line_id.state_type
            # item.is_cancel = True if item.flow_line_id.state_type=='cancel' else False
    @api.depends('flow_line_next_id.state_type')
    def _compute_next_state_type(self):
        for item in self:
            item.next_state_type = item.flow_line_next_id.state_type


    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id','=',self.flow_id.id))
        search_domain.append(('flow_id.model_id.model','=','purchase.request'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id



    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find()
        else:
            self.flow_line_id = False

    def action_next_stage(self):
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.branch_id, self.sudo().employee_id.department_id, self.sudo().employee_id.user_id):
                # for item in self.line_ids:
                #     if not item.product_id and self.state_type!='draft':
                #         raise UserError(u'%s мөр дээр бараа үүсгэж сонгож өгнө үү'%(item.desc))
                self.flow_line_id = next_flow_line_id
                # History uusgeh
                self.env['purchase.flow.history'].create_history(next_flow_line_id, self)
                self.send_chat_employee(self.sudo().employee_id.user_id.partner_id)
                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(self.branch_id, self.sudo().employee_id.sudo().department_id, self.sudo().employee_id.user_id)
                    if send_users:
                        self.send_chat_next_users(send_users.mapped('partner_id'))
                if self.flow_line_id.state_type!='done':
                    self.update_available_qty()
                    self.product_warning()
            else:
                con_user = next_flow_line_id._get_flow_users(self.branch_id, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(con_user.mapped('display_name'))
                raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
            if self.flow_line_id.state_type=='done':
                self.approved_date = datetime.now()

    def action_back_stage(self):
        back_flow_line_id = self.flow_line_id._get_back_flow_line()
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if back_flow_line_id and next_flow_line_id:
            if next_flow_line_id._get_check_ok_flow(self.branch_id, self.sudo().employee_id.department_id, self.sudo().employee_id.user_id):
            # if back_flow_line_id._get_check_ok_flow(self.branch_id, self.employee_id.sudo().department_id, self.employee_id.user_id):
                self.flow_line_id = back_flow_line_id
                # History uusgeh
                self.env['purchase.flow.history'].create_history(back_flow_line_id, self)
                self.send_chat_employee(self.sudo().employee_id.user_id.partner_id)
            else:
                raise UserError(_('You are not back user'))

    def action_cancel_stage(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(self.branch_id, self.sudo().employee_id.sudo().department_id, self.sudo().employee_id.user_id):
            self.flow_line_id = flow_line_id
            # History uusgeh
            self.env['purchase.flow.history'].create_history(flow_line_id, self)
            self.send_chat_employee(self.sudo().employee_id.user_id.partner_id)
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if self.line_ids.filtered(lambda r: r.po_line_ids):
        # if self.line_ids.filtered(lambda r: r.purchase_order_line_id):
            raise UserError(u'Худалдан авалтын захиалга үүссэн тул буцаах боломжгүй')

        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            # History uusgeh
            self.env['purchase.flow.history'].create_history(flow_line_id, self)
        else:
            raise UserError(_('You are not draft user'))

    @api.depends('line_ids.po_line_ids')
    def compute_purchase_order(self):
        for item in self:
            item.purchase_order_ids = item.line_ids.mapped('po_line_ids.order_id')

    # action_to_print
    def action_to_print(self):
        model_id = self.env['ir.model'].search([('model','=','purchase.request')], limit=1)
        template = self.env['pdf.template.generator'].search([('model_id','=',model_id.id),('name','=','purchase_request')], limit=1)
        # self.print_date = datetime.now()
        if template:
            res = template.print_template(self.id)
            return res
        else:
            raise UserError(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!')

    # def action_view_stock(self):
    #     invoice_ids = self.mapped('internal_ids')
    #     imd = self.env['ir.model.data']
    #     action = imd.xmlid_to_object('stock.vpicktree')
    #     form_view_id = imd.xmlid_to_res_id('stock.view_picking_form')

    #     return {
    #         'name': action.name,
    #         'type': 'ir.actions.act_window',
    #         'views': [(form_view_id, 'form')],
    #         'target': 'current',
    #         'res_id': invoice_ids.ids[0],
    #         'res_model': 'stock.picking',
    #     }

    # def action_view_purchase(self):
    #     invoice_ids = self.mapped('purchase_ids')
    #     imd = self.env['ir.model.data']
    #     action = imd.xmlid_to_object('purchase.purchase_order_tree')
    #     form_view_id = imd.xmlid_to_res_id('purchase.purchase_order_form')

    #     return {
    #         'name': action.name,
    #         'type': 'ir.actions.act_window',
    #         'views': [(form_view_id, 'form')],
    #         'target': 'current',
    #         'res_id': invoice_ids.ids[0],
    #         'res_model': 'purchase.order',
    #     }



    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or '/'
        return super(purchase_request, self).create(vals)

    def update_available_qty(self):
        quant_obj = self.env['stock.quant']
        for item in self.line_ids:
            quant_ids = []
            if item.request_id.warehouse_id:
                quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.set_warehouse_id','=',item.request_id.warehouse_id.id),('location_id.usage','=','internal')])
            else:
                quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.usage','=','internal')])
            item.available_qty = sum(quant_ids.mapped('quantity'))

    def unlink(self):
        for item in self:
            if item.state_type!='draft':
                raise UserError(u'Ноорог биш баримтыг устгахгүй !!!')

        return super(purchase_request, self).unlink()

    def send_chat_next_users(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('mw_purchase_request', 'action_purchase_request_tree_view')[1]
        html = u'<b>Худалдан авалтын хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.sudo().employee_id.name)
        html += u"""<b><a target="_blank" href=%s/web#id=%s&form&model=purchase.request&action=%s>%s</a></b>, дугаартай Худалдан авалтын хүсэлтийг батлана уу"""% (base_url,self.id,action_id,self.name)
        self.flow_line_id.send_chat(html, partner_ids)

    def send_chat_employee(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('mw_purchase_request', 'action_purchase_request_tree_view')[1]
        html = u'<b>Худалдан авалтын хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.sudo().employee_id.name)
        html += u"""<b><a target="_blank"  href=%s/web#id=%s&form&model=purchase.request&action=%s>%s</a></b>, дугаартай Худалдан авалтын хүсэлт <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,self.name,state)

        self.flow_line_id.send_chat(html, self.get_chat_employee(partner_ids))



    def get_user_signature(self,ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
        history_obj = self.env['purchase.flow.history']
        for item in print_flow_line_ids:
            his_id = history_obj.search([('flow_line_id','=',item.id),('request_id','=',report_id.id)], limit=1)
            image_str = '________________________'
            if his_id.user_id.digital_signature:
                image_buf = (his_id.user_id.digital_signature).decode('utf-8')
                image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />'%(image_buf)
            user_str =  '________________________'
            if his_id.user_id:
                user_str = his_id.user_id.name
            html += u'<tr><td><p>%s</p></td><td>%s</td><td> <p>/%s/</p></td></tr>'%(item.name,image_str,user_str)
        html += '</table>'
        return html

    def get_line_ids(self, ids):
        headers = [
        u'Бараа',
        u'Тайлбар',
        u'Хэмжих нэгж',
        u'Тоо',
        u'Үлдэгдэл',
        ]

        datas = []
        report_id = self.browse(ids)

        lines = report_id.line_ids

        sum1 = 0
        sum2 = 0
        sum3 = 0
        nbr = 1
        for line in lines:
            sum1 += line.qty
            pp_code = u'['+line.product_id.product_code+']' if line.product_id.product_code else u''
            def_code = u'['+line.product_id.default_code+']' if line.product_id.default_code else u''
            p_name = line.product_id.name if line.product_id else u''
            uom_name = line.uom_id.name if line.product_id else u''
            temp = [
            u'<p style="text-align: left;">'+def_code+pp_code+u' '+p_name+u'</p>',
            u'<p style="text-align: center;">'+line.name+u'</p>',
            u'<p style="text-align: center;">'+uom_name+u'</p>',
            "{0:,.0f}".format(line.qty) or '',
            "{0:,.0f}".format(line.available_qty) or '',
            ]
            nbr += 1
            datas.append(temp)
        temp = [
        u'',
        u'<p style="text-align: center; font-weight: bold; ">Нийт дүн</p>',
        u'',
        "{0:,.0f}".format(sum1) or '',
        ]
        if not datas:
            return False
        datas.append(temp)
        res = {'header': headers, 'data':datas}
        return res

    def create_expense_picking(self):
        if self.expense_picking_id:
            raise UserError(u'Зарлагын хөдөлгөөн байна')
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        if not self.warehouse_id:
            raise UserError(u'Агуулахаа сонгоно уу')
        location_id = self.warehouse_id.lot_stock_id
        location_dest_id = self.env['stock.location'].search([('usage','=','customer')], limit=1)
        name = self.desc or ''
        picking_id = picking_obj.create({
                'picking_type_id': self.warehouse_id.out_type_id.id,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'scheduled_date': self.date,
                'move_lines': [],
                'origin': self.name + name
            })
        move_lines = []
        for item in self.line_ids.filtered(lambda r: r.diff_qty>0):
            move ={
                'name': name+u' '+item.product_id.name,
                'product_id': item.product_id.id,
                'product_uom': item.product_id.uom_id.id,
                'product_uom_qty': item.qty,
                'picking_type_id': self.warehouse_id.out_type_id.id,
                'location_id': location_id.id,
                'location_dest_id': location_dest_id.id,
                'date_expected': self.date,
                'picking_id': picking_id.id,
                }
            move_obj.create(move)
        self.expense_picking_id = picking_id.id

    def product_warning(self):

        warning = {}
        title = False
        message = False

        if self.line_ids:
            warning['title'] = 'eee'
            warning['message'] = message
        for item in self.line_ids:
            message='<html>asdfasdfasdf</html>'
        warning['message'] = message
        if message:
            return {'warning': warning}
        # if product_info.purchase_line_warn != 'no-message':
        #     title = _("Warning for %s") % product_info.name
        #     message = product_info.purchase_line_warn_msg
        #     warning['title'] = title
        #     warning['message'] = message
        #     if product_info.purchase_line_warn == 'block':
        #         self.product_id = False
        #     return {'warning': warning}
        return {}

    def get_chat_employee(self, partner_ids):
        return partner_ids

    def get_company_logo(self, ids):
        report_id = self.browse(ids)
        image_buf = report_id.company_id.logo_web.decode('utf-8')
        image_str = '';
        if len(image_buf)>10:
            image_str = '<img alt="Embedded Image" width="400" src="data:image/png;base64,%s" />'%(image_buf)
        return image_str

class purchase_request_line(models.Model):
    _name = 'purchase.request.line'
    _description = 'Purchase request line'
    _inherit = ['mail.thread']

    name = fields.Char('Name', compute='_compute_name')
    product_id = fields.Many2one('product.product','Бараа')
    desc = fields.Char('Тайлбар Зориулалт')

    uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', readonly=True)
    qty = fields.Float('Тоо Хэмжээ', default=1)
    po_qty = fields.Float('PO Үүссэн Тоо', default=0, copy=False, compute='_compute_po_diff_qty', store=True)
    po_diff_qty = fields.Float('PO Үүсгэх Тоо', compute='_compute_po_diff_qty', store=True, copy=False)
    request_id = fields.Many2one('purchase.request', 'Хүсэлт Баримт', ondelete='cascade')
    price_unit = fields.Float('Нэгж Үнэ')
    company_id = fields.Many2one('res.company','Company', default=lambda self: self.env.user.company_id)
    categ_id = fields.Many2one('product.category', compute='_compute_categ_id', string='Ангилал', store=True)
    purchase_order_id = fields.Many2one('purchase.order', related='purchase_order_line_id.order_id', string='PO', readonly=True, copy=False, store=True)
    purchase_order_line_id = fields.Many2one('purchase.order.line', string='Худалдан авалтын захиалгын мөр', readonly=True, copy=False)

    purchase_order_ids = fields.Many2many('purchase.order', compute='_compute_purchase_order_ids', string='POs')

    po_line_ids = fields.Many2many('purchase.order.line', 'purchase_order_line_purchase_request_line_rel', 'pr_line_id', 'po_line_id', string='PO lines', copy=False)

    available_qty = fields.Float('Үлдэгдэл', readonly=True, copy=False)
    is_product_edit = fields.Boolean(string='Барааг засаж оруулах', compute='_compute_is_product_edit')
    user_id = fields.Many2one('res.users', string='Хангамжийн ажилтан')
    is_expense = fields.Boolean(string='Зарлага болох эсэх')
    diff_qty = fields.Float('Зөрүү', readonly=True, compute='_compute_diff_qty')
    internal_stock_move_id = fields.Many2one('stock.move', string='Дотоод хөдөлгөөн', readonly=True)
    internal_picking_id = fields.Many2one('stock.picking',related='internal_stock_move_id.picking_id', string='Дотоод хөдөлгөөн баримт', readonly=True)

    branch_id = fields.Many2one('res.branch', related='request_id.branch_id', readonly=True, store=True)
    employee_id = fields.Many2one('hr.employee', related='request_id.employee_id', readonly=True, store=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', related='request_id.stage_id', readonly=True, store=True)
    date = fields.Date(related='request_id.date', readonly=True, store=True)
    desc_req = fields.Text(related='request_id.desc',string='Үндсэн Тайлбар', readonly=True, )
    department_id = fields.Many2one('hr.department', related='request_id.department_id', readonly=True, store=True)
    is_over = fields.Boolean('Цаашид авахгүй', default=False, copy=False, track_visibility=True)
    priority = fields.Selection(related='request_id.priority', store=True, readonly=True)

    flow_id = fields.Many2one('dynamic.flow', related='request_id.flow_id', readonly=True, store=True)

    remained_qty_new = fields.Float(compute='_compute_remain_qty', string="PO үүсэх тооноос үлдсэн", store=True, readonly=True)
    outstanding_qty_new = fields.Float(compute='_compute_remain_qty', string="Хүлээн авахад үлдсэн", store=True, readonly=True)
    po_date_planned_new = fields.Char(compute='_compute_remain_qty', string="Ирэх огноо", readonly=True)
    pol_received_qty_new = fields.Float(compute='_compute_remain_qty', string="Хүлээн авсан", store=True, readonly=True)

    def write(self, values):
        if 'qty' in values:
            for line in self:
                if line.request_id.state_type != 'draft':
                    line.request_id.message_post_with_view('mw_purchase_request.track_po_line_template',
                                                         values={'line': line, 'qty': values['qty']},
                                                         subtype_id=self.env.ref('mail.mt_note').id)
        return super(purchase_request_line, self).write(values)

    def get_po_line(self):
        return self.po_line_ids

    def update_all_line_remain_qty(self):
        for item in self.env['purchase.request.line'].search([]):
            item._compute_po_diff_qty()
            item._compute_remain_qty()

    @api.depends('qty','po_line_ids.product_qty','po_line_ids.qty_received','po_qty')
    def _compute_remain_qty(self):
        for item in self:
            po_line_ids = item.get_po_line()
            po_qty = item.po_qty
            print(item)
            po_receive_qty = sum(po_line_ids.mapped('qty_received'))
            ttd = item.qty - po_qty
            if ttd<0:
                ttd = 0
            item.remained_qty_new = po_qty - po_receive_qty
            item.pol_received_qty_new = po_receive_qty
            item.outstanding_qty_new = ttd
            item.po_date_planned_new = ', '.join([str(x.date_planned) for x in  po_line_ids])


    @api.depends()
    def _compute_purchase_order_ids(self):
        for item in self:
            item.purchase_order_ids = item.po_line_ids.mapped('order_id')

    @api.depends('po_line_ids.product_qty','qty','po_line_ids.state')
    def _compute_po_diff_qty(self):
        for item in self:
            po_created_qty = item.qty - sum(item.po_line_ids.filtered(lambda r: r.state!='cancel').mapped('product_qty'))
            # sain bodoj bgad iim bolgoh heregtei yum
            # po_qty = sum(item.po_line_ids.filtered(lambda r: r.state!='cancel').mapped('product_qty'))
            # print ("len(item.mapped('po_line_ids'))<len(item.mapped('po_line_ids.pr_line_many_ids'))",len(item.mapped('po_line_ids')),'-------',len(item.mapped('po_line_ids.pr_line_many_ids')))
            # po_created_qty = 0
            # if po_qty>item.qty:
            #     po_created_qty = item.qty - po_qty
            # elif len(item.mapped('po_line_ids'))<len(item.mapped('po_line_ids.pr_line_many_ids')):
            #     po_created_qty = item.qty - po_qty
            item.po_qty = sum(item.po_line_ids.filtered(lambda r: r.state!='cancel').mapped('product_qty'))
            item.po_diff_qty = po_created_qty if po_created_qty>0 else 0
            # item.po_qty = item.po_diff_qty

    @api.onchange('po_diff_qty', 'qty')
    def _onchange_default_compute(self):
        self.po_qty = self.po_diff_qty

    @api.depends('available_qty','qty')
    def _compute_diff_qty(self):
        for item in self:
            if item.available_qty > item.qty:
                item.diff_qty = item.available_qty - item.qty
            else:
                item.diff_qty = 0


    def unlink(self):
        for item in self:
            if item.request_id.state_type != 'draft':
                item.request_id.message_post_with_view('mw_purchase_request.track_po_line_template_delete',
                                                        values={'line': item},
                                                        subtype_id=self.env.ref('mail.mt_note').id)
            if item.po_line_ids:
                if 'cancel' not in item.po_line_ids.mapped('state'):
                    raise UserError(u'ХУДАЛДАН АВАЛТ үүссэн хүсэлтийн мөрийн устгахгүй !!!')

        return super(purchase_request_line, self).unlink()

    @api.depends('request_id.state_type','product_id')
    def _compute_is_product_edit(self):
        for item in self:
            if item.request_id.state_type=='draft':
                item.is_product_edit = True
            elif item.request_id.state_type in ['done','cancel']:
                item.is_product_edit = False
            else:
                item.is_product_edit = True


    # @api.depends('product_id','request_id.warehouse_id')
    # def _compute_available_qty(self):
    #     for item in self:
    #         item.available_qty = self.env['stock.quant']._get_available_quantity(item.product_id, item.request_id.warehouse_id.lot_stock_id, lot_id=False, package_id=False, owner_id=False, strict=True)


    @api.depends('product_id','request_id')
    def _compute_name(self):
        for item in self:
            if item.product_id:
                item.name = item.request_id.name+u' | '+item.product_id.name+u' | '+(item.desc or '')
            else:
                item.name = item.request_id.name+' | '+item.desc

    @api.depends('product_id')
    def _compute_categ_id(self):
        for item in self:
            item.categ_id = item.product_id.categ_id

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.desc = self.product_id.name
        else:
            self.desc = False

class purchase_request_line_po_create(models.TransientModel):
    _name='purchase.request.line.po.create'
    _description = 'Purchase Order Create'

    @api.model
    def _default_line_ids(self):
        obj = self.env['purchase.request.line'].browse(self._context['active_ids'])

        line_ids = []

        for item in obj:
            line_ids.append((0, 0, {'pr_line_id': item.id, 'product_id': item.product_id.id, 'qty': item.qty, 'po_qty': item.po_qty}))

        return line_ids

    partner_id = fields.Many2one('res.partner', string='Харилцагч')
    partner_ids = fields.Many2many('res.partner','purchase_request_line_create_res_partner_rel','pur_id','par_id', 'Харилцагчид')
    is_comparison = fields.Boolean('Харьцуулалттай эсэх', default=False)
    is_internal = fields.Boolean('Дотоод хөдөлгөөн үүсгэх', default=False)
    is_po_qty_edit = fields.Boolean('Худалдан авалтын тоог өөрчлөх', default=False)
    date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Оноох Хангамжийн Ажилтан')
    flow_id = fields.Many2one('dynamic.flow', string='Худалдан авалтын урсгал тохиргоо', domain="[('model_id.model', '=', 'purchase.order')]")

    warehouse_id = fields.Many2one('stock.warehouse', string='Худалдан авах агуулах')
    to_warehouse_id = fields.Many2one('stock.warehouse', string='Дотоод хөдөлгөөнөөр явуулах')
    transport_track_id = fields.Many2one('transport.track','Тээвэрлэх машин')
    picking_date = fields.Datetime(string='Дотоод хөдөлгөөн үүсгэх огноо', default=fields.Datetime.now)
    line_ids = fields.One2many('purchase.request.line.po.create.line', 'parent_id', 'Мөр', default=_default_line_ids)
    purchase_sub_id = fields.Many2one('purchase.order', 'Нэмэгдэх PO')
    is_sub_po = fields.Boolean('Худалдан авалтын захиалганд нэгтгэх', default=False)

    def get_pr_po_line(self, product_id, re_lines, date, po_id, uom_id):
        return  {
                    'product_id': product_id.id,
                    'name': '%s'%(', '.join(set(re_lines.mapped('name')))),
                    'date_planned': date,
                    'product_qty': sum(re_lines.mapped('po_qty')) if self.is_po_qty_edit else sum(re_lines.mapped('qty')),
                    'price_unit': 1,
                    'product_uom': uom_id.id,
                    'order_id': po_id.id,
                    'pr_line_many_ids': [(6,0,re_lines.ids)],
        }

    def action_done(self):
        obj = self.env['purchase.request.line'].browse(self._context['active_ids'])
        
        if obj.filtered(lambda r: r.request_id.state_type!='done'):
            raise ValidationError(_('Not done request line in selected!'))

        if obj.filtered(lambda r: r.po_line_ids and r.po_diff_qty<=0):
            raise ValidationError(_('Purchase order created!'))

        if obj.filtered(lambda r: not r.product_id):
            raise ValidationError('Бараа сонгогдоогүй Хүсэлт байна Бараагаа үүсгэнэ үү')

        desc = obj.mapped('request_id.name')+obj.filtered(lambda r: r.request_id.desc!=False).mapped('request_id.desc')+obj.filtered(lambda r: r.request_id.desc_done!=False).mapped('request_id.desc_done')
        user_ids = obj.mapped('user_id')

        if not self.is_sub_po:
            search_domain = [('flow_id','=',self.flow_id.id)]
            flow_line_id = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id

            vals = {
                'date_order': self.date,
                'flow_id': self.flow_id.id,
                'picking_type_id': self.warehouse_id.in_type_id.id,
                'date_planned': self.date,
                'origin': ','.join(desc) if len(desc)>0 else '',
                'flow_line_id': flow_line_id,
                'state': 'draft',
            }
            if user_ids:
                vals['user_id'] = user_ids[0].id
            if self.is_comparison:
                vals['partner_id'] = self.partner_ids[0].id
                vals['is_comparison'] = True
            else:
                vals['partner_id'] = self.partner_id.id
            po_id = self.env['purchase.order'].create(vals)
        else:
            po_id = self.purchase_sub_id

        res = []
        linevals = []
        product_ids = obj.mapped('product_id')

        for item in product_ids:
            re_lines = obj.filtered(lambda r: r.product_id.id==item.id)
            if item.type=='service':
                for prline in re_lines:
                    po_line_val = {
                        'product_id': item.id,
                        'name': '%s'%(prline.name),
                        'date_planned': self.date,
                        'product_qty': prline.po_qty if self.is_po_qty_edit else prline.qty,
                        'price_unit': 1,
                        'product_uom': item.uom_id.id,
                        'order_id': po_id.id,
                        'pr_line_many_ids': [(6,0,[prline.id])],
                    }
                    po_line_id = self.env['purchase.order.line'].create(po_line_val)
            else:
                found_po_line_id = False
                if self.is_sub_po:
                    found_po_line_id = po_id.order_line.filtered(lambda r: r.product_id.id==item.id)
                    if found_po_line_id:
                        if len(found_po_line_id)>1:
                            found_po_line_id = found_po_line_id[0]
                        add_prline_qty = sum(re_lines.mapped('po_qty')) if self.is_po_qty_edit else sum(re_lines.mapped('qty'))
                        add_prline_qty += found_po_line_id.product_qty
                        pr_line_many_ids = [(6,0,found_po_line_id.pr_line_many_ids.ids+re_lines.ids)]
                        found_po_line_id.write({
                            'product_qty': add_prline_qty,
                            'pr_line_many_ids': pr_line_many_ids
                            })
                    else:
                        po_line_vals = self.get_pr_po_line(item, re_lines, self.date, po_id, item.uom_id)
                        po_line_id = self.env['purchase.order.line'].create(po_line_vals)
                else:
                    po_line_vals = self.get_pr_po_line(item, re_lines, self.date, po_id, item.uom_id)
                    po_line_id = self.env['purchase.order.line'].create(po_line_vals)

        for item in po_id.order_line:
            if item.product_id.type!='service':
                item._onchange_quantity()
        try:
            po_id.onchange_taxes_id()
        except Exception as e:
            _logger.info('---------------', e)


        # chat ilgeeh
        for item in po_id.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
            po_id.send_chat_employee(item)

        if self.is_comparison:
            po_id.onchange_is_comparison()
            for item in self.partner_ids:
                con = dict(self._context)
                con['active_id'] = po_id.id
                self.env['purchase.comparison.create'].create({'partner_id': item.id}).with_context(con).action_done()

        if self.is_internal:
            picking_obj = self.env['stock.picking']
            move_obj = self.env['stock.move']
            if self.to_warehouse_id:
                int_wh_ids = self.to_warehouse_id
            else:
                int_wh_ids = obj.filtered(lambda r: r.request_id.warehouse_id.id != self.warehouse_id.id).mapped('request_id.warehouse_id')
            for item in int_wh_ids:
                if not self.is_sub_po:
                    warehouse_id = self.warehouse_id
                else:
                    warehouse_id = po_id.picking_type_id.warehouse_id

                location_id = warehouse_id.lot_stock_id
                picking_type_id = warehouse_id.int_type_id
                location_dest_id = item.lot_stock_id

                if self.to_warehouse_id:
                    req_ids = obj
                else:
                    req_ids = obj.filtered(lambda r: r.request_id.warehouse_id.id == item.id)

                desc = [x.name+u' '+x.sudo().employee_id.name+u' '+(x.desc or '') for x in req_ids.mapped('request_id')]
                name = ','.join(desc)

                picking_id = picking_obj.create({
                        'picking_type_id': picking_type_id.id,
                        'location_id': location_id.id,
                        'location_dest_id': location_dest_id.id,
                        'scheduled_date': self.picking_date,
                        'move_lines': [],
                        'origin': name,
                        'transport_track_id': self.transport_track_id.id if self.transport_track_id else False
                    })
                move_lines = []
                for line in req_ids:
                    move ={
                        'name': name+u' '+line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.po_qty if self.is_po_qty_edit else line.qty,
                        # 'product_uom_qty': line.qty,
                        'picking_type_id': picking_type_id.id,
                        'location_id': location_id.id,
                        'location_dest_id': location_dest_id.id,
                        'date_expected': self.picking_date,
                        'picking_id': picking_id.id,
                        }
                    stock_move_id = move_obj.create(move)
                    stock_move_id._action_confirm()
                    line.internal_stock_move_id = stock_move_id.id

        return obj

class purchase_request_line_po_create_line(models.TransientModel):
    _name='purchase.request.line.po.create.line'
    _description = 'Purchase Order Create Line'

    parent_id = fields.Many2one('purchase.request.line.po.create', ondelete='cascade', string='Parent')
    pr_line_id = fields.Many2one('purchase.request.line', string='Захиалгын мөр')
    product_id = fields.Many2one('product.product', related='pr_line_id.product_id', readonly=True)
    desc = fields.Char(related='pr_line_id.desc', readonly=True)
    qty = fields.Float(related='pr_line_id.qty', readonly=True)
    po_qty = fields.Float(related='pr_line_id.po_qty')



class purchase_request_line_user_set(models.TransientModel):
    _name='purchase.request.line.user.set'
    _description = 'Purchase Order Create'

    user_id = fields.Many2one('res.users', string='Оноох Хангамжийн Ажилтан', required=True)

    def action_done(self):
        obj = self.env['purchase.request.line'].browse(self._context['active_ids'])

        if obj.filtered(lambda r: r.po_line_ids):
            raise ValidationError(_('Purchase order created!'))

        html = ''
        html = u'<i style="color: red">%s</i> ажилтанд <br/><b>Худалдан авалтын хүсэлт оноогдлоо </b><br/>'%(self.user_id.name)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('mw_purchase_request', 'action_purchase_request_line_tree_view')[1]

        for item in obj:
            item.user_id = self.user_id.id
            html += u"""<b><a target="_blank"  href=%s/web#id=%s&form&model=purchase.request.line&action=%s>%s</a></b>,"""% (base_url,item.id,action_id,item.name)


        self.env['dynamic.flow.line'].send_chat(html,self.user_id.partner_id)

        for item in obj.sudo().mapped('request_id.employee_id.user_id.partner_id'):
            self.env['dynamic.flow.line'].send_chat(html,item)

        # self.env['purchase.request'].send_chat(html,self.user_id.partner_id)

        return True


class request_refund_history(models.Model):
    _name = 'request.refund.history'
    _description = "request refund history"

    company_id = fields.Many2one('res.company','Company',required=True, default=lambda self: self.env.user.company_id)
    refund_user_id = fields.Many2one('res.users','Refund users',required=True)
    refund_desc = fields.Char('Refund desc',required=True)
    refund_date = fields.Date('Refund date',required=True)
    request_id = fields.Many2one('purchase.request','Purchase request', ondelete='cascade')


class purchase_flow_history(models.Model):
    _name = 'purchase.flow.history'
    _description = 'Purchase flow history'
    _order = 'date desc'

    request_id = fields.Many2one('purchase.request','Хүсэлт', ondelete='cascade')
    purchase_id = fields.Many2one('purchase.order','Худалдан авалтын захиалга', ondelete='cascade')
    user_id = fields.Many2one('res.users','Өөрчилсөн Хэрэглэгч')
    date = fields.Datetime('Огноо', default=fields.Datetime.now)
    flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв')

    def create_history(self, flow_line_id, request_id):
        self.env['purchase.flow.history'].create({
            'request_id': request_id.id,
            'user_id': self.env.user.id,
            'date': datetime.now(),
            'flow_line_id': flow_line_id.id
            })

    def create_history_po(self, flow_line_id, purchase_id):
        self.env['purchase.flow.history'].create({
            'purchase_id': purchase_id.id,
            'user_id': self.env.user.id,
            'date': datetime.now(),
            'flow_line_id': flow_line_id.id
            })

