# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero
from odoo.exceptions import UserError, ValidationError

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class res_branch_category(models.Model):
    _name = 'res.branch.category'
    _description = 'res.branch.category'
    
    name = fields.Char('Name', required=True)
    address = fields.Text('Address', size=252)
    telephone_no = fields.Char("Telephone No")
    company_id =  fields.Many2one('res.company', 'Company', required=True)
    
class res_branch(models.Model):
    _name = 'res.branch'
    _description = 'res.branch'
    
    name = fields.Char('Name', required=True)
    address = fields.Text('Address', size=252)
    telephone_no = fields.Char("Telephone No")
    company_id =  fields.Many2one('res.company', 'Company', required=True)
    user_id = fields.Many2one('res.users', string='Салбарын менежер')
    user_ids = fields.Many2many('res.users', 'res_branch_res_users_rel', id1='branch_id', id2='user_id',string='Users')
    category_id =  fields.Many2one('res.branch.category', 'Category')
    
    main_user_ids = fields.One2many('res.users','branch_id', 'Main Users',)
    

    
    def name_get(self):
        res = []
        for branch in self:
            name = branch.name or ''
            if branch.category_id:
                name = branch.name+' [ ' + branch.category_id.name+' ]'
            res.append((branch.id, name))
        return res

class res_users(models.Model):
    _inherit = 'res.users'

    
    branch_id = fields.Many2one('res.branch', 'Branch', required=True)
    branch_ids = fields.Many2many('res.branch', 'res_branch_res_users_rel', id1='user_id', id2='branch_id',string='Branch')
    cash_journal_id = fields.Many2one('account.journal', string='Cash journal', domain=[('type', 'in', ['bank','cash'])])
    


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _get_purchase_default_branch(self):
        user_pool = self.env['res.users']
        branch_id = user_pool.browse(self.env.user.id).branch_id.id
        return branch_id


    branch_id = fields.Many2one('res.branch', 'Branch', default = _get_purchase_default_branch)    


    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        from override purchase
        '''
        res = super(purchase_order, self).action_view_invoice()
        res['context'].update({'default_branch_id':self.branch_id.id})
        return res


class account_journal(models.Model):
    _inherit = 'account.journal'

    @api.model
    def _get_joural_default_branch(self):
        user_pool = self.env['res.users']
        branch_id = user_pool.browse(self.env.user.id).branch_id.id
        return branch_id


    branch_id = fields.Many2one('res.branch', 'Branch', default = _get_joural_default_branch)    
   


# class account_invoice(models.Model):
#     _inherit = 'account.invoice'
# 
#     @api.model
#     def _get_invoice_default_branch(self):
#         user_pool = self.env['res.users']
#         branch_id = user_pool.browse(self.env.user.id).branch_id.id or False
#         return branch_id
# 
#     
#     branch_id = fields.Many2one('res.branch', 'Branch', required=True, default = _get_invoice_default_branch)
#     
# 
#    
#     
#     def invoice_pay_customer(self, cr, uid, ids, context=None):
#         result = super(account_invoice, self).invoice_pay_customer(cr, uid, ids, context=context)
#         inv = self.pool.get('account.invoice').browse(cr, uid, ids[0], context=context)
#         sale_order_id = inv.sale_order_id and inv.sale_order_id.id or False
#         if sale_order_id:
#             result.get('context').update({'default_branch_id': inv.branch_id.id, 'default_sale_order_id':sale_order_id})
#         else:
#             result.get('context').update({'default_branch_id': inv.branch_id.id})
#         return result
# 
#     # Load all unsold PO lines
#     @api.onchange('purchase_id')
#     def purchase_order_change(self):
#         if not self.purchase_id:
#             return {}
#         if not self.partner_id:
#             self.partner_id = self.purchase_id.partner_id.id
# 
#         new_lines = self.env['account.invoice.line']
#         line_list=[]
#         line_dict={}
#         for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
#             data = self._prepare_invoice_line_from_po_line(line)
#             if not self.partner_id.group_invoice:
#                 line_list.append(data)
#             else:
#                 if line_dict.has_key(data['account_id']):
#                     line_dict[data['account_id']]['price_unit']+=round(data['price_unit'],2)*round(data['quantity'],2)
#                 else:
#                     line_dict[data['account_id']]={
#                                                     'name':self.purchase_id.name,
#                                                     'origin':'',
#                                                    'price_unit':round(data['price_unit'],2)*round(data['quantity'],2),
#                                                    'quantity':1.0,
#                                                    'discount':0.0,
#                                                    'uom_id':1,
#                                                    'product_id':False,
#                                                    'branch_id':data['branch_id'],
#                                                    }
#         if not self.partner_id.group_invoice:
#             for d in line_list:
#                 new_line = new_lines.new(d)
#                 new_line._set_additional_fields(self)
#                 new_lines += new_line
#         else:
#             for d in line_dict:
#                 line_dict[d].update({'account_id':d})
#                 new_line = new_lines.new(line_dict[d])
#                 new_line._set_additional_fields(self)
#                 new_lines += new_line
#                 
#         self.invoice_line_ids += new_lines
#         self.payment_term_id = self.purchase_id.payment_term_id
#         self.env.context = dict(self.env.context, from_purchase_order_change=True)
#         self.purchase_id = False
#         return {}

# class account_voucher(models.Model):
# 
#     _inherit = 'account.voucher'
# 
#     @api.model
#     def _get_voucher_default_branch(self):
#         user_pool = self.env['res.users']
#         branch_id = user_pool.browse(self.env.uid).branch_id.id  or False
#         return branch_id
# 
#     branch_id = fields.Many2one('res.branch', 'Branch', required=True, default = _get_voucher_default_branch)







   

    



class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.model
    def create(self ,val):

#         if val.get('journal_id'):
#             user_pool =  self.env['res.users']
#             val.update({'branch_id': self.journal_id.branch_id.id})
        if self._context.get('active_ids',False) and self._context.get('active_model','') =='account.invoice':
            invoice = self.env['account.invoice'].browse(self._context['active_ids'][0])
            if invoice and invoice.branch_id:
                val.update({'branch_id': invoice.branch_id.id})
                
        return super(AccountPayment , self ).create(val)

    branch_id = fields.Many2one('res.branch', string='Branch', )

    def _get_counterpart_move_line_vals(self, invoice=False):
        
        if self.payment_type == 'transfer':
            name = self.name
        else:
            name = ''
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    name += _("Customer Payment")
                elif self.payment_type == 'outbound':
                    name += _("Customer Refund")
            elif self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    name += _("Vendor Refund")
                elif self.payment_type == 'outbound':
                    name += _("Vendor Payment")
            if invoice:
                name += ': '
                for inv in invoice:
                    if inv.move_id:
                        name += inv.number + ', '
                name = name[:len(name)-2] 
        branch_id=self.branch_id.id
        if not branch_id:
            branch_id = self.journal_id.branch_id.id
        return {
            'name': name,
            'account_id': self.destination_account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
            'payment_id': self.id,
            'branch_id' : branch_id,
        }

    def _get_liquidity_move_line_vals(self, amount):
        #Мөнгөн хөрөнгийн дансны бичилт
        user_pool =  self.env['res.users']
        res = super(AccountPayment, self)._get_liquidity_move_line_vals(amount)
        res.update({'branch_id':self.journal_id.branch_id.id })
        return res


    @api.model
    def default_get(self, default_fields):
        rec = super(AccountPayment, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids).filtered(lambda move: move.is_invoice(include_receipts=True))

        # Check all invoices are open
        if not invoices or any(invoice.state != 'posted' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        # Check if, in batch payments, there are not negative invoices and positive invoices
        dtype = invoices[0].type
        for inv in invoices[1:]:
            if inv.type != dtype:
                if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
                        (dtype == 'in_invoice' and inv.type == 'in_refund')):
                    raise UserError(_("You cannot register payments for vendor bills and supplier refunds at the same time."))
                if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
                        (dtype == 'out_invoice' and inv.type == 'out_refund')):
                    raise UserError(_("You cannot register payments for customer invoices and credit notes at the same time."))

        amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id, rec.get('payment_date') or fields.Date.today())

        user_pool = self.env['res.users']
        user = user_pool.browse(self.env.uid)
        journal_id = user.cash_journal_id.id  or False

        rec.update({
            'currency_id': invoices[0].currency_id.id,
            'amount': abs(amount),
            'payment_type': 'inbound' if amount > 0 else 'outbound',
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
            'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
            'invoice_ids': [(6, 0, invoices.ids)],
            'journal_id':journal_id
        })
        return rec


    @api.onchange('amount', 'currency_id')
    def _onchange_amount(self):
        """Анхны утга валютаар авахгүй байх
        """
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        domain_on_types = [('type', 'in', list(journal_types))]
        if self.invoice_ids:
            domain_on_types.append(('company_id', '=', self.invoice_ids[0].company_id.id))
        if self.journal_id.type not in journal_types or (self.invoice_ids and self.journal_id.company_id != self.invoice_ids[0].company_id):
            if self.env.user.cash_journal_id:
                self.journal_id = self.env.user.cash_journal_id
            else:
                domain_on_types.append(('currency_id','=',False))
                self.journal_id = self.env['account.journal'].search(domain_on_types, limit=1)
        return {'domain': {'journal_id': jrnl_filters['domain'] + domain_on_types}}

# class account_invoice_refund(models.TransientModel):
#    
#     _inherit = 'account.invoice.refund'
# 
#     @api.model
#     def _get_invoice_refund_default_branch(self):
#         if self._context.get('active_id'):
#             ids = self._context.get('active_id')
#             user_pool = self.env['account.invoice']
#             branch_id = user_pool.browse(ids).branch_id and user_pool.browse(ids).branch_id.id or False
#             return branch_id
# 
# 
#     branch_id = fields.Many2one('res.branch', 'Branch', default = _get_invoice_refund_default_branch , required=True)
# 
# 
# 
# class account_invoice_line(models.Model):
# 
#     _inherit = 'account.invoice.line'
# 
#     branch_id  = fields.Many2one('res.branch', 'Branch')
# 
#     
#     def asset_create(self):
#         if self.asset_category_id:
#             vals = {
#                 'name': self.name,
#                 'code': self.invoice_id.number or False,
#                 'category_id': self.asset_category_id.id,
#                 'value': self.price_subtotal_signed,
#                 'partner_id': self.invoice_id.partner_id.id,
#                 'company_id': self.invoice_id.company_id.id,
#                 'currency_id': self.invoice_id.company_currency_id.id,
#                 'date': self.invoice_id.date_invoice,
#                 'invoice_id': self.invoice_id.id,
# #                 'value': self.price_subtotal/self.quantity,
#                 'price_unit':float(self.price_subtotal/self.quantity),
#                 'qty':float(self.quantity),
#                 'branch_id': self.invoice_id.branch_id and self.invoice_id.branch_id.id or False
#             }
#             changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
#             vals.update(changed_vals['value'])
#             asset = self.env['account.asset.asset'].create(vals)
#             if self.asset_category_id.open_asset:
#                 asset.validate()
#         return True


class account_bank_statement(models.Model):

    _inherit = 'account.bank.statement'

    @api.model
    def _get_bank_statement_default_branch(self):
        user_pool = self.env['res.users']
        branch_id = user_pool.browse(self.env.uid).branch_id.id  or False
        return branch_id


    branch_id = fields.Many2one('res.branch', 'Branch', default=_get_bank_statement_default_branch )



class account_bank_statement_line(models.Model):


    _inherit = 'account.bank.statement.line'

    @api.model
    def _get_bank_statement_default_branch(self):
        user_pool = self.env['res.users']
        branch_id = user_pool.browse(self.env.uid).branch_id.id  or False
        return branch_id



    branch_id = fields.Many2one('res.branch', 'Branch', related='statement_id.branch_id', default=_get_bank_statement_default_branch ,)
    tax_id = fields.Many2one('account.tax', 'Tax')
    branch_res_id = fields.Many2one('res.branch', 'Branch')
# 
#     def process_reconciliation(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
#         """ Match statement lines with existing payments (eg. checks) and/or payables/receivables (eg. invoices and credit notes) and/or new move lines (eg. write-offs).
#             If any new journal item needs to be created (via new_aml_dicts or counterpart_aml_dicts), a new journal entry will be created and will contain those
#             items, as well as a journal item for the bank statement line.
#             Finally, mark the statement line as reconciled by putting the matched moves ids in the column journal_entry_ids.
# 
#             :param self: browse collection of records that are supposed to have no accounting entries already linked.
#             :param (list of dicts) counterpart_aml_dicts: move lines to create to reconcile with existing payables/receivables.
#                 The expected keys are :
#                 - 'name'
#                 - 'debit'
#                 - 'credit'
#                 - 'move_line'
#                     # The move line to reconcile (partially if specified debit/credit is lower than move line's credit/debit)
# 
#             :param (list of recordsets) payment_aml_rec: recordset move lines representing existing payments (which are already fully reconciled)
# 
#             :param (list of dicts) new_aml_dicts: move lines to create. The expected keys are :
#                 - 'name'
#                 - 'debit'
#                 - 'credit'
#                 - 'account_id'
#                 - (optional) 'tax_ids'
#                 - (optional) Other account.move.line fields like analytic_account_id or analytics_id
#                 - (optional) 'reconcile_model_id'
# 
#             :returns: The journal entries with which the transaction was matched. If there was at least an entry in counterpart_aml_dicts or new_aml_dicts, this list contains
#                 the move created by the reconciliation, containing entries for the statement.line (1), the counterpart move lines (0..*) and the new move lines (0..*).
#             шууд батлахад fast_counterpart_creation дотор шууд ажил гүйлгээ хийдэг болсон тул энд үйлдэлгүй
#         """
#         print ('22222')
#         
#         payable_account_type = self.env.ref('account.data_account_type_payable')
#         receivable_account_type = self.env.ref('account.data_account_type_receivable')
#         suspense_moves_mode = self._context.get('suspense_moves_mode')
#         counterpart_aml_dicts = counterpart_aml_dicts or []
#         payment_aml_rec = payment_aml_rec or self.env['account.move.line']
#         new_aml_dicts = new_aml_dicts or []
# 
#         aml_obj = self.env['account.move.line']
# 
#         company_currency = self.journal_id.company_id.currency_id
#         statement_currency = self.journal_id.currency_id or company_currency
#         st_line_currency = self.currency_id or statement_currency
# 
#         counterpart_moves = self.env['account.move']
# 
#         # Check and prepare received data
#         if any(rec.statement_id for rec in payment_aml_rec):
#             raise UserError(_('A selected move line was already reconciled.'))
#         for aml_dict in counterpart_aml_dicts:
#             if aml_dict['move_line'].reconciled and not suspense_moves_mode:
#                 raise UserError(_('A selected move line was already reconciled.'))
#             if isinstance(aml_dict['move_line'], int):
#                 aml_dict['move_line'] = aml_obj.browse(aml_dict['move_line'])
# 
#         account_types = self.env['account.account.type']
#         for aml_dict in (counterpart_aml_dicts + new_aml_dicts):
#             if aml_dict.get('tax_ids') and isinstance(aml_dict['tax_ids'][0], int):
#                 # Transform the value in the format required for One2many and Many2many fields
#                 aml_dict['tax_ids'] = [(4, id, None) for id in aml_dict['tax_ids']]
# 
#             user_type_id = self.env['account.account'].browse(aml_dict.get('account_id')).user_type_id
#             if user_type_id in [payable_account_type, receivable_account_type] and user_type_id not in account_types:
#                 account_types |= user_type_id
#         if suspense_moves_mode:
#             if any(not line.journal_entry_ids for line in self):
#                 raise UserError(_('Some selected statement line were not already reconciled with an account move.'))
#         else:
#             if any(line.journal_entry_ids for line in self):
#                 raise UserError(_('A selected statement line was already reconciled with an account move.'))
# 
#         # Fully reconciled moves are just linked to the bank statement
#         total = self.amount
#         currency = self.currency_id or statement_currency
#         for aml_rec in payment_aml_rec:
#             balance = aml_rec.amount_currency if aml_rec.currency_id else aml_rec.balance
#             aml_currency = aml_rec.currency_id or aml_rec.company_currency_id
#             total -= aml_currency._convert(balance, currency, aml_rec.company_id, aml_rec.date)
#             aml_rec.with_context(check_move_validity=False).write({'statement_line_id': self.id})
#             counterpart_moves = (counterpart_moves | aml_rec.move_id)
#             if aml_rec.journal_id.post_at == 'bank_rec' and aml_rec.payment_id and aml_rec.move_id.state == 'draft':
#                 # In case the journal is set to only post payments when performing bank
#                 # reconciliation, we modify its date and post it.
#                 aml_rec.move_id.date = self.date
#                 aml_rec.payment_id.payment_date = self.date
#                 aml_rec.move_id.post()
#                 # We check the paid status of the invoices reconciled with this payment
#                 for invoice in aml_rec.payment_id.reconciled_invoice_ids:
#                     self._check_invoice_state(invoice)
# 
#         # Create move line(s). Either matching an existing journal entry (eg. invoice), in which
#         # case we reconcile the existing and the new move lines together, or being a write-off.
#         print ('new_aml_dicts ',new_aml_dicts)
#         print ('counterpart_aml_dicts ',counterpart_aml_dicts)
#         if counterpart_aml_dicts or new_aml_dicts:
# 
#             # Create the move
#             self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
#             move_vals = self._prepare_reconciliation_move(self.statement_id.name)
#             if suspense_moves_mode:
#                 self.button_cancel_reconciliation()
#             move = self.env['account.move'].with_context(default_journal_id=move_vals['journal_id']).create(move_vals)
#             counterpart_moves = (counterpart_moves | move)
# 
#             # Create The payment
#             payment = self.env['account.payment']
#             partner_id = self.partner_id or (aml_dict.get('move_line') and aml_dict['move_line'].partner_id) or self.env['res.partner']
#             if abs(total)>0.00001:
#                 payment_vals = self._prepare_payment_vals(total)
#                 if not payment_vals['partner_id']:
#                     payment_vals['partner_id'] = partner_id.id
#                 if payment_vals['partner_id'] and len(account_types) == 1:
#                     payment_vals['partner_type'] = 'customer' if account_types == receivable_account_type else 'supplier'
#                 #darmaa
#                 if self.import_line_id.move_id:
#                     payment_vals.update({
#                             'invoice_ids': [(6, 0, self.import_line_id.move_id.ids)],
#                         })
# #                print 'self.import_line_ids-----: ',self.import_line_ids
#                 if self.import_line_ids:
#                     lines=[]
#                     for l in self.import_line_ids:
#                         if l.import_inv_id:
#                             lines.append(l.import_inv_id.id)
#                     # print 'lines ',lines
#                     payment_vals.update({
#                                 'invoice_ids': [(6, 0, lines)],
#                                 })
#                 #олон гүйлгээ импортолсон бол нэхэмжл                
#                 #darmaa
#                 payment = payment.create(payment_vals)
# 
#             # Complete dicts to create both counterpart move lines and write-offs
#             to_create = (counterpart_aml_dicts + new_aml_dicts)
#             date = self.date or fields.Date.today()
#             for aml_dict in to_create:
#                 aml_dict['move_id'] = move.id
#                 aml_dict['partner_id'] = self.partner_id.id
#                 aml_dict['statement_line_id'] = self.id
#                 self._prepare_move_line_for_currency(aml_dict, date)
# 
#             new_aml_id=False
#             # Create write-offs
#             for aml_dict in new_aml_dicts:
#                 aml_dict['payment_id'] = payment and payment.id or False
# #                 aml_obj.with_context(check_move_validity=False).create(aml_dict)
#                 new_aml_id = aml_obj.with_context(check_move_validity=False).create(aml_dict)
# 
#             # Create counterpart move lines and reconcile them
#             for aml_dict in counterpart_aml_dicts:
#                 if aml_dict['move_line'].payment_id:
#                     aml_dict['move_line'].write({'statement_line_id': self.id})
#                 if aml_dict['move_line'].partner_id.id:
#                     aml_dict['partner_id'] = aml_dict['move_line'].partner_id.id
#                 aml_dict['account_id'] = aml_dict['move_line'].account_id.id
#                 aml_dict['payment_id'] = payment and payment.id or False
# 
#                 counterpart_move_line = aml_dict.pop('move_line')
#                 new_aml = aml_obj.with_context(check_move_validity=False).create(aml_dict)
# 
#                 (new_aml | counterpart_move_line).reconcile()
# 
#                 self._check_invoice_state(counterpart_move_line.move_id)
# 
#             # new_aml_id Авлага өглөг төлөлт
#             #darmaa
#             if self.import_line_id and new_aml_id:
# #                 print 'new_aml_dicts | self.import_line_id------111 ',new_aml_id | self.import_line_id
#                 (new_aml_id | self.import_line_id).reconcile()
#             #Олон нэхэмжлэх импортлосон бол бүгдийг нь хугацааны дарааллаар тулгах
#             if self.import_line_ids  and new_aml_id:
#                 imort_lines=False
#                 for l in self.import_line_ids:
#                     if l.import_inv_id:
#               #          print 'l.import_inv_id.move_id ',l.import_inv_id.move_id
#                         if l.import_inv_id.move_id:
# #                             imort_lines = [aml for aml in l.import_inv_id.move_id.line_ids if aml.account_id.internal_type in ('receivable', 'payable')]
#                             for  aml in l.import_inv_id.move_id.line_ids:
#                                 if aml.account_id.internal_type in ('receivable', 'payable'):
#                                     if not imort_lines:
#                                         imort_lines=aml
#                                     else:
#                                         imort_lines+=aml
#                 (new_aml_id | imort_lines).reconcile()
#             print ('self.import_aml_ids ',self.import_aml_ids)
#             print ('new_aml_id ',new_aml_id)
#             if self.import_aml_ids  and new_aml_id:
#                 imort_lines=False
#                 for aml in self.import_aml_ids:
#                     if not imort_lines:
#                         imort_lines=aml
#                     else:
#                         imort_lines+=aml
#                 print ('imort_lines ',imort_lines)
#                 (new_aml_id | imort_lines).reconcile()    
#             #end darmaa            
#             # Balance the move
#             st_line_amount = -sum([x.balance for x in move.line_ids])
#             aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
#             aml_dict['payment_id'] = payment and payment.id or False
#             aml_obj.with_context(check_move_validity=False).create(aml_dict)
# 
#             move.post()
#             #record the move name on the statement line to be able to retrieve it in case of unreconciliation
#             self.write({'move_name': move.name})
#             payment and payment.write({'payment_reference': move.name})
#         elif self.move_name:
#             raise UserError(_('Operation not allowed. Since your statement line already received a number (%s), you cannot reconcile it entirely with existing journal entries otherwise it would make a gap in the numbering. You should book an entry and make a regular revert of it in case you want to cancel it.') % (self.move_name))
# 
#         #create the res.partner.bank if needed
#         if self.account_number and self.partner_id and not self.bank_account_id:
#             # Search bank account without partner to handle the case the res.partner.bank already exists but is set
#             # on a different partner.
#             bank_account = self.env['res.partner.bank'].search([('acc_number', '=', self.account_number)])
#             if not bank_account:
#                 bank_account = self.env['res.partner.bank'].create({
#                     'acc_number': self.account_number, 'partner_id': self.partner_id.id
#                 })
#             self.bank_account_id = bank_account
# 
#         counterpart_moves._check_balanced()
#         return counterpart_moves
    
    def fast_counterpart_creation(self):
        """This function is called when confirming a bank statement and will allow to automatically process lines without
        going in the bank reconciliation widget. By setting an account_id on bank statement lines, it will create a journal
        entry using that account to counterpart the bank account
        """
        payment_list = []
        move_list = []
        account_type_receivable = self.env.ref('account.data_account_type_receivable')
        already_done_stmt_line_ids = [a['statement_line_id'][0] for a in self.env['account.move.line'].read_group([('statement_line_id', 'in', self.ids)], ['statement_line_id'], ['statement_line_id'])]
#         print ('already_done_stmt_line_ids ',already_done_stmt_line_ids)
        managed_st_line = []
        aml_obj = self.env['account.move.line']
#         aml_obj = self.env['account.move.line']
        new_aml_id=False
        move_vals=False
        move_ids=[]
        branch_id=False
        
        for st_line in self:
            # Technical functionality to automatically reconcile by creating a new move line
            if st_line.branch_res_id:
                branch_id=st_line.branch_res_id.id
            elif st_line.branch_id:
                 branch_id=st_line.branch_id.id
            if self.tax_id:#Татвартай бол
                
                if st_line.account_id and not st_line.id in already_done_stmt_line_ids:
                        if self.amount<0:
                            tax_all = self.tax_id.compute_all(abs(self.amount))
                            data = [{'partner_id': self.partner_id and self.partner_id.id or False, 
                                     'counterpart_aml_dicts': [], 
                                     'payment_aml_ids': [], 
                                     'new_aml_dicts': [{'name': self.name,#'POS/00342 дотоод шилжүүлэг гарах Эрдэнэт салбар', 
                                                        'debit': tax_all['total_excluded'],#520181.82,
                                                        'credit': 0,'branch_id':branch_id,  'analytic_tag_ids': [[6, None, []]], 'account_id': self.account_id.id,'analytic_account_id':st_line.analytic_account_id and st_line.analytic_account_id.id or False, 
                                                        'tax_ids': [[6, None, [self.tax_id.id]]]},
                                                        {'name': self.name,#'POS/00342 дотоод шилжүүлэг гарах Эрдэнэт салбар НӨАТ', 
                                                         'debit': tax_all['taxes'][0]['amount'], 
                                                         'credit': 0, 'branch_id':branch_id, 'analytic_tag_ids': 
                                                         [[6, None, []]], 'account_id': tax_all['taxes'][0]['account_id'], 
                                                         'tax_repartition_line_id': tax_all['taxes'][0]['tax_repartition_line_id']}],'to_check': False}
                                    ]
                        else:
                            tax_all = self.tax_id.compute_all(abs(self.amount))
                            data = [{'partner_id': self.partner_id and self.partner_id.id or False, 
                                     'counterpart_aml_dicts': [], 
                                     'payment_aml_ids': [], 
                                     'new_aml_dicts': [{'name': self.name,#'POS/00342 дотоод шилжүүлэг гарах Эрдэнэт салбар', 
                                                        'credit': tax_all['total_excluded'],#520181.82,
                                                        'debit': 0,'branch_id':branch_id,  'analytic_tag_ids': [[6, None, []]], 'account_id': self.account_id.id,'analytic_account_id':st_line.analytic_account_id and st_line.analytic_account_id.id or False, 
                                                        'tax_ids': [[6, None, [self.tax_id.id]]]},
                                                        {'name': self.name,#'POS/00342 дотоод шилжүүлэг гарах Эрдэнэт салбар НӨАТ', 
                                                         'credit': tax_all['taxes'][0]['amount'], 
                                                         'debit': 0, 'branch_id':branch_id, 'analytic_tag_ids': 
                                                         [[6, None, []]], 'account_id': tax_all['taxes'][0]['account_id'], 
                                                         'tax_repartition_line_id': tax_all['taxes'][0]['tax_repartition_line_id']}],'to_check': False}
                                    ]                
                        reconciliation_obj = self.env['account.reconciliation.widget']
                        reconciliation_obj.process_bank_statement_line([self.id],data)
                        return True  
            else:          
                if st_line.account_id and not st_line.id in already_done_stmt_line_ids:
                    move_vals = st_line._prepare_reconciliation_move(st_line.statement_id.name)
                    move_ids = self.env['account.move'].create(move_vals)
    #                 print ('move_ids ',move_ids)
                    managed_st_line.append(st_line.id)
                    # Create payment vals
                    total = st_line.amount
                    payment_methods = (total > 0) and st_line.journal_id.inbound_payment_method_ids or st_line.journal_id.outbound_payment_method_ids
                    currency = st_line.journal_id.currency_id or st_line.company_id.currency_id
                    partner_type = 'customer' if st_line.account_id.user_type_id == account_type_receivable else 'supplier'
                    payment_list.append({
                        'payment_method_id': payment_methods and payment_methods[0].id or False,
                        'payment_type': total > 0 and 'inbound' or 'outbound',
                        'partner_id': st_line.partner_id.id,
                        'partner_type': partner_type,
                        'journal_id': st_line.statement_id.journal_id.id,
                        'payment_date': st_line.date,
                        'state': 'reconciled',
                        'currency_id': currency.id,
                        'amount': abs(total),
                        'communication': st_line._get_communication(payment_methods[0] if payment_methods else False),
                        'name': st_line.statement_id.name or _("Bank Statement %s") % st_line.date,
                        'branch_id':branch_id
                    })
    
                    # Create move and move line vals
    #                 move_vals = st_line._prepare_reconciliation_move(st_line.statement_id.name)
                    #харьцсан дансны
                    aml_dict = {
                        'name': st_line.name,
                        'debit': st_line.amount < 0 and -st_line.amount or 0.0,
                        'credit': st_line.amount > 0 and st_line.amount or 0.0,
                        'account_id': st_line.account_id.id,
                        'partner_id': st_line.partner_id.id,
                        'statement_line_id': st_line.id,
                        'move_id':move_ids.id,
                        'branch_id':branch_id
                    }
                    if st_line.analytic_account_id:
                        aml_dict.update({'analytic_account_id':st_line.analytic_account_id.id})
                    if self.tax_id:
                        # Transform the value in the format required for One2many and Many2many fields
                        aml_dict['tax_ids'] = [(4, self.tax_id.id, None)]
                    
    #                 print ('aml_dict ',aml_dict)
                    st_line._prepare_move_line_for_currency(aml_dict, st_line.date or fields.Date.context_today())
                    new_aml_id = aml_obj.with_context(check_move_validity=False).create(aml_dict)
    #                 move_vals['line_ids'] = [(0, 0, aml_dict)]
    #                 balance_line = self._prepare_reconciliation_move_line(
    #                     move_vals, -aml_dict['debit'] if st_line.amount < 0 else aml_dict['credit'])
    #                 move_vals['line_ids'].append((0, 0, balance_line))
    #                 print ('move_vals222 ',move_vals)
    #                 move_list.append(move_vals)
    
                    #Мөнгөн хөрөнгийн
    #                 balance_line = self._prepare_reconciliation_move_line_mw(
    #                     move_ids, -aml_dict['debit'] if st_line.amount < 0 else aml_dict['credit'])
    #                 aml_obj.with_context(check_move_validity=False).create(balance_line)
                    aml_dict = self._prepare_reconciliation_move_line(move_ids, -aml_dict['debit'] if st_line.amount < 0 else aml_dict['credit'])
        #             aml_dict Мөнгөн хөрөнгийн дансны гүйлгээ
    #                 aml_dict['payment_id'] = payment and payment.id or False
                    aml_dict['move_id'] = move_ids.id
                    aml_obj.with_context(check_move_validity=False).create(aml_dict)
                    
                    if self.import_aml_ids  and new_aml_id:
                        imort_lines=False
        #                 curr олох
                        curr=False
        #                 for aml in self.imported_aml_ids:
                        for imp in self.import_aml_ids:
                            if imp.import_aml_id:
                                if imp.import_aml_id.currency_id:
                                    curr=imp.import_aml_id.currency_id
                                    break
    
                        invoice_ids=[]
                        for imp in self.import_aml_ids:
        #                 for aml in self.imported_aml_ids:
                            if imp.import_aml_id:
                                aml=imp.import_aml_id
                                if not imort_lines:
                                    imort_lines=aml
                                else:
                                    imort_lines+=aml
                                    #curr bsl deer currency_id nemj uzeh teri jishij bolno
                                if not aml.currency_id and curr != self.company_id.currency_id:
                                    aml.with_context(allow_amount_currency=True, check_move_validity=False).write({
                                        'amount_currency': imp.currency_amount,#self.company_id.currency_id.with_context(date=credit_aml.date).compute(aml.balance, self.currency_id),
                                        'currency_id': curr and curr.id or False})
                                invoice_ids.append(imp.import_aml_id.move_id.id)
    #                         payment_list[0].update({
    #                             'invoice_ids':self.import_aml_ids.ids
    #                             })
                                    
                            payment_list[0].update({
    #                             'invoice_ids':self.import_aml_ids.ids
                                'invoice_ids':invoice_ids
                                })
                        print ('new_aml_id ',new_aml_id)
                        print ('imort_lines ',imort_lines)
                        (new_aml_id | imort_lines).reconcile()                  
                
#             if self.import_aml_ids  and new_aml_id:
#                 imort_lines=False
#                 for aml in self.import_aml_ids:
#                     if not imort_lines:
#                         imort_lines=aml
#                     else:
#                         imort_lines+=aml
#                 print ('imort_lines111 ',imort_lines)
#                 (new_aml_id | imort_lines).reconcile()    
        # Creates
#         print ('payment_list ',payment_list)
        payment_ids = self.env['account.payment'].create(payment_list)
        for m in move_ids:
#             print ('mmm ',m)
            for aml in m.line_ids:
                print ('aml ',aml)
                aml.write({'payment_id':payment_ids.id})
                
        for payment_id, move_vals in zip(payment_ids, move_list):
#             print ('aaaaaa ',move_vals['line_ids'])
            for line in move_vals['line_ids']:
                line[2]['payment_id'] = payment_id.id
#         move_ids = self.env['account.move'].create(move_list)
#         move_ids.post() #You need to add a line before posting. geed bn

        for move, st_line, payment in zip(move_ids, self.browse(managed_st_line), payment_ids):
            st_line.write({'move_name': move.name})
            payment.write({'payment_reference': move.name})
                
        

    def _prepare_reconciliation_move_line(self, move, amount):
        """ Prepare the dict of values to balance the move.

            :param recordset move: the account.move to link the move line
            :param float amount: the amount of transaction that wasn't already reconciled
        """
        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency
        amount_currency = False
        st_line_currency_rate = self.currency_id and (self.amount_currency / self.amount) or False
        # We have several use case here to compure the currency and amount currency of counterpart line to balance the move:
        if st_line_currency != company_currency and st_line_currency == statement_currency:
            # company in currency A, statement in currency B and transaction in currency B
            # counterpart line must have currency B and correct amount is inverse of already existing lines
            amount_currency = -sum([x.amount_currency for x in move.line_ids])
        elif st_line_currency != company_currency and statement_currency == company_currency:
            # company in currency A, statement in currency A and transaction in currency B
            # counterpart line must have currency B and correct amount is inverse of already existing lines
            amount_currency = -sum([x.amount_currency for x in move.line_ids])
        elif st_line_currency != company_currency and st_line_currency != statement_currency:
            # company in currency A, statement in currency B and transaction in currency C
            # counterpart line must have currency B and use rate between B and C to compute correct amount
            amount_currency = -sum([x.amount_currency for x in move.line_ids])/st_line_currency_rate
        elif st_line_currency == company_currency and statement_currency != company_currency:
            # company in currency A, statement in currency B and transaction in currency A
            # counterpart line must have currency B and amount is computed using the rate between A and B
            amount_currency = amount/st_line_currency_rate
        
        # last case is company in currency A, statement in currency A and transaction in currency A
        # and in this case counterpart line does not need any second currency nor amount_currency
        branch_id=False
        if self.branch_res_id:
            branch_id=self.branch_res_id.id
        elif self.branch_id:
            branch_id=self.branch_id.id
        ret_vals={
            'name': self.name,
            'move_id': move.id,
            'partner_id': self.partner_id and self.partner_id.id or False,
            'account_id': amount >= 0 \
                and self.statement_id.journal_id.default_credit_account_id.id \
                or self.statement_id.journal_id.default_debit_account_id.id,
            'credit': amount < 0 and -amount or 0.0,
            'debit': amount > 0 and amount or 0.0,
            'statement_line_id': self.id,
            'currency_id': statement_currency != company_currency and statement_currency.id or (st_line_currency != company_currency and st_line_currency.id or False),
            'amount_currency': amount_currency,
            'branch_id':branch_id,
        }
        if self.analytic_account_id:
            ret_vals.update({'analytic_account_id':self.analytic_account_id.id})
        return ret_vals
#                         
#     def process_reconciliation_old(self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None):
# 
#         """ Match statement lines with existing payments (eg. checks) and/or payables/receivables (eg. invoices and refunds) and/or new move lines (eg. write-offs).
#             If any new journal item needs to be created (via new_aml_dicts or counterpart_aml_dicts), a new journal entry will be created and will contain those
#             items, as well as a journal item for the bank statement line.
#             Finally, mark the statement line as reconciled by putting the matched moves ids in the column journal_entry_ids.
#             new_aml_dicts Данс сонгосон мөрийн мөнгөтэй харьцаж буй гүйлгээ
#         """
#         print ('counterpart_aml_dicts ',str(counterpart_aml_dicts)+' , '+str(new_aml_dicts))
#         counterpart_aml_dicts = counterpart_aml_dicts or []
#         payment_aml_rec = payment_aml_rec or self.env['account.move.line']
#         new_aml_dicts = new_aml_dicts or []
#         aml_obj = self.env['account.move.line']
# 
#         company_currency = self.journal_id.company_id.currency_id
#         statement_currency = self.journal_id.currency_id or company_currency
#         st_line_currency = self.currency_id or statement_currency
# 
#         counterpart_moves = self.env['account.move']
# #         if self.import_line_id and not counterpart_aml_dicts:
# #             counterpart_aml_dicts = [{'move_line':self.import_line_id,'credit':self.import_line_id.credit,\
# #                                      'debit':self.import_line_id.debit,'name':self.import_line_id.name}]
#         # Check and prepare received data
#         if any(rec.statement_id for rec in payment_aml_rec):
#             raise UserError(_('A selected move line was already reconciled.'))
#         for aml_dict in counterpart_aml_dicts:
#             if aml_dict['move_line'].reconciled:
#                 raise UserError(_('A selected move line was already reconciled.'))
#             if isinstance(aml_dict['move_line'], (int, long)):
#                 aml_dict['move_line'] = aml_obj.browse(aml_dict['move_line'])
#         for aml_dict in (counterpart_aml_dicts + new_aml_dicts):
#             if aml_dict.get('tax_ids') and aml_dict['tax_ids'] and isinstance(aml_dict['tax_ids'][0], (int, long)):
#                 # Transform the value in the format required for One2many and Many2many fields
#                 aml_dict['tax_ids'] = map(lambda id: (4, id, None), aml_dict['tax_ids'])
#         # Fully reconciled moves are just linked to the bank statement
#         total = self.amount
#         for aml_rec in payment_aml_rec:
#             total -= aml_rec.debit-aml_rec.credit
#             aml_rec.write({'branch_id': self.branch_id.id})
# 
#             aml_rec.write({'statement_id': self.statement_id.id})
#             aml_rec.move_id.write({'statement_line_id': self.id})
#             counterpart_moves = (counterpart_moves | aml_rec.move_id)
# 
#         # Create move line(s). Either matching an existing journal entry (eg. invoice), in which
#         # case we reconcile the existing and the new move lines together, or being a write-off.
# #         print 'counterpart_aml_dicts  branch',counterpart_aml_dicts
# #         print 'new_aml_dicts ',new_aml_dicts
#         if counterpart_aml_dicts or new_aml_dicts:
#             st_line_currency = self.currency_id or statement_currency
#             st_line_currency_rate = self.currency_id and (self.amount_currency / self.amount) or False
# 
#             # Create the move
#             self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
#             move_vals = self._prepare_reconciliation_move(self.statement_id.name)
#             move_vals.update({'branch_id': self.branch_id.id})
#             print ('move_vals ',move_vals)
#             move = self.env['account.move'].create(move_vals)
#             counterpart_moves = (counterpart_moves | move)
#             # Create The payment
#             payment = False
#             if abs(total)>0.00001:
#                 partner_id = self.partner_id and self.partner_id.id or False
#                 partner_type = False
#                 if partner_id:
#                     if total < 0:
#                         partner_type = 'supplier'
#                     else:
#                         partner_type = 'customer'
# 
#                 payment_methods = (total>0) and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
#                 currency = self.journal_id.currency_id or self.company_id.currency_id
#                 p_vals={
#                         'payment_method_id': payment_methods and payment_methods[0].id or False,
#                         'payment_type': total >0 and 'inbound' or 'outbound',
#                         'partner_id': self.partner_id and self.partner_id.id or False,
#                         'partner_type': partner_type,
#                         'journal_id': self.statement_id.journal_id.id,
#                         'payment_date': self.date,
#                         'state': 'reconciled',
#                         'branch_id': self.branch_id.id,
#                         'currency_id': currency.id,
#                         'amount': abs(total),
#                         'communication': self.name or '',
#                         'name': self.statement_id.name,
#                     }
# #                 print 'self.import_line_id.invoice_id ',self.import_line_id.invoice_id
#                 #Хобоотой импортлосон нэхэмжлэх хавсаргах, эндээс нийт төлөлтийг авах account_invoice_payment_rel
# #                print 'import_line_id.invoice_id ',self.import_line_id.invoice_id
# #                 if self.import_line_id.invoice_id:
#                 if self.import_line_id.move_id:
#                     p_vals.update({
#                             'invoice_ids': [(6, 0, self.import_line_id.move_id.ids)],
#                         })
# #                print 'self.import_line_ids-----: ',self.import_line_ids
#                 if self.import_line_ids:
#                     lines=[]
#                     for l in self.import_line_ids:
#                         if l.import_inv_id:
#                             lines.append(l.import_inv_id.id)
#                     # print 'lines ',lines
#                     p_vals.update({
#                                 'invoice_ids': [(6, 0, lines)],
#                                 })
#                 #олон гүйлгээ импортолсон бол нэхэмжл
#                 payment = self.env['account.payment'].create(p_vals)
#             # Complete dicts to create both counterpart move lines and write-offs
#             to_create = (counterpart_aml_dicts + new_aml_dicts)
#             ctx = dict(self._context, date=self.date)
#             for aml_dict in to_create:
#                 aml_dict['move_id'] = move.id
#                 aml_dict['branch_id'] = self.branch_id.id
#                 aml_dict['partner_id'] = self.partner_id.id
#                 aml_dict['statement_id'] = self.statement_id.id
#                 if st_line_currency.id != company_currency.id:
#                     aml_dict['amount_currency'] = aml_dict['debit'] - aml_dict['credit']
#                     aml_dict['currency_id'] = st_line_currency.id
#                     if self.currency_id and statement_currency.id == company_currency.id and st_line_currency_rate:
#                         # Statement is in company currency but the transaction is in foreign currency
#                         aml_dict['debit'] = company_currency.round(aml_dict['debit'] / st_line_currency_rate)
#                         aml_dict['credit'] = company_currency.round(aml_dict['credit'] / st_line_currency_rate)
#                     elif self.currency_id and st_line_currency_rate:
#                         # Statement is in foreign currency and the transaction is in another one
#                         aml_dict['debit'] = statement_currency.with_context(ctx).compute(aml_dict['debit'] / st_line_currency_rate, company_currency)
#                         aml_dict['credit'] = statement_currency.with_context(ctx).compute(aml_dict['credit'] / st_line_currency_rate, company_currency)
#                     else:
#                         # Statement is in foreign currency and no extra currency is given for the transaction
#                         aml_dict['debit'] = st_line_currency.with_context(ctx).compute(aml_dict['debit'], company_currency)
#                         aml_dict['credit'] = st_line_currency.with_context(ctx).compute(aml_dict['credit'], company_currency)
#                 elif statement_currency.id != company_currency.id:
#                     # Statement is in foreign currency but the transaction is in company currency
#                     prorata_factor = (aml_dict['debit'] - aml_dict['credit']) / self.amount_currency
#                     aml_dict['amount_currency'] = prorata_factor * self.amount
#                     aml_dict['currency_id'] = statement_currency.id
# 
#             # Create write-offs
#             # When we register a payment on an invoice, the write-off line contains the amount
#             # currency if all related invoices have the same currency. We apply the same logic in
#             # the manual reconciliation.
#             counterpart_aml = self.env['account.move.line']
#             for aml_dict in counterpart_aml_dicts:
#                 counterpart_aml |= aml_dict.get('move_line', self.env['account.move.line'])
#             new_aml_currency = False
#             if counterpart_aml\
#                     and len(counterpart_aml.mapped('currency_id')) == 1\
#                     and counterpart_aml[0].currency_id\
#                     and counterpart_aml[0].currency_id != company_currency:
#                 new_aml_currency = counterpart_aml[0].currency_id
#             new_aml_id=False
#             for aml_dict in new_aml_dicts:
#                 aml_dict['payment_id'] = payment and payment.id or False
#                 if new_aml_currency and not aml_dict.get('currency_id'):
#                     aml_dict['currency_id'] = new_aml_currency.id
#                     aml_dict['amount_currency'] = company_currency.with_context(ctx).compute(aml_dict['debit'] - aml_dict['credit'], new_aml_currency)
#                 # харьцсан дансны бичилт
#                 new_aml_id = aml_obj.with_context(check_move_validity=False, apply_taxes=True).create(aml_dict)
#             # Create counterpart move lines and reconcile them
#             for aml_dict in counterpart_aml_dicts:
#                 if aml_dict['move_line'].partner_id.id:
#                     aml_dict['partner_id'] = aml_dict['move_line'].partner_id.id
#                 aml_dict['account_id'] = aml_dict['move_line'].account_id.id
#                 aml_dict['payment_id'] = payment and payment.id or False
# 
#                 counterpart_move_line = aml_dict.pop('move_line')
#                 if counterpart_move_line.currency_id and counterpart_move_line.currency_id != company_currency and not aml_dict.get('currency_id'):
#                     aml_dict['currency_id'] = counterpart_move_line.currency_id.id
#                     aml_dict['amount_currency'] = company_currency.with_context(ctx).compute(aml_dict['debit'] - aml_dict['credit'], counterpart_move_line.currency_id)
#                 new_aml = aml_obj.with_context(check_move_validity=False).create(aml_dict)
#                 (new_aml | counterpart_move_line).reconcile()
#         
#         
# #             print 'counterpart_aml_dicts============================== ',counterpart_aml_dicts
# #             print 'self.import_line_id ',self.import_line_id
#             # new_aml_id Авлага өглөг төлөлт
#             
#             if self.import_line_id and new_aml_id:
# #                 print 'new_aml_dicts | self.import_line_id------111 ',new_aml_id | self.import_line_id
#                 (new_aml_id | self.import_line_id).reconcile()
#             #Олон нэхэмжлэх импортлосон бол бүгдийг нь хугацааны дарааллаар тулгах
#             if self.import_line_ids  and new_aml_id:
#                 imort_lines=False
#                 for l in self.import_line_ids:
#                     if l.import_inv_id:
#               #          print 'l.import_inv_id.move_id ',l.import_inv_id.move_id
#                         if l.import_inv_id.move_id:
# #                             imort_lines = [aml for aml in l.import_inv_id.move_id.line_ids if aml.account_id.internal_type in ('receivable', 'payable')]
#                             for  aml in l.import_inv_id.move_id.line_ids:
#                                 if aml.account_id.internal_type in ('receivable', 'payable'):
#                                     if not imort_lines:
#                                         imort_lines=aml
#                                     else:
#                                         imort_lines+=aml
#                 (new_aml_id | imort_lines).reconcile()
#             if self.import_aml_ids  and new_aml_id:
#                 imort_lines=False
#                 for aml in self.import_aml_ids:
#                     if not imort_lines:
#                         imort_lines=aml
#                     else:
#                         imort_lines+=aml
#                 (new_aml_id | imort_lines).reconcile()                
# #             counterpart_aml_dicts = [{'move_line':self.import_line_id,'credit':self.import_line_id.credit,\
# #                                      'debit':self.import_line_id.debit,'name':self.import_line_id.name}]            
#             
#             # Create the move line for the statement line using the bank statement line as the remaining amount
#             # This leaves out the amount already reconciled and avoids rounding errors from currency conversion
#             st_line_amount = -sum([x.balance for x in move.line_ids])#Бүх гүйлгээний зөрүүгээр
#             aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
# #             aml_dict Мөнгөн хөрөнгийн дансны гүйлгээ
#             aml_dict['payment_id'] = payment and payment.id or False
#             aml_obj.with_context(check_move_validity=False).create(aml_dict)
#             print ('move ',move)
#             move.post()
#             #record the move name on the statement line to be able to retrieve it in case of unreconciliation
#             self.write({'move_name': move.name})
#             payment.write({'payment_reference': move.name})
#         elif self.move_name:
#             raise UserError(_('Operation not allowed. Since your statement line already received a number, you cannot reconcile it entirely with existing journal entries otherwise it would make a gap in the numbering. You should book an entry and make a regular revert of it in case you want to cancel it.'))
#         counterpart_moves._check_balanced()
#         return counterpart_moves
#     

#     def fast_counterpart_creation_old(self):
#         #darmaa 
#         for st_line in self:
#             # Technical functionality to automatically reconcile by creating a new move line
#  
#             vals = {
#                 'name': st_line.name,
#                 'debit': st_line.amount < 0 and -st_line.amount or 0.0,
#                 'credit': st_line.amount > 0 and st_line.amount or 0.0,
#                 'account_id': st_line.account_id.id,
#                 'branch_id':st_line.branch_id and st_line.branch_id.id or False,
#                 'tax_ids':st_line.tax_id and [[4, st_line.tax_id.id, False]] or False,#татварын бичилт салгаж бичих хэсэг aml дотор хийгдэнэ
#             }
#              
#             st_line.process_reconciliation(new_aml_dicts=[vals])
#     
# 
#     def _prepare_reconciliation_move_line_old(self, move, amount):
#         """ Prepare the dict of values to balance the move.
#             add darmaa
#             :param recordset move: the account.move to link the move line
#             :param float amount: the amount of transaction that wasn't already reconciled
#         """
#         company_currency = self.journal_id.company_id.currency_id
#         statement_currency = self.journal_id.currency_id or company_currency
#         st_line_currency = self.currency_id or statement_currency
#         amount_currency = False
#         st_line_currency_rate = self.currency_id and (self.amount_currency / self.amount) or False
#         # We have several use case here to compure the currency and amount currency of counterpart line to balance the move:
#         if st_line_currency != company_currency and st_line_currency == statement_currency:
#             # company in currency A, statement in currency B and transaction in currency B
#             # counterpart line must have currency B and correct amount is inverse of already existing lines
#             amount_currency = -sum([x.amount_currency for x in move.line_ids])
#         elif st_line_currency != company_currency and statement_currency == company_currency:
#             # company in currency A, statement in currency A and transaction in currency B
#             # counterpart line must have currency B and correct amount is inverse of already existing lines
#             amount_currency = -sum([x.amount_currency for x in move.line_ids])
#         elif st_line_currency != company_currency and st_line_currency != statement_currency:
#             # company in currency A, statement in currency B and transaction in currency C
#             # counterpart line must have currency B and use rate between B and C to compute correct amount
#             amount_currency = -sum([x.amount_currency for x in move.line_ids])/st_line_currency_rate
#         elif st_line_currency == company_currency and statement_currency != company_currency:
#             # company in currency A, statement in currency B and transaction in currency A
#             # counterpart line must have currency B and amount is computed using the rate between A and B
#             amount_currency = amount/st_line_currency_rate
#         
#         # last case is company in currency A, statement in currency A and transaction in currency A
#         # and in this case counterpart line does not need any second currency nor amount_currency
# 
#         return {
#             'name': self.name,
#             'move_id': move.id,
#             'partner_id': self.partner_id and self.partner_id.id or False,
#             'account_id': amount >= 0 \
#                 and self.statement_id.journal_id.default_credit_account_id.id \
#                 or self.statement_id.journal_id.default_debit_account_id.id,
#             'credit': amount < 0 and -amount or 0.0,
#             'debit': amount > 0 and amount or 0.0,
#             'statement_line_id': self.id,
#             'currency_id': statement_currency != company_currency and statement_currency.id or (st_line_currency != company_currency and st_line_currency.id or False),
#             'amount_currency': amount_currency,
#             'branch_id':self.branch_id and self.branch_id.id or False
#         }

class StockWarehouse(models.Model):

    _inherit = 'stock.warehouse'

    branch_id  = fields.Many2one('res.branch', 'Branch')
    owner_partner_id  = fields.Many2one('res.partner', u'Эд хариуцагч харилцагч')

class StockPickingType(models.Model):

    _inherit = 'stock.picking.type'

    branch_id  = fields.Many2one(related='warehouse_id.branch_id')



# class account_asset_asset(models.Model):

#     _inherit = 'account.asset'

#     branch_id  = fields.Many2one('res.branch', 'Branch')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
