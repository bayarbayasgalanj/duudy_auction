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
from odoo.tools.safe_eval import safe_eval
import logging
_logger = logging.getLogger(__name__)

class account_move_line(models.Model):

    _inherit = 'account.move.line'


    cash_type_id = fields.Many2one('account.cash.move.type',)# compute='get_compute_cash_type', store=True
    set_cash_type = fields.Boolean('Set cmt')

    
    @api.depends('account_id','statement_line_id','statement_line_id.cash_type_id')
    def get_compute_cash_type(self):
        count=1
        for item in self:
            _logger.info(u'get_compute_cash_type %s '%(count))
            count+=1
            if item.account_id.internal_type == 'liquidity':
                if item.statement_line_id and item.statement_line_id.cash_type_id:
                    item.cash_type_id=item.statement_line_id.cash_type_id.id
                elif item.account_id.cmtype_ids:
                    for c in item.account_id.cmtype_ids:
                        item.cash_type_id=c.id
                        break



    def create_analytic_lines(self):
        """ account.analytic.line ийг ашиглахгүй
        """
        return True
#         lines_to_create_analytic_entries = self.env['account.move.line']
#         for obj_line in self:
#             for tag in obj_line.analytic_tag_ids.filtered('active_analytic_distribution'):
#                 for distribution in tag.analytic_distribution_ids:
#                     vals_line = obj_line._prepare_analytic_distribution_line(distribution)
#                     self.env['account.analytic.line'].create(vals_line)
#             if obj_line.analytic_account_id:
#                 lines_to_create_analytic_entries |= obj_line
# 
#         # create analytic entries in batch
#         if lines_to_create_analytic_entries:
#             values_list = lines_to_create_analytic_entries._prepare_analytic_line()
#             self.env['account.analytic.line'].create(values_list)

#     @api.model
#     def _get_fields_onchange_balance_model(self, quantity, discount, balance, move_type, currency, taxes, price_subtotal):
#         ''' This method is used to recompute the values of 'quantity', 'discount', 'price_unit' due to a change made
#         in some accounting fields such as 'balance'.
#  
#         This method is a bit complex as we need to handle some special cases.
#         For example, setting a positive balance with a 100% discount.
#  
#         :param quantity:    The current quantity.
#         :param discount:    The current discount.
#         :param balance:     The new balance.
#         :param move_type:   The type of the move.
#         :param currency:    The currency.
#         :param taxes:       The applied taxes.
#         :return:            A dictionary containing 'quantity', 'discount', 'price_unit'.
#         darmaa round 2
#                     Өөрчлөлт
#                     'price_unit': balance / discount_factor / (quantity or 1.0),
#                     -->
#                     aa=round(balance / discount_factor / (quantity or 1.0),2)
#                     Нэмсэн
#                     balance = round(balance,2)                   
#                     _check_balanced dotor zuruugeer taaruulah 
#         '''
#         if move_type in self.move_id.get_outbound_types():
#             sign = 1
#         elif move_type in self.move_id.get_inbound_types():
#             sign = -1
#         else:   
#             sign = 1
#         balance *= sign
#         
#         #darmaa 15454.550000000001 suuliin  0000000001  g arilgah
#         balance = round(balance,2)
#         # Avoid rounding issue when dealing with price included taxes. For example, when the price_unit is 2300.0 and
#         # a 5.5% price included tax is applied on it, a balance of 2300.0 / 1.055 = 2180.094 ~ 2180.09 is computed.
#         # However, when triggering the inverse, 2180.09 + (2180.09 * 0.055) = 2180.09 + 119.90 = 2299.99 is computed.
#         # To avoid that, set the price_subtotal at the balance if the difference between them looks like a rounding
#         # issue.
#         if currency.is_zero(balance - price_subtotal):
#             return {}
# 
#         taxes = taxes.flatten_taxes_hierarchy()
#         if taxes and any(tax.price_include for tax in taxes):
#             # Inverse taxes. E.g:
#             #
#             # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
#             # -----------------------------------------------------------------------------------
#             # 110           | 10% incl, 5%  |                   | 100               | 115
#             # 10            |               | 10% incl          | 10                | 10
#             # 5             |               | 5%                | 5                 | 5
#             #
#             # When setting the balance to -200, the expected result is:
#             #
#             # Price Unit    | Taxes         | Originator Tax    |Price Subtotal     | Price Total
#             # -----------------------------------------------------------------------------------
#             # 220           | 10% incl, 5%  |                   | 200               | 230
#             # 20            |               | 10% incl          | 20                | 20
#             # 10            |        
# #             .with_context(force_price_include=True)       | 5%                | 10                | 10
#             taxes_res = taxes._origin.compute_all(balance, currency=currency, handle_price_include=False)
#             for tax_res in taxes_res['taxes']:
#                 tax = self.env['account.tax'].browse(tax_res['id'])
#                 if tax.price_include:
#                     # 1545.45 baih yostoi baihad 1545.46
#                     balance += tax_res['amount']
#  
#         discount_factor = 1 - (discount / 100.0)
#         if balance and discount_factor:
#             # discount != 100%
# #             aa=round(balance / discount_factor / (quantity or 1.0),1)
# #             if balance>17000:
# #                 print (a)
#             aa=round(balance / discount_factor / (quantity or 1.0),2)
#             vals = {
#                 'quantity': quantity or 1.0,
#                 'price_unit': aa,
#             }
#         elif balance and not discount_factor:
#             # discount == 100%    
#             vals = {
#                 'quantity': quantity or 1.0,
#                 'discount': 0.0,
#                 'price_unit': balance / (quantity or 1.0),
#             }
#         else:
#             vals = {}
#         _logger.info(u'_get_fields_onchange_balance_model vals-------------------------- %s '%(vals))
#         return vals
