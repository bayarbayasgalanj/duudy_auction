# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import time
from datetime import datetime, time, timedelta

class ImportBankInvoice(models.TransientModel):
    _name = 'import.bank.invoice'
    _description = 'Import Invoice'
    
    TYPE_SELECTION = [
#         ('incash','Incash'),
        ('invoice','Invoice'),
        ('move','Account Move')
    ]    
    
    @api.model
    def default_get(self, fields):
        rec = super(ImportBankInvoice, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
#         department_id=False
        partner_id=False
        is_account_cost_sharing=False
        currency_id=False
#         cashflow_account_id=False
        is_line=False
        to_line=False
        income_line=False
        if context.get('active_model',False) and context['active_model']=='cash.income.line':
            income_line=True
            context.update({'income_line':True})
#             br=self.browse(context['wizard_ids'][0])
#             partner_id=br.partner_id.id
#             cashflow_account_id=br.parent_id.cashflow_account_id.id
#             currency_id=br.parent_id.currency_id.id
            payments = self.env[active_model].browse(active_ids)
            partner_id=payments.partner_id.id
#             cashflow_account_id=payments.cashflow_account_id.id
            currency_id=payments.parent_id.currency_id.id
#             department_id=payments.parent_id.department_id.id
#         print 'context---- ',context
        if context.get('to_line',False) and context['to_line']:
            to_line=True
        if context.get('from_line',False) and context['from_line']:
            if context['wizard_ids']:
                br=self.browse(context['wizard_ids'][0])
                partner_id=br.partner_id.id
                is_line=True
            elif context.get('partner_id',False):
                partner_id=context['partner_id']
                is_line=True
                
        if not active_model or not active_ids:
            raise UserError(_("Programmation error: wizard action executed without active_model or active_ids in context."))
        
        payments = self.env[active_model].browse(active_ids)
        rec.update({
#             'department_id':department_id,
            'partner_id':partner_id,
#             'cashflow_account_id':cashflow_account_id,
#             'currency_id':currency_id,
            'is_line':is_line,
            'to_line':to_line
        })
        return rec
    
    type = fields.Selection(TYPE_SELECTION, string='Type', default='move', required=True)
    partner_id = fields.Many2one('res.partner', string='Receiving Partner',required=True)
    inv_ids = fields.Many2many('account.move', 'account_invoice_bank_import_relation', 'invoice_id', 'line_id', 'Account invoice')#invoice
    move_ids = fields.Many2many('account.move.line', 'account_move_line_bank_import_relation', 'move_id', 'line_id', 'Account move line')
#     currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    
    self_line_ids = fields.One2many('import.bank.invoice.line','parent_id','Line')
    is_multi = fields.Boolean(u'Олон гүйлгээ', help=u"Олон гүйлгээ нийлүүлэх бол.", default=False)
    is_line = fields.Boolean(u'Мөрөөс',default=False)
    to_line = fields.Boolean(u'Мөрөөс мөрүү',default=False)
    income_line = fields.Boolean(u'Мөрөөс дуудах',default=False)

    date = fields.Date(required=True, string=u'Огноо', default=fields.Date.context_today)
    amount = fields.Float(string=u'Дүн',)

    self_aml_line_ids = fields.One2many('import.bank.account.move.line','parent_id','Line')
    sort_by_due = fields.Boolean(u'Төлөх огноогоор сортлох',default=False)

    multi_inv_ids = fields.Many2many('account.move', 'account_invoice_multi_bank_import_relation', 'invoice_id', 'line_id', 'Account invoice')#invoice
    is_multi_invoice_choose = fields.Boolean(u'Select?',default=True)

#     is_aml = fields.Boolean(u'Санхүү бичилтээс?', help=u"Import from account move line.", default=False)

    
    def populate_statement_line(self):
        context=self._context
        payment_id = context.get('line_id', False)
        
        data = self.read()[0]
        line_ids = data['self_line_ids']
        self_line_obj = self.env['import.bank.invoice.line']
#         print 'self.inv_ids ',self.inv_ids
        for inv in self.inv_ids:
            vals = {'type': self.type,
                'partner_id': inv.partner_id.id,
                'invoice_id': inv.id,
                'parent_id':context['active_id'],#self.id,#context['wizard_ids'][0],
                'amount':inv.residual,
                'date':inv.date
                }
#                 print "valsvalsvals ",vals
            new_line_id = self_line_obj.create(vals)
        context=context.copy()
        context.update({'to_line': True})
        income_line=False
        if context.get('income_line',False):
            income_line = context['income_line']
#         self.env['import.bank.invoice'].browse(context['wizard_ids'][0]).write({'to_line': True,'income_line':income_line})
        self.env['import.bank.invoice'].browse(context['active_id']).write({'to_line': True,'income_line':income_line})

        return {
            'name': _('Wizard'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.bank.invoice',
            'res_id': context['active_id'],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }
    
    
    def populate_statement_inv(self):
        context=self._context
        context = dict(context or {})
        payment_id = context.get('line_id', False)
        if not payment_id:
            return {'type': 'ir.actions.act_window_close'}
        
        data = self.read()[0]
        line_ids = data['inv_ids']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}
        
        partner_id = data['partner_id']
        if partner_id:
            partner_id=partner_id[0]
        
        inv_obj = self.env['account.invoice']
        payment_obj = self.env['account.bank.statement']
        bank_line_obj = self.env['account.bank.statement.line']
        currency_obj = self.env['res.currency']
        move_line_obj = self.env['account.move.line']
        payment = payment_obj.browse(payment_id)
        line_date = payment.date
        
        
        # for each selected move lines
        name=''
        for line in inv_obj.browse(line_ids):
#             partner_id=line.partner_id.id
            part = self.env['res.partner']._find_accounting_partner(line.partner_id)
            partner_id=part.id
            account_id=line.account_id.id
            if line.name:
                name=line.name+' '
            else:
                name=line.move_name+' '
            amount_currency=0.0
#             print 'in_invoice ',line.type
            if line.type=='in_invoice':
                amount = -line.residual
            else:
                amount = line.residual
            rate = 0.0
            if line.currency_id != payment.currency_id:
                amount_currency = line.residual
                amount = payment.currency_rate*amount_currency
                rate=line.invoice_id.currency_rate
            ctx = context.copy()
            #  take the date for computation of currency => use payment date
            ctx['date'] = line_date
#             amount = line.residual
#             if line.residual > 0.0:
#                 amount = line.residual+line.amount_tax
#             print      "amount :" , amount
            import_move_id=False
            ref=''
            move_line_id = move_line_obj.search(
                [('account_id', '=', line.account_id.id), ('invoice_id', '=', line.id)])  # , ('reconcile','=',False)
            if move_line_id:
                move_line = move_line_obj.browse(move_line_id.id)
                import_move_id = move_line.id
                ref  =move_line.ref
            context.update({'invoice_id': line.id})
            bank_line_obj.create({
                'name': name,
                'amount': amount,
#                 'date':time.strftime("%Y-%m-%d"),
                'date': payment.date,
    #             'invoice_id': line.id,
                'statement_id':context['active_id'],
#                 'is_payment': True,
    #                 'sector_id':department_id,
                'account_id':account_id,    
                'state':'draft',
    #             'cashflow_account_id':cashflow_account_id,
                'partner_id':partner_id,
                'invoice_ids':[(6,0,[line.id])],
                'date':data['date'],
                'import_line_id': import_move_id,
                'ref': ref,
            })
#             statement_line_obj.create({
#                     'name': move_line.name or '?',
#                     'amount': amount,
#                     'partner_id': move_line.partner_id.id,
#                     'bank_account_id': bank_account_id,
#                     'statement_id': statement_id,
#                     'ref': move_line.ref,
#                     'date': statement.date,
#                     'amount_currency': move_line.amount_currency,
#                     'currency_id': move_line.currency_id.id,
#                     'import_line_id': move_line.id,
#                     'account_id': line.account_id.id,
#                     'cashflow_id': False
#                 })            
        return {'type': 'ir.actions.act_window_close'}

    
    def populate_statement_multi_inv(self):
        '''Олон гүйлгээ
        '''
        context=self._context
        context = dict(context or {})
#         print 'context4 ',context
#         print 'self.income_line ',self.income_line
        if self.income_line:
            data = self.read()[0]
            line_ids = data['self_line_ids']
            
#             department_id = data['department_id']
#             if department_id:
#                 department_id=department_id[0]
                
            partner_id = data['partner_id']
            if partner_id:
                partner_id=partner_id[0]
            
            line_obj = self.env['import.bank.invoice.line']
            inv_obj = self.env['account.invoice']
            payment_obj = self.env['cash.income']
            payment_line_obj = self.env['cash.income.line']
            currency_obj = self.env['res.currency']
#             payment = payment_obj.browse(context['active_id'])
            payment_line = payment_line_obj.browse(context['active_id'])
            payment=payment_line.parent_id
            line_date = payment.date
            # for each selected move lines
            invoice_ids=[]
            name=''
            amount=0
            amount_currency=0
            account_id=False
            partner_id=False
            amsl_vals = []
            for line in line_obj.browse(line_ids):
    #             print "line ",line
    #             print "line invoice_id ",line.invoice_id
                amount_currency=0.0
                amount += line.amount
                invoice_ids.append(line.invoice_id.id)
                rate = 0.0
                partner_id=line.invoice_id.partner_id.id
                account_id=line.invoice_id.account_id.id
                name+=line.invoice_id.reference+' '
#                 if line.currency_id != payment.currency_id:
#                     amount_currency = line.residual
#                     amount = payment.currency_rate*amount_currency
#                     rate=line.invoice_id.currency_rate
                ctx = context.copy()
                #  take the date for computation of currency => use payment date
                ctx['date'] = line_date
                amsl_vals += [(0,0,{
    #                                                        'line_ids': [(6, 0, [line.id])]
                                    'inv_amount':line.amount,
                                    'import_inv_id':line.invoice_id.id
                                        })]
            if invoice_ids:
                invoice_ids = list(set(invoice_ids))
    
            payment_line.write({
                'invoice_ids':[(6,0,invoice_ids)],
                'import_line_ids':amsl_vals
            })
            return {'type': 'ir.actions.act_window_close'}            
        else:#Олон мөрөөс үүссэн нэхэмжлэх
            data = self.read()[0]
            line_ids = data['self_line_ids']
            if not line_ids:
                return {'type': 'ir.actions.act_window_close'}
            partner_id = data['partner_id']
            if partner_id:
                partner_id=partner_id[0]
            line_obj = self.env['import.bank.invoice.line']
            inv_obj = self.env['account.invoice']
            payment_obj = self.env['account.bank.statement']
            payment_line_obj = self.env['account.bank.statement.line']
            currency_obj = self.env['res.currency']
#             payment = payment_obj.browse(context['active_id'])
            payment = payment_obj.browse(context['line_id'])
            line_date = payment.date
            # for each selected move lines
            invoice_ids=[]
            name=''
            amount=0
            amount_currency=0
            account_id=False
            partner_id=False
            amsl_vals = []
            ref=''
            for line in line_obj.browse(line_ids):
                amount_currency=0.0
                if line.invoice_id.type=='in_invoice':
                    amount += -line.amount
                else:
                    amount += line.amount
                if line.invoice_id.origin:
                    ref +=line.invoice_id.origin+', '
                invoice_ids.append(line.invoice_id.id)
                rate = 0.0
                partner_id=line.invoice_id.partner_id.id
                account_id=line.invoice_id.account_id.id
#                 name+=line.invoice_id.move_name+' '
                if line.invoice_id.origin:
                    name+=line.invoice_id.origin+' '
                if line.invoice_id.reference:
                    name+=line.invoice_id.reference+' '

                ctx = context.copy()
                #  take the date for computation of currency => use payment date
                ctx['date'] = line_date
                amsl_vals += [(0,0,{
    #                                                        'line_ids': [(6, 0, [line.id])]
                                    'inv_amount':line.amount,
                                    'import_inv_id':line.invoice_id.id
                                        })]
            if invoice_ids:
                invoice_ids = list(set(invoice_ids))
#             print 'context54321--: ',context
                
            payment_line_obj.create({
                'name': name,
                'amount': amount,
#                 'date':time.strftime("%Y-%m-%d"),
                'date':self.date,
                'statement_id':context['line_id'],
                'account_id':account_id,    
                'state':'draft',
                'partner_id':partner_id,
                'ref':ref,
                'import_line_ids':amsl_vals
            })
            return {'type': 'ir.actions.act_window_close'}
       
    
    def populate_statement(self):
        context=self._context
        context = dict(context or {})
        payment_id = context.get('line_id', False)
        if not payment_id:
            return {'type': 'ir.actions.act_window_close'}
        
        data = self.read()[0]
        line_ids = data['line_ids']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}
        
        partner_id = data['partner_id']
        if partner_id:
            partner_id=partner_id[0]
            
        line_obj = self.env['account.cost.sharing.line']
        inv_obj = self.env['account.invoice']
        payment_obj = self.env['cash.income']
        payment_line_obj = self.env['cash.income.line']
        currency_obj = self.env['res.currency']
        payment = payment_obj.browse(payment_id)
        line_date = payment.date

        # for each selected move lines
        for line in line_obj.browse(line_ids):
            ctx = context.copy()
            #  take the date for computation of currency => use payment date
            ctx['date'] = line_date
            amount = line.residual
            amount_currency = line.residual_currency
            
            vals = {}
            if line.transaction_currency_id.id != payment.currency_id.id:
                rate=0.0
                if amount_currency > 0.0:
                    rate = amount/amount_currency
                vals = { 'name': line.name or '?',
                        'amount': amount,
                        'amount_currency': amount_currency,
                        'account_cost_share_line_id': line.id,
                        'parent_id':payment_id,
                        'is_payment': True,
#                         'sector_id':department_id,
                        'account_id':line.receivable_account_id.id,
                        'state':payment.state,
#                         'cashflow_account_id':cashflow_account_id,
                        'partner_id':partner_id,
                        'is_other_currency':True,
                        'receiving_payment_account_id':payment.receiving_payment_account_id.id,
                        'currency_id':payment.currency_id.id,
                        'transaction_currency_id':line.transaction_currency_id.id,
                        'currency_rate':rate,
                        'tax_id':payment.tax_id.id if payment.tax_id else False,
                        'date':payment.date}
            else:
                vals = { 'name': line.name or '?',
                        'amount': amount,
                        'account_cost_share_line_id': line.id,
                        'parent_id':payment_id,
#                         'is_payment': True,
#                         'sector_id':department_id,
                        'account_id':line.receivable_account_id.id,
                        'state':payment.state,
#                         'cashflow_account_id':cashflow_account_id,
                        'partner_id':partner_id,
                        'receiving_payment_account_id':payment.receiving_payment_account_id.id,
                        'currency_id':payment.currency_id.id,
                        'transaction_currency_id':line.transaction_currency_id.id,
                        'is_other_currency':payment.is_other_currency,
#                         'tax_id':payment.tax_id.id if payment.tax_id else False,
                        'date':payment.date}
            payment_line_obj.create(vals)
        return {'type': 'ir.actions.act_window_close'}

    def button_import_invoice(self, context=None):
        ''' Харилцахын болон кассын ордер дээх нэхэмжлэл импорт хийнэ.
        '''
        mod_obj = self.env['ir.model.data']
        if context is None:
            context = {}
        context.update({'from_line': True,'wizard_ids':self.ids})
#         print 'context1 ',context
        if self.sort_by_due:
            query = """
                select id from account_invoice where residual>0 and partner_id={0} and type in ('in_invoice','out_invoice') order by date_due,id
            """.format(self.partner_id.id)
        else:
            query = """
                    select id from account_invoice where residual>0 and partner_id={0} and type in ('in_invoice','out_invoice') order by date_invoice,id
                """.format(self.partner_id.id)

        self.env.cr.execute(query)
        invoice_ids = self.env.cr.fetchall()   
#         print 'invoice_ids ',invoice_ids
        self_amount=self.amount
        amount=0
        self_line_obj = self.env['import.bank.invoice.line']
        invoice_obj = self.env['account.invoice']
        inv_dic={}
        if 0>=self_amount:
            raise UserError(_(u"Шилжүүлэх мөнгөн дүнгээ оруулана уу!!."))
        
        for invoice in invoice_obj.browse([i[0] for i in invoice_ids]):
            if (amount+invoice.residual)<self_amount:
                amount+=invoice.residual
                inv_dic[invoice.id]=invoice.residual
            elif (amount+invoice.residual)==self_amount:
                amount+=invoice.residual
                inv_dic[invoice.id]=invoice.residual
                break
            else:
                inv_dic[invoice.id]=self_amount-amount
                amount+=self_amount-amount
                break
        if amount<self_amount:
            raise UserError(_(u"Нийт нээлттэй нэхэмжлэхүүдийн дүн шилжүүлгийн дүнд хүрэхгүй байна."))
            
#         print 'context123 1 ',context
#         print 'self.inv_ids ',self.inv_ids
        res_id=self.env['import.bank.invoice'].with_context(context).create({'type':'invoice',
                                                       'partner_id':self.partner_id.id
                                                       ,'is_multi':True,'date':self.date,
                                                       'to_line':True,'is_line':False})
        for inv in inv_dic:
            invoice=invoice_obj.browse(inv)
            vals = {'type': self.type,
                'partner_id': invoice.partner_id.id,
                'invoice_id': inv,
                'parent_id':res_id.id,#self.id,#context['wizard_ids'][0],
                'amount':inv_dic[inv],
                'date_invoice':invoice.date_invoice,
                'number':invoice.number,
                'residual':invoice.residual,
                'state':invoice.state,
                'origin':invoice.origin
                }
            
#                 print "valsvalsvals ",vals
            new_line_id = self_line_obj.create(vals)
#         context=context.copy()
#         context.update({'to_line': True})
#         print '123123 ',context['active_id']
#         income_line=False
#         if context.has_key('income_line'):
#             income_line = context['income_line']
# #         self.env['import.bank.invoice'].browse(context['wizard_ids'][0]).write({'to_line': True,'income_line':income_line})
#         self.env['import.bank.invoice'].browse(context['active_id']).write({'to_line': True,'income_line':income_line})
            
#         return {
#             'name': _('Import Invoice'),
#             'context': context,
#             'view_type': 'form',
#             'view_mode': 'tree,form',
#             'res_model': 'import.bank.invoice',
#             'views': [(resource_id,'form')],
#             'type': 'ir.actions.act_window',
#             'target': 'new',
# #             'nodestroy': True
#         }
#         
        form_res = mod_obj.get_object_reference('mn_account', 'view_import_bank_invoice')
        form_id = form_res and form_res[1] or False
        return {
            'name': _('Account Transaction Balance Report'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'import.bank.invoice',
            'res_id': res_id.id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target':'new'
        }         

    @api.onchange('date')
    def onchange_date(self):
        vals = {}
        if self.date:
            for line in self.self_aml_line_ids:
                line.date=self.date
                line.onchange_date()
#                 self.rate = self.set_currency()
    
    
    @api.onchange('multi_inv_ids')
    def onchange_multi_inv_ids(self):
        if self.multi_inv_ids:
            mod_obj = self.env['ir.model.data']
            context = self._context.copy()
            context.update({'from_line': True,'wizard_ids':self.ids})

            self_amount=self.amount
            amount=0
            self_line_obj = self.env['import.bank.invoice.line']
            invoice_obj = self.env['account.invoice']
            inv_dic={}
    #         if 0>=self_amount:
    #             raise UserError(_(u"Шилжүүлэх мөнгөн дүнгээ оруулана уу!!."))
            if self.multi_inv_ids:
                invoice_ids= self.multi_inv_ids
            for invoice in self.multi_inv_ids:#invoice_obj.browse([i[0] for i in invoice_ids]):
                    amount+=invoice.residual
                    inv_dic[invoice.id]=invoice.residual
    #         if amount<self_amount:
    #             raise UserError(_(u"Нийт нээлттэй нэхэмжлэхүүдийн дүн шилжүүлгийн дүнд хүрэхгүй байна."))
    #         print 'self.inv_ids ',self.inv_ids
#             context.update({'to_line':True})
#             res_id=self.env['import.bank.invoice'].with_context(context).create({'type':'invoice',
#                                                            'partner_id':self.partner_id.id
#                                                            ,'is_multi':True,'date':self.date,
#                                                            'to_line':True,'is_line':False})
#             print 'res_id ',res_id
#             self.write({'type':'invoice',
#                                                            'partner_id':self.partner_id.id
#                                                            ,'is_multi':True,'date':self.date,
#                                                            'to_line':True,'is_line':False})

            new_lines=self.env['import.bank.invoice.line']
            for inv in inv_dic:
                invoice=invoice_obj.browse(inv)
                vals = {'type': 'invoice',
                    'partner_id': invoice.partner_id.id,
                    'invoice_id': inv,
#                     'parent_id':res_id.id,#self.id,#context['wizard_ids'][0],
#                     'parent_id':self.id,#self.id,#context['wizard_ids'][0],
                    'amount':inv_dic[inv],
                    'date_invoice':invoice.date_invoice,
                    'number':invoice.number,
                    'residual':invoice.residual,
                    'state':invoice.state,
                    'origin':invoice.origin,
                    'to_line':True
                    }
                
    #                 print "valsvalsvals ",vals
#                 new_line_id = self_line_obj.create(vals)
                
                new_line = self_line_obj.new(vals)
                new_lines += new_line
            self.self_line_ids = new_lines
            self.to_line=True
            self.onchange_date()
#             return True
#             form_res = mod_obj.get_object_reference('mn_account', 'view_import_bank_invoice')
#             form_id = form_res and form_res[1] or False
#             return {
#                 'name': _('Account Transaction Balance Report'),
#                 'view_type': 'form',
#                 'view_mode': 'form',
#                 'res_model': 'import.bank.invoice',
#                 'res_id': res_id.id,
#                 'view_id': False,
#                 'views': [(form_id, 'form')],
#                 'type': 'ir.actions.act_window',
#                 'target':'new'
#             }                 
        
    @api.onchange('move_ids')
    def onchange_move_ids(self):
        self.self_aml_line_ids = False
        domain = []
        currency_dict={}
        if self.move_ids:
            account_id=False
            for aml in self.move_ids:
                if aml.amount_residual_currency!=0 or aml.amount_residual:
                    if account_id and account_id!=aml.account_id.id:
                        raise UserError(_(u"Шижүүлгийн дансууд бүгд ижил байх ёстой шалгана уу!!."))
                    account_id=aml.account_id.id
                    if aml.currency_id:
                        if currency_dict.get(aml.currency_id.id,False):
                            currency_dict[aml.currency_id.id]['debit']+=aml.debit
                            currency_dict[aml.currency_id.id]['credit']+=aml.credit
                            currency_dict[aml.currency_id.id]['amount_currency']+=aml.amount_currency
                            currency_dict[aml.currency_id.id]['residual']+=aml.amount_residual
                            currency_dict[aml.currency_id.id]['residual_currency']+=aml.amount_residual_currency
        #                     currency_dict[aml.currency_id.id]['debit']+=aml.debit
                            currency_dict[aml.currency_id.id]['aml_ids'][0][2].append(aml.id)
                        else:
                            vals={
                                'partner_id':aml.partner_id.id,
                                'parent_id':self.id,
                                'account_id':account_id,
                                'amount':0,
                                'debit':aml.debit,
                                'credit':aml.credit,
                                'amount_currency':aml.amount_currency,
                                'residual':aml.amount_residual,
                                'residual_currency':aml.amount_residual_currency,
        #                         'debit':aml.debit,
                                'rate':0,
                                'aml_ids':[(6,0,[aml.id])],
                                
                                }
                            currency_dict[aml.currency_id.id]=vals
                    else:
                        if currency_dict.get(True,False):
                            currency_dict[True]['debit']+=aml.debit
                            currency_dict[True]['credit']+=aml.credit
                            currency_dict[True]['amount_currency']+=aml.amount_currency
                            currency_dict[True]['residual']+=aml.amount_residual
                            currency_dict[True]['residual_currency']+=aml.amount_residual_currency
        #                     currency_dict[False]['debit']+=aml.debit
                            currency_dict[True]['aml_ids'][0][2].append(aml.id)
                        else:
                            vals={
                                'partner_id':aml.partner_id.id,
                                'account_id':account_id,
    #                             'parent_id':self.id,
                                'amount':0,
                                'debit':aml.debit,
                                'credit':aml.credit,
                                'amount_currency':aml.amount_currency,
                                'residual':aml.amount_residual,
                                'residual_currency':aml.amount_residual_currency,
        #                         'debit':aml.debit,
                                'rate':0,
                                'aml_ids':[(6,0,[aml.id])],
                                
                                }
                            currency_dict[True]=vals        
            lins_ids=[]
            new_lines=self.env['import.bank.account.move.line']
            for curr in currency_dict:
                dic=currency_dict[curr]
                dic.update({'currency_id':curr})
#                 self.self_aml_line_ids.new(dic)
                
                new_line = new_lines.new(dic)
                new_lines += new_line
            self.self_aml_line_ids = new_lines
            self.onchange_date()
            
            
    
    def populate_statement_move(self):
        context=self._context
        context = dict(context or {})
        payment_id = context.get('line_id', False)
        if not payment_id:
            return {'type': 'ir.actions.act_window_close'}
        
        data = self.read()[0]
        line_ids = data['self_aml_line_ids']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}
        
        partner_id = data['partner_id']
        if partner_id:
            partner_id=partner_id[0]
        
        inv_obj = self.env['account.move']
        payment_obj = self.env['account.bank.statement']
        bank_line_obj = self.env['account.bank.statement.line']
        currency_obj = self.env['res.currency']
        move_line_obj = self.env['account.move.line']
        payment = payment_obj.browse(payment_id)
        line_date = payment.date
        
        
        # for each selected move lines
        name=''
        ref=''
#         for line in inv_obj.browse(line_ids):
        amount=0
        import_move_id=False
        import_move_ids=[]
        account_id=False
        amsl_vals = []
        
        #curr rate
        rate=1
        currency_id=False
        for line in self.self_aml_line_ids:
#             if currency_id and line.currency_id.currency_id:#Зөвхөн нэг валют болон МНТ
            if line.currency_id and line.rate:
                rate=line.rate
                currency_id=line.currency_id.id
                break
        for line in self.self_aml_line_ids:
#             partner_id=line.partner_id.id
            part = self.env['res.partner']._find_accounting_partner(line.partner_id)
            partner_id=part.id
            if account_id and account_id!=line.account_id.id:
                raise UserError(_(u"Шижүүлгийн дансууд бүгд ижил байх ёстой шалгана уу!!."))

            account_id=line.account_id.id
            if line.origin:
                name=line.name+' '
            else:
                name=u'Төлөлтүүд '
            amount_currency=0.0
#             print 'in_invoice ',line.type
            #  take the date for computation of currency => use payment date
#             ctx['date'] = line_date
#             amount = line.residual
#             if line.residual > 0.0:
#                 amount = line.residual+line.amount_tax
#             print      "amount :" , amount
            if line.aml_ids:
                for laml in line.aml_ids:
                    move_line =laml
                    import_move_ids.append(move_line.id)
                    if move_line.ref:
                        ref  +=move_line.ref+' '
                    curr_amount=0
                    is_mnt=True
                    if move_line.currency_id:
                        curr_amount=move_line.amount_residual_currency
                        is_mnt=False
                    elif rate>1:
                        curr_amount=move_line.amount_residual/rate#ТӨГ ийн гүйлгээний валютыг засна.
#                     print 'curr_amount ',curr_amount
                        
                    amsl_vals += [(0,0,{
        #                                                        'line_ids': [(6, 0, [line.id])]
                                        'currency_amount':curr_amount,
                                        'import_aml_id':move_line.id,
                                        'is_mnt':is_mnt,
                                        'currency_id':currency_id,
                                            })]
                        
            amount+=line.amount
#             context.update({'invoice_id': line.id})
#         print 'amount ',amount
        bank_line_obj.create({
            'name': name,
            'amount': amount,
#                 'date':time.strftime("%Y-%m-%d"),
            'date': payment.date,
#             'invoice_id': line.id,
            'statement_id':context['active_id'],
#                 'is_payment': True,
#                 'sector_id':department_id,
            'account_id':account_id,    
            'state':'draft',
#             'cashflow_account_id':cashflow_account_id,
            'partner_id':partner_id,
#             'imported_aml_ids':[(6,0,import_move_ids)],
            'import_aml_ids':amsl_vals,
            'date':data['date'],
#                 'import_line_id': import_move_id,
            'ref': ref,
#             'currency_id':currency_id
        })
        return {'type': 'ir.actions.act_window_close'}            
#                 id=self.env['import.bank.account.move.line'].create(dic)
#                 print 'id',id
#                 lins_ids.append(id.id)
#             domain = [('id','in', lins_ids)]
#             print 'domain ',domain
#             return {'domain': {'self_aml_line_ids': domain}}

#     aml_ids = fields.Many2many('account.move.line', 'aml_bank_import_aml_relation', 'move_id', 'line_id', 'Account move line')
#     
#     date = fields.Date('Date', readonly=True)
#     rate = fields.Float('Rate', digits=(16, 4),)
#     number = fields.Char('Number', readonly=True)
#     state = fields.Char('state', readonly=True)
#     origin = fields.Char('Origin', readonly=True)    
    
                    
                    
class ImportBankInvoiceLine(models.TransientModel):
    _name = 'import.bank.invoice.line'
    _description = 'Import Invoice Line'
    
    TYPE_SELECTION = [
#         ('incash','Incash'),
        ('invoice','Invoice'),
        ('move','Account Move')
    ]    
    

    type = fields.Selection(TYPE_SELECTION, string='Type', default='invoice', required=True)
    department_id = fields.Many2one('hr.department', string='Department',)
    partner_id = fields.Many2one('res.partner', string='Receiving Partner',required=True)# readonly=True
#     line_ids = fields.Many2many('account.cost.sharing.line', 'account_cost_sharing_line_relation', 'cost_id', 'line_id', 'Account cost sharing line')
#     inv_ids = fields.Many2many('account.invoice', 'account_invoice_import_relation', 'invoice_id', 'line_id', 'Account invoice')
#     move_ids = fields.Many2many('account.move.line', 'account_move_line_import_relation', 'move_id', 'line_id', 'Account move line')
#     cashflow_account_id = fields.Many2one('account.analytic.account', string='Cashflow Type', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    parent_id = fields.Many2one('import.bank.invoice', string='Parent')
    amount = fields.Float('Amount', digits=(16, 4),)
    
    invoice_id = fields.Many2one('account.move', 'Invoice',)# readonly=True invoice
    
    residual = fields.Float('Amount', digits=(16, 4),)
    date_invoice = fields.Date('Date',)# readonly=True
    number = fields.Char('Number',)# readonly=True
    state = fields.Char('state', )#readonly=True
    origin = fields.Char('Origin', )#readonly=True
    
# 
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        raise UserError(_(u"Харилцагч сольж болохгүй!!."))
        return {'type': 'ir.actions.act_window_close'}

class ImportBankAccountMoveLine(models.TransientModel):
    _name = 'import.bank.account.move.line'
    _description = 'Import Account move Line'
    
    partner_id = fields.Many2one('res.partner', string='Receiving Partner',required=True)
    aml_ids = fields.Many2many('account.move.line', 'aml_bank_import_aml_relation', 'move_id', 'line_id', 'Account move line')
#     cashflow_account_id = fields.Many2one('account.analytic.account', string='Cashflow Type', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    parent_id = fields.Many2one('import.bank.invoice', string='Parent')
    amount = fields.Float('Amount', digits=(16, 4),)
    debit = fields.Float('Debit', digits=(16, 4),)
    credit = fields.Float('Credit', digits=(16, 4),)
    amount_currency = fields.Float('Amount currency', digits=(16, 4),)
    
    invoice_id = fields.Many2one('account.move', 'Invoice', readonly=True)#invoice
    
    residual = fields.Float('Residual', digits=(16, 4),)
    residual_currency = fields.Float('Residual currency', digits=(16, 4),)
    date = fields.Date('Date', readonly=True)
    rate = fields.Float('Rate', digits=(16, 4),)
    number = fields.Char('Number', readonly=True)
    state = fields.Char('state', readonly=True)
    origin = fields.Char('Origin')    
    account_id = fields.Many2one('account.account', string='Account',required=True)
    
    
    def set_amount(self):
        if self.residual_currency:
            if self.currency_id and self.rate:
                self.amount = self.rate*self.residual_currency
        elif self.residual:
            if not self.currency_id and not self.rate:
                self.amount = self.residual
                
    @api.onchange('residual')
    def onchange_residual(self):
        self.set_amount()
        

    @api.onchange('rate')
    def onchange_ratel(self):
        self.set_amount()        
                

    @api.onchange('residual_currency')
    def onchange_residual_currency(self):
        self.set_amount()

    @api.onchange('date')
    def onchange_date(self):
        vals = {}
        if self.date:
            self.rate = self.set_currency()
        self.set_amount()

    
    def set_currency(self):
        if self.date and self.currency_id:
            dates = self.date#datetime.strptime(self.date, '%Y-%m-%d')
            rate_id = self.env['res.currency.rate'].search([('currency_id','=',self.currency_id.id), ('name','<=',self.date)], order='name desc')
            rate = 0
            if rate_id:
                rate = rate_id[0].rate
                rate_date = rate_id[0].name#datetime.strptime(rate_id[0].name, "%Y-%m-%d")
                self.rate_date = rate_date#.date()
            return rate
        
