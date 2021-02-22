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
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, pycompat

class pos_session(models.Model):
    _inherit = 'pos.session'

    # 
    # def _get_session_default_branch(self):
    #     for session in self:
    #         user_pool = self.env['res.users']
    #         branch_id = user_pool.browse(self.env.uid).branch_id and  user_pool.browse(self.env.uid).branch_id.id
    #         session.branch_id = branch_id
            
    
    @api.depends('config_id')
    def _get_session_default_branch(self):
        for item in self:
            item.branch_id = item.config_id.branch_id.id

    branch_id = fields.Many2one('res.branch', 'Branch', compute = '_get_session_default_branch' , store=True)    


class pos_order(models.Model):
    _inherit = 'pos.order'

    @api.model
    def create(self, val):
        
#         user_pool = self.env['res.users']
#         branch_id = user_pool.browse(self.env.uid).branch_id and  user_pool.browse(self.env.uid).branch_id.id
        #darmaa sessoin buyu config iin branch avah
        if val.get('session_id',False):
            session_pool = self.env['pos.session']
            branch_id = session_pool.browse(val['session_id']).branch_id and  session_pool.browse(val['session_id']).branch_id.id
        else:
            user_pool = self.env['res.users']
            branch_id = user_pool.browse(self.env.uid).branch_id and  user_pool.browse(self.env.uid).branch_id.id
            
        val.update({'branch_id' : branch_id})  
        res  =  super(pos_order,self).create(val)

        return res
        
    branch_id = fields.Many2one('res.branch', 'Branch')
    

    def _create_account_move_line(self, session=None, move=None):
        # Tricky, via the workflow, we only have one id in the ids variable
        """Create a account move line of order grouped by products or not.
        branch_id add darmaa"""
        IrProperty = self.env['ir.property']
        ResPartner = self.env['res.partner']

        if session and not all(session.id == order.session_id.id for order in self):
            raise UserError(_('Selected orders do not have the same session!'))

        grouped_data = {}
        have_to_group_by = session and session.config_id.group_by or False
        rounding_method = session and session.config_id.company_id.tax_calculation_rounding_method

        for order in self.filtered(lambda o: not o.account_move or o.state == 'paid'):
            current_company = order.sale_journal.company_id
            account_def = IrProperty.get(
                'property_account_receivable_id', 'res.partner')
            order_account = order.partner_id.property_account_receivable_id.id or account_def and account_def.id
            order_branch = order.branch_id and order.branch_id.id or False
            # print 'order_branch ',order_branch
            partner_id = ResPartner._find_accounting_partner(order.partner_id).id or False
            if move is None:
                # Create an entry for the sale
                journal_id = self.env['ir.config_parameter'].sudo().get_param(
                    'pos.closing.journal_id_%s' % current_company.id, default=order.sale_journal.id)
                move = self._create_account_move(
                    order.session_id.start_at, order.name, int(journal_id), order.company_id.id)

            def insert_data(data_type, values):
                # if have_to_group_by:
                values.update({
                    'partner_id': partner_id,
                    'move_id': move.id,
                })

                key = self._get_account_move_line_group_data_type_key(data_type, values)
                if not key:
                    return

                grouped_data.setdefault(key, [])

                if have_to_group_by:
                    if not grouped_data[key]:
                        grouped_data[key].append(values)
                    else:
                        current_value = grouped_data[key][0]
                        current_value['quantity'] = current_value.get('quantity', 0.0) + values.get('quantity', 0.0)
                        current_value['credit'] = current_value.get('credit', 0.0) + values.get('credit', 0.0)
                        current_value['debit'] = current_value.get('debit', 0.0) + values.get('debit', 0.0)
                else:
                    grouped_data[key].append(values)

            # because of the weird way the pos order is written, we need to make sure there is at least one line,
            # because just after the 'for' loop there are references to 'line' and 'income_account' variables (that
            # are set inside the for loop)
            # TOFIX: a deep refactoring of this method (and class!) is needed
            # in order to get rid of this stupid hack
            assert order.lines, _('The POS order must have lines when calling this method')
            # Create an move for each order line
            cur = order.pricelist_id.currency_id
            for line in order.lines:
                amount = line.price_subtotal

                # Search for the income account
                if line.product_id.property_account_income_id.id:
                    income_account = line.product_id.property_account_income_id.id
                elif line.product_id.categ_id.property_account_income_categ_id.id:
                    income_account = line.product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(_('Please define income '
                                      'account for this product: "%s" (id:%d).')
                                    % (line.product_id.name, line.product_id.id))

                name = line.product_id.name
                if line.notice:
                    # add discount reason in move
                    name = name + ' (' + line.notice + ')'

                # Create a move for the line for the order line
                insert_data('product', {
                    'name': name,
                    'quantity': line.qty,
                    'product_id': line.product_id.id,
                    'account_id': income_account,
                    'analytic_account_id': self._prepare_analytic_account(line),
                    'credit': ((amount > 0) and amount) or 0.0,
                    'debit': ((amount < 0) and -amount) or 0.0,
                    'tax_ids': [(6, 0, line.tax_ids_after_fiscal_position.ids)],
                    'partner_id': partner_id,
                    'branch_id': order_branch,
                })

                # Create the tax lines
                taxes = line.tax_ids_after_fiscal_position.filtered(lambda t: t.company_id.id == current_company.id)
                if not taxes:
                    continue
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                for tax in taxes.compute_all(price, cur, line.qty)['taxes']:
                    insert_data('tax', {
                        'name': _('Tax') + ' ' + tax['name'],
                        'product_id': line.product_id.id,
                        'quantity': line.qty,
                        'account_id': tax['account_id'] or income_account,
                        'credit': ((tax['amount'] > 0) and tax['amount']) or 0.0,
                        'debit': ((tax['amount'] < 0) and -tax['amount']) or 0.0,
                        'tax_line_id': tax['id'],
                        'partner_id': partner_id,
                        'branch_id': order_branch,
                    })

            # round tax lines per order
            if rounding_method == 'round_globally':
                for group_key, group_value in grouped_data.items():
                    if group_key[0] == 'tax':
                        for line in group_value:
                            line['credit'] = cur.round(line['credit'])
                            line['debit'] = cur.round(line['debit'])

            # counterpart
            insert_data('counter_part', {
                'name': _("Trade Receivables"),  # order.name,
                'account_id': order_account,
                'branch_id': order_branch,
                'credit': ((order.amount_total < 0) and -order.amount_total) or 0.0,
                'debit': ((order.amount_total > 0) and order.amount_total) or 0.0,
                'partner_id': partner_id
            })

            order.write({'state': 'done', 'account_move': move.id})

        all_lines = []
        for group_key, group_data in grouped_data.items():
            for value in group_data:
                all_lines.append((0, 0, value),)
        if move:  # In case no order was changed
            move.sudo().write({'line_ids': all_lines})
            move.sudo().post()
        return True

    def _prepare_invoice(self):
        ''' branch_id append
        '''
        invoice_field = super(pos_order, self)._prepare_invoice()
        inv_branch=False
        if self.session_id.config_id.invoice_branch_id:
            inv_branch = self.session_id.config_id.invoice_branch_id.id
        else:
            user_pool = self.env['res.users']
            inv_branch = user_pool.browse(self.env.uid).branch_id and  user_pool.browse(self.env.uid).branch_id.id            
        invoice_field['branch_id'] = inv_branch
        return invoice_field


    def _action_create_invoice_line(self, line=False, invoice_id=False):
        ''' branch_id append
        '''
        InvoiceLine = self.env['account.invoice.line']
        inv_name = line.product_id.name_get()[0][1]
        
        inv_branch=False
        if self.session_id.config_id.invoice_branch_id:
            inv_branch = self.session_id.config_id.invoice_branch_id.id
        else:
            user_pool = self.env['res.users']
            inv_branch = user_pool.browse(self.env.uid).branch_id and  user_pool.browse(self.env.uid).branch_id.id 
                    
        inv_line = {
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'quantity': line.qty,
            'account_analytic_id': self._prepare_analytic_account(line),
            'name': inv_name,
            'branch_id':inv_branch
        }
        # Oldlin trick
        invoice_line = InvoiceLine.sudo().new(inv_line)
        invoice_line._onchange_product_id()
        invoice_line.invoice_line_tax_ids = invoice_line.invoice_line_tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id).ids
        fiscal_position_id = line.order_id.fiscal_position_id
        if fiscal_position_id:
            invoice_line.invoice_line_tax_ids = fiscal_position_id.map_tax(invoice_line.invoice_line_tax_ids, line.product_id, line.order_id.partner_id)
        invoice_line.invoice_line_tax_ids = invoice_line.invoice_line_tax_ids.ids
        # We convert a new id object back to a dictionary to write to
        # bridge between old and new api
        inv_line = invoice_line._convert_to_write({name: invoice_line[name] for name in invoice_line._cache})
        inv_line.update(price_unit=line.price_unit, discount=line.discount, name=inv_name)
        return InvoiceLine.sudo().create(inv_line)
    

#     def create_picking(self):
#         """Picking BBO deer invoice branch avah."""
#         Picking = self.env['stock.picking']
#         Move = self.env['stock.move']
#         StockWarehouse = self.env['stock.warehouse']
#         for order in self:
# #            print 'order-----to_invoice ',order.to_invoice
            
#             if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
#                 continue
#             address = order.partner_id.address_get(['delivery']) or {}
#             picking_type = order.picking_type_id
#             return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
#             order_picking = Picking
#             return_picking = Picking
#             moves = Move
#             location_id = order.location_id.id
#             if order.partner_id:
#                 destination_id = order.partner_id.property_stock_customer.id
#             else:
#                 if (not picking_type) or (not picking_type.default_location_dest_id):
#                     customerloc, supplierloc = StockWarehouse._get_partner_locations()
#                     destination_id = customerloc.id
#                 else:
#                     destination_id = picking_type.default_location_dest_id.id

#             if picking_type:
#                 message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
#                 picking_vals = {
#                     'origin': order.name,
#                     'partner_id': address.get('delivery', False),
#                     'date_done': order.date_order,
#                     'picking_type_id': picking_type.id,
#                     'company_id': order.company_id.id,
#                     'move_type': 'direct',
#                     'note': order.note or "",
#                     'location_id': location_id,
#                     'location_dest_id': destination_id,
#                 }
#                 pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
#                 if pos_qty:
#                     is_invoice=False
#                     if order.to_invoice:
#                         is_invoice=True
#                     order_picking = Picking.with_context(is_invoice=is_invoice,order_id=order).create(picking_vals.copy())
#                     order_picking.message_post(body=message)
#                 neg_qty = any([x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
#                 if neg_qty:
# #                     is_invoice=False
# #                     if order.to_invoice:
# #                         is_invoice=True
#                     return_vals = picking_vals.copy()
#                     return_vals.update({
#                         'location_id': destination_id,
#                         'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
#                         'picking_type_id': return_pick_type.id
#                     })
#                     return_picking = Picking.create(return_vals)
#                     return_picking.message_post(body=message)

#             for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
#                 moves |= Move.create({
#                     'name': line.name,
#                     'product_uom': line.product_id.uom_id.id,
#                     'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
#                     'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
#                     'product_id': line.product_id.id,
#                     'product_uom_qty': abs(line.qty),
#                     'state': 'draft',
#                     'location_id': location_id if line.qty >= 0 else destination_id,
#                     'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
#                 })

#             # prefer associating the regular order picking, not the return
#             order.write({'picking_id': order_picking.id or return_picking.id})

#             if return_picking:
#                 order._force_picking_done(return_picking)
#             if order_picking:
#                 order._force_picking_done(order_picking)

#             # when the pos.config has no picking_type_id set only the moves will be created
#             if moves and not return_picking and not order_picking:
#                 moves._action_assign()
#                 moves.filtered(lambda m: m.state in ['confirmed', 'waiting'])._force_assign()
#                 moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

#         return True
        
class PosConfig(models.Model):
    _inherit = 'pos.config'

    branch_id = fields.Many2one('res.branch', 'Branch')
    address = fields.Text('Address',related='branch_id.address', store=True,)
    telephone_no = fields.Char('Telephone no',related='branch_id.telephone_no', )

    invoice_branch_id = fields.Many2one('res.branch', 'Invoice Branch')
    









# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
