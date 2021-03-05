# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

from odoo.addons.mw_base.report_helper import verbose_numeric, comma_me, convert_curr
from odoo.addons.mw_base.verbose_format import verbose_format

class AccountMovePrint(models.TransientModel):
    _name = 'account.move.print'
    _description = 'Account Move print'

    move_id = fields.Many2one('account.move', string='Journal Entry',)
#         domain=[('state', '=', 'posted'), ('type', 'not in', ('out_refund', 'in_refund'))])
    date = fields.Date(string='print date', default=fields.Date.context_today, required=True)
    account_ids = fields.Many2many('res.partner.bank', string='accounts', )

    is_lebal = fields.Boolean(string=u'Гүйлгээний утгаас авах', default=False)

    is_so_name = fields.Boolean(string=u'PO дугаар?', default=False)
    is_ot_code = fields.Boolean(string=u'ОТ код?', default=False)
    
    date_str = fields.Char(string=u'Төлбөрийн нөхцөл')

    @api.model
    def default_get(self, fields):
        res = super(AccountMovePrint, self).default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']
        
#         res['refund_method'] = (len(move_ids) > 1 or move_ids.type == 'entry') and 'cancel' or 'refund'
#         res['residual'] = len(move_ids) == 1 and move_ids.amount_residual or 0
#         res['currency_id'] = len(move_ids.currency_id) == 1 and move_ids.currency_id.id or False
        res['move_id'] = len(move_ids) == 1 and move_ids.id or False
        return res


    def part_name(self,ids):
        line=self.browse(ids)
        name=''
        if line.move_id.partner_id:
            name = line.move_id.partner_id.name
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))   
        return name    


    def part_addr(self,ids):
        line=self.browse(ids)
        name=''
        if line.move_id.partner_id and line.move_id.partner_id.street:
            name = line.move_id.partner_id.street
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))   
        return name    


    def part_vat(self,ids):
        line=self.browse(ids)
        name=''
        if line.move_id.partner_id and line.move_id.partner_id.vat:
            name = line.move_id.partner_id.vat
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))   
        return name    


    def get_date(self,ids):
        line=self.browse(ids)
        name=''
        if line.move_id and line.move_id.date:
            name = str(line.move_id.date)
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))   
        return name    
    

    def pay_date(self,ids):
        line=self.browse(ids)
        name=''
        if line.date_str:
            name = line.date_str
        elif line.date:
            name = str(line.date)
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))   
        return name      
    
    def com_name(self,ids):
        line=self.browse(ids)
        name=''
        if line.move_id:
            name = line.move_id.company_id.name
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))  
        return name    
    
    

    def com_addr(self,ids):
        line=self.browse(ids)
        name=''
        if line.move_id and line.move_id.company_id.partner_id.street:
            name = line.move_id.company_id.partner_id.street
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))  
        return name        

    def com_phone(self,ids):
        line=self.browse(ids)
        name=''
        if line.move_id and line.move_id.company_id.partner_id.phone:
            name = line.move_id.company_id.partner_id.phone
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))  
        return name     


    def com_bank_acc(self,ids):
        line=self.browse(ids)
        name=''
        if line.account_ids:
            for acc in line.account_ids:
                name += acc.acc_number+' , ' 
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))  
        return name     

    def com_bank(self,ids):
        line=self.browse(ids)
        name=''
        if line.account_ids:
            for acc in line.account_ids:
                if acc.bank_id:
                    name += acc.bank_id.name+' , ' 
#         else:
#             raise UserError(_(u'Харилцагчаа сонгоно уу!'))  
        return name     
    

    def get_company_logo(self, ids):    
        report_id = self.browse(ids)
        print ('report_id.move_id.company_id ',report_id.move_id.company_id)
        if report_id.move_id.company_id and not report_id.move_id.company_id.logo_web:
            raise UserError(_(u'Компаний мэдээлэл дээр логогоо сонгоно уу!'))   

        image_buf = report_id.move_id.company_id.logo_web.decode('utf-8')
        image_str = '';
        if len(image_buf)>10:
            image_str = '<img alt="Embedded Image" width="550" src="data:image/png;base64,%s" />'%(image_buf)
        return image_str
      

    def amount_str(self,ids):
#         line=self.browse(ids)
#         list = verbose_numeric(abs(line.amount))[0]
        moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id
        report_id = moves[0]
        list=verbose_format(abs(report_id.amount_total))
        return list

         
         
    def get_move_product_line(self, ids):
        datas = []
        moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id
        report_id = moves[0]

        i = 1
        lines = []
        lines = report_id.invoice_line_ids
        sum1 = 0
        sum2 = 0
        sum3 = 0
        nbr = 1
        code=''
        otcode=''
        ss = self.env['account.move.print'].browse(ids)
        for line in lines:
            if ss.is_lebal:
                name = line.name
            else:
                name = line.product_id.name# + (line.product_id.default_code and ' [ '+line.product_id.default_code+' ] ' or '')
            qty = line.quantity
            price_unit = line.price_unit
            price_subtotal = line.price_subtotal
            sum2 += qty
            sum3 += price_subtotal

            if ss.is_so_name and ss.is_ot_code:
                so_name=''
                if len(line.sale_line_ids)>0:
                    so_name=line.sale_line_ids[0].name
                code=line.product_id.default_code
                otcode=line.product_id.product_code and line.product_id.product_code or ''
                temp = [
                u'<p style="text-align: center;">'+str(nbr)+u'</p>',
                u'<p style="text-align: left;">'+(so_name)+u'</p>',
                u'<p style="text-align: left;">'+(otcode)+u'</p>',
                u'<p style="text-align: left;">'+(code)+u'</p>',
                u'<p style="text-align: left;">'+(name)+u'</p>',
                "{0:,.0f}".format(qty) or '',
                "{0:,.0f}".format(price_unit) or '',
                "{0:,.0f}".format(price_subtotal) or '',
                ]         
            elif ss.is_so_name:
                so_name=''
                if len(line.sale_line_ids)>0:
                    so_name=line.sale_line_ids[0].name
                code=line.product_id.default_code
                otcode=line.product_id.product_code and line.product_id.product_code or ''
                temp = [
                u'<p style="text-align: center;">'+str(nbr)+u'</p>',
                u'<p style="text-align: left;">'+(so_name)+u'</p>',
#                 u'<p style="text-align: left;">'+(otcode)+u'</p>',
                u'<p style="text-align: left;">'+(code)+u'</p>',
                u'<p style="text-align: left;">'+(name)+u'</p>',
                "{0:,.0f}".format(qty) or '',
                "{0:,.0f}".format(price_unit) or '',
                "{0:,.0f}".format(price_subtotal) or '',
                ]                       
            else:
                temp = [
                u'<p style="text-align: center;">'+str(nbr)+u'</p>',
                u'<p style="text-align: left;">'+(name)+u'</p>',
                "{0:,.0f}".format(qty) or '',
                "{0:,.0f}".format(price_unit) or '',
                "{0:,.0f}".format(price_subtotal) or '',
                ]                
            nbr += 1
            datas.append(temp)
            i += 1

        if ss.is_so_name and ss.is_ot_code:
            temp = [
                u'',
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Нийт дүн</p>', 
                "{0:,.0f}".format(sum2) or '',
                u'',
                "{0:,.0f}".format(sum3) or '',
                ]
            
            if not datas:
                return False
            datas.append(temp)
            
            temp = [
                u'',
                u'',
                u'',
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Дүн</p>', 
                "{0:,.0f}".format(report_id.amount_untaxed) or '',
                ]
            datas.append(temp)  
            temp = [
                u'',
                u'',
                u'',
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">НӨАТ</p>', 
                "{0:,.0f}".format(report_id.amount_tax) or '',
                ]
            datas.append(temp)  
    
            temp = [
                u'',
                u'',
                u'',
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Дүн</p>', 
                "{0:,.0f}".format(report_id.amount_total) or '',
                ]            
        elif ss.is_so_name:
            temp = [
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Нийт дүн</p>', 
                "{0:,.0f}".format(sum2) or '',
                u'',
                "{0:,.0f}".format(sum3) or '',
                ]
            
            if not datas:
                return False
            datas.append(temp)
            
            temp = [
                u'',
                u'',
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Дүн</p>', 
                "{0:,.0f}".format(report_id.amount_untaxed) or '',
                ]
            datas.append(temp)  
            temp = [
                u'',
                u'',
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">НӨАТ</p>', 
                "{0:,.0f}".format(report_id.amount_tax) or '',
                ]
            datas.append(temp)  
    
            temp = [
                u'',
                u'',
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Дүн</p>', 
                "{0:,.0f}".format(report_id.amount_total) or '',
                ]            
        else:
            temp = [
                u'',
                u'<p style="text-align: center;">Нийт дүн</p>', 
                "{0:,.0f}".format(sum2) or '',
                u'',
                "{0:,.0f}".format(sum3) or '',
                ]
            
            if not datas:
                return False
            datas.append(temp)
            
            temp = [
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Дүн</p>', 
                "{0:,.0f}".format(report_id.amount_untaxed) or '',
                ]
            datas.append(temp)  
            temp = [
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">НӨАТ</p>', 
                "{0:,.0f}".format(report_id.amount_tax) or '',
                ]
            datas.append(temp)  
    
            temp = [
                u'',
                u'',
                u'',
                u'<p style="text-align: center;">Дүн</p>', 
                "{0:,.0f}".format(report_id.amount_total) or '',
                ]            
        datas.append(temp)                        
        return datas
    
    def get_move_line(self, ids):
        report_id = self.browse(ids)
        print ('report_id ',report_id)
        if report_id.is_so_name and report_id.is_ot_code:
            headers = [
            u'№',
            u'PO дугаар',
            u'ОТ код',
            u'Код',
            u'Гүйлгээний утга',
            u'Тоо хэмжээ',
            u'Нэгж үнэ',
            u'Нийт үнэ',
            ]            
        elif report_id.is_so_name:
            headers = [
            u'№',
            u'PO дугаар',
            u'Код',
            u'Гүйлгээний утга',
            u'Тоо хэмжээ',
            u'Нэгж үнэ',
            u'Нийт үнэ',
            ]
        else:
            headers = [
            u'№',
            u'Гүйлгээний утга',
            u'Тоо хэмжээ',
            u'Нэгж үнэ',
            u'Нийт үнэ',
            ]            

        datas = self.get_move_product_line(ids)
        if not datas:
            return ''
        res = {'header': headers, 'data':datas}
        return res

    
    def print_moves(self):
        html = ''
        counter = 1
        moves = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.move_id
        model_id = self.env['ir.model'].sudo().search([('model','=','account.move.print')], limit=1)
        template=False
        if moves[0].type in ('out_invoice', 'out_refund','in_invoice'):
            template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','invoice')], limit=1)
#         else:
#             return self.env['report'].get_action(self, 'mn_account.report_cash_income_receipt')
#             if self.amount<0:
#                 template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','cash_expense')], limit=1)
#             else:
#                 template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','cash_income')], limit=1)
            
            if template:
                pttrn_name='<th '
                template_html = template.sudo().get_template_data_html(self.id)
#                 print ('template_html ',template_html)
                if template_html:
                    template_html = template_html.replace(pttrn_name, '<th style="font-weight: normal;" ')

                pttrn_name = 'border: 1px solid #dddddd;'
                if template_html:
                    template_html = template_html.replace(pttrn_name, 'border: 1px solid #777777;')
                    back_html = u"""
    <div id="background" style="
    position:absolute;
    z-index:0;
    background:white;
    display:block;
    min-height:100%; 
    min-width:100%;
   ">
    </div>
"""
                    html += back_html+u'<div class="break_page" style="z-index: 1; position:absolute;">'+template_html+'</div>'
                    first_picking = moves[0]
                    # html += u'<div class="break_page">'+template_html+'</div>'
                    counter+=1            
        return template.sudo().print_template_html(html)
#         if template:
#             res = template.sudo().print_template(self.id)
#             return res
#         else:
#             raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))   
