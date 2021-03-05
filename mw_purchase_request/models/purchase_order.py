# -*- coding: utf-8 -*-
from datetime import date, datetime,timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError

class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, val):
        res  =  super(purchase_order,self).create(val)
        for item in res:
            if item.flow_id:
                search_domain = [('flow_id','=',item.flow_id.id)]
                re_flow =  self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
                item.flow_line_id = re_flow
            item.onchange_partner_id()
        return res

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = []
        search_domain.append(('model_id.model','=','purchase.order'))
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв PO', track_visibility='onchange', index=True,
        default=_get_dynamic_flow_line_id, domain="[('id','in',visible_flow_line_ids)]",
         copy=False)

    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', track_visibility='onchange',
        default=_get_default_flow_id,
         copy=True, required=True, domain="[('model_id.model', '=', 'purchase.order')]")
    flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
    flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)
    categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
    is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True)

    @api.depends('flow_id.line_ids', 'flow_id.is_amount', 'amount_total')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                if item.flow_id.is_amount:
                    flow_line_ids = []
                    for fl in item.flow_id.line_ids:
                        if fl.state_type in ['draft','cancel']:
                            flow_line_ids.append(fl.id)
                        elif fl.amount_price_min==0 and fl.amount_price_max==0:
                            flow_line_ids.append(fl.id)
                        elif fl.amount_price_min<=item.amount_total and fl.amount_price_max>=item.amount_total:
                            flow_line_ids.append(fl.id)

                    item.visible_flow_line_ids = flow_line_ids
                else:
                    item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'purchase.order')])
            else:
                item.visible_flow_line_ids = []

    @api.depends('flow_line_id.stage_id')
    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    #------------------------------flow------------------
    @api.depends('flow_line_id')
    def _compute_state_type(self):
        for item in self:
            item.state_type = item.flow_line_id.state_type

    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id','=',self.flow_id.id))

        search_domain.append(('flow_id.model_id.model','=','purchase.order'))
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
            if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                check_next_flow_line_id = next_flow_line_id
                while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:

                    temp_stage = check_next_flow_line_id._get_next_flow_line()
                    if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
                        break
                    check_next_flow_line_id = temp_stage
                next_flow_line_id = check_next_flow_line_id

            if next_flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, False):
                self.check_comparison()
                self.flow_line_id = next_flow_line_id
                if self.flow_line_id.state_type=='done':
                    self.button_confirm()

                # History uusgeh
                self.env['purchase.flow.history'].create_history_po(next_flow_line_id, self)

                # chat ilgeeh
                for item in self.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
                    self.send_chat_employee(item)


                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(self.branch_id, self.user_id.department_id, False)
                    if send_users:
                        self.send_chat_next_users(send_users.mapped('partner_id'))
            else:
                con_user = next_flow_line_id._get_flow_users(self.branch_id, self.user_id.department_id, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(con_user.mapped('display_name'))
                raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
                # raise UserError(_('You are not confirm user'))

    def action_back_stage(self):
        back_flow_line_id = self.flow_line_id._get_back_flow_line()
        if back_flow_line_id:
            if self.visible_flow_line_ids and back_flow_line_id.id not in self.visible_flow_line_ids.ids:
                check_next_flow_line_id = back_flow_line_id
                while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:

                    temp_stage = check_next_flow_line_id._get_back_flow_line()
                    if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
                        break;
                    check_next_flow_line_id = temp_stage
                back_flow_line_id = check_next_flow_line_id

            if back_flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, False):
                self.flow_line_id = back_flow_line_id
                # History uusgeh
                self.env['purchase.flow.history'].create_history_po(back_flow_line_id, self)
                # chat ilgeeh
                for item in self.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
                    self.send_chat_employee(item)

            else:
                raise UserError(_('You are not back user'))

    def action_cancel_stage(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, False):
            self.flow_line_id = flow_line_id

            # History uusgeh
            self.env['purchase.flow.history'].create_history_po(flow_line_id, self)

            # chat ilgeeh
            for item in self.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
                self.send_chat_employee(item)

            self.button_cancel()
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['purchase.flow.history'].create_history_po(flow_line_id, self)
        else:
            raise UserError(_('You are not draft user'))
    #------------------------------flow------------------



    def check_comparison(self):
        if self.is_comparison and not self.win_partner_id:
            raise UserError(_('Харицуулалттай байна'))

    pr_line_many_ids = fields.Many2many(related='order_line.pr_line_many_ids')
    po_type = fields.Selection([('internal','Дотоод'), ('foreign','Гадаад')], 'Төрөл', default='internal')
    user_id = fields.Many2one('res.users', string='Хариуцагч', default=lambda self: self.env.user.id)
    history_ids = fields.One2many('purchase.flow.history', 'purchase_id', 'Түүхүүд')


    def send_chat_employee(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('mw_purchase_request', 'action_purchase_request_tree_view')[1]
        html = u'<b>Худалдан авалтын захиалга</b><br/>%s Ажилтаны үүсгэсэн </br>'%(', '.join(partner_ids.mapped('name')))
        for pr in self.order_line.mapped('pr_line_many_ids').filtered(lambda r: r.request_id.sudo().employee_id.user_id.partner_id.id in partner_ids.ids).mapped('request_id'):
            html += u"""<b><a target="_blank" href=%s/web#id=%s&model=purchase.request&action=%s>%s</a></b>, """% (base_url,pr.id,action_id,pr.name)
        html +=u' Хүсэлтийн </br> <b>%s</b> дугаартай Худалдан авалтын захиалга </br> <b>%s</b> төлөвт орлоо'% (self.name,state)

        self.flow_line_id.send_chat(html, partner_ids)

    def send_chat_next_users(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_action_generic')[1]
        html = u'<b>Худалдан авалтын захиалга</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.user_id.name)
        html += u"""<b><a target="_blank" href=%s/web#id=%s&form&model=purchase.order&action=%s>%s</a></b>, дугаартай Худалдан авалтын захиалгыг батлана уу"""% (base_url,self.id,action_id,self.name)
        self.flow_line_id.send_chat(html, partner_ids)

    def get_view_purchase_request(self):
        context = dict(self._context)
        tree_view_id = self.env.ref('mw_purchase_request.purchase_request_line_tree_view').id
        form_view_id = self.env.ref('mw_purchase_request.purchase_request_line_form_view').id
        action = {
                'name': u'Хүсэлт',
                'view_mode': 'tree',
                'res_model': 'purchase.request.line',
                'domain': [('id','in',self.order_line.mapped('pr_line_many_ids').ids)],
                # 'domain': [('id','in',self.pr_line_ids.ids)],
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_id': tree_view_id,
                'type': 'ir.actions.act_window',
                # 'context': context,
                'target': 'current'
            }
        return action

    def create_invoice_hand(self):
        return self.with_context(default_branch_id=self.branch_id.id).action_view_invoice()
        # inv_obj = self.env['account.invoice']
        # # if self.invoice_ids:
        # #     return False

        # journal_domain = [
        #     ('type', '=', 'purchase'),
        #     ('company_id', '=', self.company_id.id),
        #     # ('currency_id', '=', self.partner_id.property_purchase_currency_id.id),
        # ]
        # default_journal_id = self.env['account.journal'].search(journal_domain, limit=1,order='id')
        # vals = {
        #     'partner_id': self.partner_id.id,
        #     'purchase_id': self.id,
        #     'origin': self.name,
        #     'reference': self.partner_ref,
        #     'journal_id': default_journal_id.id if default_journal_id else False,
        #     'date_invoice': self.date_planned,
        #     'type': 'in_invoice',
        #     'branch_id':self.branch_id.id,
        #     'currency_id':self.currency_id.id
        # }
        # invoice_id = inv_obj.create(vals)
        # invoice_id._onchange_partner_id()
        # invoice_id.purchase_order_change()

        # invoice_id.compute_taxes()
        # if invoice_id.amount_total==0:
        #     raise UserError(u'Нэхэмжлэх үүсгэх мөр алга')

        # return {}

    def get_company_logo(self, ids):
        report_id = self.browse(ids)
        image_buf = report_id.company_id.logo_web.decode('utf-8')
        image_str = '';
        if len(image_buf)>10:
            image_str = '<img alt="Embedded Image" width="400" src="data:image/png;base64,%s" />'%(image_buf)
        return image_str

    def get_order_line(self, ids):
        headers = [
        u'Бар код',
        u'Барааны нэр',
        u'Хэмжих нэгж',
        u'Тоо хэмжээ',
        u'Нэгж үнэ',
        u'Нийт үнэ',
        u'Хөнгөлөлт %',
        u'Хөнгөлөлтийн дүн',
        u'Төлөх дүн',
        ]
        datas = []
        report_id = self.browse(ids)

        i = 1

        lines = report_id.order_line
        sum1 = 0
        sum2 = 0
        sum3 = 0

        for line in lines:
            p_name = line.product_id.default_code or line.product_id.product_code or ''
            b_name = line.product_id.barcode
            u_name = line.product_uom.name
            discount_amount = line.price_total*line.discount/100
            am = line.price_total-discount_amount
            temp = [
            b_name,
            p_name,
            u_name,
            "{0:,.0f}".format(line.product_qty) or '',
            u'<p style="text-align: right;">'+("{0:,.2f}".format(line.price_unit_without_discount) or '')+u'</p>',
            u'<p style="text-align: right;">'+("{0:,.2f}".format(line.price_unit_without_discount*line.product_qty) or '')+u'</p>',
            u'<p style="text-align: right;">'+("{0:,.2f}".format(line.discount) or '')+u'</p>',
            u'<p style="text-align: right;">'+("{0:,.2f}".format(discount_amount) or '')+u'</p>',
            u'<p style="text-align: right;">'+("{0:,.2f}".format(line.price_total) or '')+u'</p>',
            ]
            datas.append(temp)
            i += 1

        # datas.append(temp)
        res = {'header': headers, 'data':datas}
        return res

    def get_user_signature(self,ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
        history_obj = self.env['purchase.flow.history']
        for item in print_flow_line_ids:
            his_id = history_obj.search([('flow_line_id','=',item.id),('purchase_id','=',report_id.id)], limit=1)
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

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    pr_line_many_ids = fields.Many2many('purchase.request.line', 'purchase_order_line_purchase_request_line_rel', 'po_line_id', 'pr_line_id', string='Хүсэлтийн мөрүүд')
    flow_id = fields.Many2one('dynamic.flow', related='order_id.flow_id', readonly=True, store=True)

    def unlink(self):
        for this in self:
            if this.pr_line_many_ids and this.order_id.state!='cancel':
                raise UserError(u'PR-аас үүссэн байна')

        return super(purchase_order_line, self).unlink()

    # @api.model
    # def create(self, val):
    #     res  =  super(purchase_order_line,self).create(val)
    #     for item in res:
    #         item.onchange_product_id()
    #     return res
