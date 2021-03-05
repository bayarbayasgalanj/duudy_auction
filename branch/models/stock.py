# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class StockMove(models.Model):
    _inherit = "stock.move"
    
    def _is_inter(self):
        """ 
        """
        return self.location_id.company_id.id == self.location_dest_id.company_id.id and self.location_id.usage == 'internal' and self.location_dest_id.usage == 'internal' 


    
#     def _action_done(self, cancel_backorder=False):
# #         self.product_price_update_before_done()
#         res = super(StockMove, self)._action_done(cancel_backorder)
#         # Bayasaa haav _run_valuation gedeg func 13 dr bhgui bolson uchir
#         # for move in res:
#         #     move._run_valuation()

#         # Bayasaa haav _account_entry_move ene func uurchilugdsun bsan
#         # for move in res.filtered(lambda m: m.product_id.valuation == 'real_time' and m._is_inter()):
#         #     move._account_entry_move()
#         return res
        
    def get_branch(self):
        dest_branch=False
        src_branch=False
        if self.location_id.usage=='internal' and self.location_dest_id.usage=='customer':
#             wh_dest=self.location_dest_id.get_warehouse()
            wh_src=self.location_id.get_warehouse()
            dest_branch =src_branch = wh_src.branch_id.id
        elif self.location_id.usage=='supplier' and self.location_dest_id.usage=='internal':
            wh_dest=self.location_dest_id.get_warehouse()
            dest_branch =src_branch = wh_dest.branch_id.id
        elif self.location_id.usage=='customer' and self.location_dest_id.usage=='internal':
            wh_dest=self.location_dest_id.get_warehouse()
            dest_branch =src_branch = wh_dest.branch_id.id
        elif self.location_id.usage=='internal' and self.location_dest_id.usage=='supplier':
            wh_src=self.location_id.get_warehouse()
            dest_branch =src_branch = wh_src.branch_id.id
        elif self.location_id.usage=='inventory' or self.location_dest_id.usage=='internal':
            wh_src=self.location_dest_id.get_warehouse()
            dest_branch =src_branch = wh_src.branch_id.id
        elif self.location_id.usage=='internal' or self.location_dest_id.usage=='inventory':
            wh_src=self.location_id.get_warehouse()
            dest_branch =src_branch = wh_src.branch_id.id
        else:
            #дотоод хөдөлгөөн, буцаалт гм
            wh_dest=self.location_dest_id.get_warehouse()
            wh_src=self.location_id.get_warehouse()
            dest_branch = wh_dest.branch_id.id
            src_branch = wh_src.branch_id.id
            
        return dest_branch,src_branch
        

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        """ Overridden from stock_account add branch_id from warehouse 
        """
        self.ensure_one()

        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
        dest_branch,src_branch = self.get_branch()
#         if pos_order_id:
#             if  pos_order_id.session_id and pos_order_id.session_id.config_id \
#                         and pos_order_id.session_id.config_id.invoice_branch_id:
#                 dest_branch = pos_order_id.session_id.config_id.invoice_branch_id.id
        if self.picking_id.other_expense_id:
            account_id =False
            if self.picking_id.other_expense_id:
                if self.picking_id.other_expense_id.account_id:
                    account_id=self.picking_id.other_expense_id.account_id.id
                elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.account_id:
                    account_id = self.picking_id.other_expense_id.transaction_value_id.account_id.id
#                 if self.picking_id.other_expense_id.branch_id:
#                     dest_branch =  self.picking_id.other_expense_id.branch_id.id #Шаардах дээрээс буруу бранч аваад байна.
            if self.picking_id.other_expense_id.department_id and self.picking_id.other_expense_id.department_id.branch_id:
                dest_branch = self.picking_id.other_expense_id.department_id.branch_id.id
                src_branch = self.picking_id.other_expense_id.department_id.branch_id.id
            if account_id:
                rslt['debit_line_vals']['account_id'] = account_id
        rslt['debit_line_vals']['branch_id'] = dest_branch
        rslt['credit_line_vals']['branch_id'] = src_branch
        return rslt

#     def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
#         """
#         branch агуулахаас авах. Дотоод хөдөлгөөн бол өөр өөрийн branch руу хийх
#         """
#         self.ensure_one()
#         if self._context.get('force_valuation_amount'):
#             valuation_amount = self._context.get('force_valuation_amount')
#         else:
#             valuation_amount = cost

#         if self._context.get('forced_ref'):
#             ref = self._context['forced_ref']
#         else:
#             ref = self.picking_id.name
#         is_pos_invoice=False
#         pos_order_id=False
#         if self._context.get('is_invoice') and self._context.get('order_id'):
#             is_pos_invoice = self._context['is_invoice']
#             pos_order_id = self._context['order_id']
#         # the standard_price of the product may be in another decimal precision, or not compatible with the coinage of
#         # the company currency... so we need to use round() before creating the accounting entries.
#         debit_value = self.company_id.currency_id.round(valuation_amount)

#         # check that all data is correct
#         if self.company_id.currency_id.is_zero(debit_value):
#             raise UserError(_("The cost of %s is currently equal to 0. Change the cost or the configuration of your product to avoid an incorrect valuation.") % (self.product_id.name,))
#         credit_value = debit_value

#         if self.product_id.cost_method == 'average' and self.company_id.anglo_saxon_accounting:
#             # in case of a supplier return in anglo saxon mode, for products in average costing method, the stock_input
#             # account books the real purchase price, while the stock account books the average price. The difference is
#             # booked in the dedicated price difference account.
#             if self.location_dest_id.usage == 'supplier' and self.origin_returned_move_id and self.origin_returned_move_id.purchase_line_id:
#                 debit_value = self.origin_returned_move_id.price_unit * qty
#             # in case of a customer return in anglo saxon mode, for products in average costing method, the stock valuation
#             # is made using the original average price to negate the delivery effect.
#             if self.location_id.usage == 'customer' and self.origin_returned_move_id:
#                 debit_value = self.origin_returned_move_id.price_unit * qty
#                 credit_value = debit_value
#         partner_id = (self.picking_id.partner_id and self.env['res.partner']._find_accounting_partner(self.picking_id.partner_id).id) or False
# #         self.env['stock.warehouse']
#         dest_branch,src_branch = self.get_branch()
#         if pos_order_id:
#             if  pos_order_id.session_id and pos_order_id.session_id.config_id \
#                         and pos_order_id.session_id.config_id.invoice_branch_id:
#                 dest_branch = pos_order_id.session_id.config_id.invoice_branch_id.id
#         analytic_account_id=False
#         if self.picking_id.other_expense_id:
#             if self.picking_id.other_expense_id.account_id:
#                 debit_account_id=self.picking_id.other_expense_id.account_id.id
#             if self.picking_id.other_expense_id.account_analytic_id:
#                 analytic_account_id = self.picking_id.other_expense_id.account_analytic_id.id
#             if self.picking_id.other_expense_id.branch_id:
#                 dest_branch = self.picking_id.other_expense_id.branch_id.id
                
#         debit_line_vals = {
#             'name': self.name,
#             'product_id': self.product_id.id,
#             'quantity': qty,
#             'product_uom_id': self.product_id.uom_id.id,
#             'ref': ref,
#             'partner_id': partner_id,
#             'debit': debit_value if debit_value > 0 else 0,
#             'credit': -debit_value if debit_value < 0 else 0,
#             'account_id': debit_account_id,
#             'branch_id':dest_branch,
#             'analytic_account_id':analytic_account_id
#         }
#         credit_line_vals = {
#             'name': self.name,
#             'product_id': self.product_id.id,
#             'quantity': qty,
#             'product_uom_id': self.product_id.uom_id.id,
#             'ref': ref,
#             'partner_id': partner_id,
#             'credit': credit_value if credit_value > 0 else 0,
#             'debit': -credit_value if credit_value < 0 else 0,
#             'account_id': credit_account_id,
#             'branch_id':src_branch
#         }
#         res = [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
#         if credit_value != debit_value:
#             # for supplier returns of product in average costing method, in anglo saxon mode
#             diff_amount = debit_value - credit_value
#             price_diff_account = self.product_id.property_account_creditor_price_difference
#             if not price_diff_account:
#                 price_diff_account = self.product_id.categ_id.property_account_creditor_price_difference_categ
#             if not price_diff_account:
#                 raise UserError(_('Configuration error. Please configure the price difference account on the product or its category to process this operation.'))
#             price_diff_line = {
#                 'name': self.name,
#                 'product_id': self.product_id.id,
#                 'quantity': qty,
#                 'product_uom_id': self.product_id.uom_id.id,
#                 'ref': ref,
#                 'partner_id': partner_id,
#                 'credit': diff_amount > 0 and diff_amount or 0,
#                 'debit': diff_amount < 0 and -diff_amount or 0,
#                 'account_id': price_diff_account.id,
#             }
#             res.append((0, 0, price_diff_line))
#         return res
    
#     def _account_entry_move(self):
#         """ Accounting Valuation Entries """
#         self.ensure_one()
#         print '_account_entry_move '
#         if self.product_id.type != 'product':
#             # no stock valuation for consumable products
#             return False
#         if self.restrict_partner_id:
#             # if the move isn't owned by the company, we don't make any valuation
#             return False
# 
#         location_from = self.location_id
#         location_to = self.location_dest_id
#         company_from = location_from.usage == 'internal' and location_from.company_id or False
#         company_to = location_to and (location_to.usage == 'internal') and location_to.company_id or False
# 
#         # Create Journal Entry for products arriving in the company; in case of routes making the link between several
#         # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
#         if company_to and (self.location_id.usage not in ('internal', 'transit') and self.location_dest_id.usage == 'internal' or company_from != company_to):
#             journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
#             if location_from and location_from.usage == 'customer':  # goods returned from customer
#                 self.with_context(force_company=company_to.id)._create_account_move_line(acc_dest, acc_valuation, journal_id)
#             else:
#                 self.with_context(force_company=company_to.id)._create_account_move_line(acc_src, acc_valuation, journal_id)
# 
#         # Create Journal Entry for products leaving the company
#         if company_from and (self.location_id.usage == 'internal' and self.location_dest_id.usage not in ('internal', 'transit') or company_from != company_to):
#             journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
#             if location_to and location_to.usage == 'supplier':  # goods returned to supplier
#                 self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_src, journal_id)
#             else:
#                 self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_dest, journal_id)
# 
#         if self.company_id.anglo_saxon_accounting and self.location_id.usage == 'supplier' and self.location_dest_id.usage == 'customer':
#             # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
#             journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
#             self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_dest, journal_id)


    # 13 deer uurchilugdsun bsan
    # def _account_entry_move(self):
    #     """Дотоод хөдөлгөөнд санхүү бичилт үүсгэх """
    #     self.ensure_one()
    #     if self.product_id.type != 'product':
    #         # no stock valuation for consumable products
    #         return False
    #     if self.restrict_partner_id:
    #         # if the move isn't owned by the company, we don't make any valuation
    #         return False

    #     location_from = self.location_id
    #     location_to = self.location_dest_id
    #     company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
    #     company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False


    #     # Create Journal Entry for products arriving in the company; in case of routes making the link between several
    #     # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
    #     is_in=self._is_in()
    #     if is_in:#Орлого
    #         journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
    #         if location_from and location_from.usage == 'customer':  # goods returned from customer
    #             self.with_context(force_company=company_to.id)._create_account_move_line(acc_dest, acc_valuation, journal_id)
    #         else:
    #             self.with_context(force_company=company_to.id)._create_account_move_line(acc_src, acc_valuation, journal_id)

    #     # Create Journal Entry for products leaving the company
    #     is_ount=self._is_out()
    #     if is_ount:#зарлага
    #         journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
    #         if location_to and location_to.usage == 'supplier':  # goods returned to supplier
    #             self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_src, journal_id)
    #         else:
    #             self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_dest, journal_id)

    #     _is_inter=self._is_inter()
    #     if _is_inter:#Дотоод
    #         company_from = self.location_id.company_id or False
    #         company_to =  self.location_dest_id.company_id or False
    #         journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
    #         self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_valuation, journal_id)

    #     if self.company_id.anglo_saxon_accounting and self._is_dropshipped():
    #         # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
    #         journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
    #         self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_dest, journal_id)
    
