# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    # Override
    def _default_picking_type(self):
        if self.company_id and self.env.user.warehouse_id and self.env.user.warehouse_id.company_id == self.company_id:
            return self.env.user.warehouse_id.in_type_id
        else:
            return False

    taxes_id = fields.Many2many('account.tax', string='Татвар')
    warehouse_id = fields.Many2one('stock.warehouse', related='picking_type_id.warehouse_id', string='Агуулах')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        # Override
        if self.company_id and self.env.user.warehouse_id and self.env.user.warehouse_id.company_id == self.company_id:
            self.picking_type_id = self.env.user.warehouse_id.in_type_id
        else:
            self.picking_type_id = False

    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        if self.company_id and self.branch_id:
            warehouses = self.env['stock.warehouse'].search([
                ('company_id', '=', self.company_id.id),
                ('branch_id', '=', self.branch_id.id),
                '|',
                ('id', '=', self.env.user.warehouse_id.id),
                ('access_user_ids', 'in', [self.env.uid])
            ])
            if len(warehouses) == 1:
                self.picking_type_id = warehouses.in_type_id
            else:
                self.picking_type_id = False

    @api.onchange('taxes_id')
    def onchange_taxes_id(self):
        for line in self.order_line:
            line.taxes_id = self.taxes_id

    # Хөнгөлөлтийн хувийг харилцагчаас авах
    @api.onchange('partner_id')
    def onchange_partner_discount(self):
        for line in self.order_line:
            line.discount = self.partner_id.discount_percent

    def action_update_stock_account_move_price_from_po(self):
        move_obj = self.env['stock.move']
        for po in self:
            for item in po.order_line:
                move_ids = move_obj.search([('purchase_line_id','=',item.id),('state','=','done')])
                for move_id in move_ids:
                    # if round(item.price_unit_stock_move, 2) != round(move_id.price_unit, 2):
                    obj = self.env['stock.move.change.price.unit']
                    change = obj.create({
                        'stock_move_ids': move_id.id,
                        'change_price_unit': round(item.price_unit_stock_move, 2)
                    })
                    change.with_context(force_update=True).set_change_price_unit()
                    # move_id.price_unit = round(item.price_unit_stock_move, 2)
                    # account_move_id = self.env['account.move'].search([('stock_move_id','=',move_id.id)])
                    # if account_move_id:
                    #     acc_amount = move_id.product_uom_qty * move_id.price_unit
                    #     query = """
                    #     UPDATE account_move_line set debit='%s' where move_id=%s and debit>0;
                    #     UPDATE account_move_line set credit='%s' where move_id=%s and credit>0;
                    #     """ % (acc_amount, account_move_id.id, acc_amount, account_move_id.id)

                    #     self._cr.execute(query)

                    #     query = """
                    #     UPDATE account_move set amount_total_signed='%s' where id=%s
                    #     """ % (acc_amount, account_move_id.id)

                    #     self._cr.execute(query)

    def button_cancel(self):
        for order in self:
            received_line_order = False
            not_done_pick = False

            if order.picking_ids.filtered(lambda r: r.state not in ['done','cancel']):
                not_done_pick = True
            for line in order.order_line.filtered(lambda r: r.qty_received > 0):
                received_line_order = True
            if not_done_pick or received_line_order:
                for pick in order.picking_ids:
                    if pick.state == 'done':
                        raise UserError(_('Unable to cancel purchase order %s as some receptions have already been done.') % (order.name))
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(_("Unable to cancel this purchase order. You must first cancel related vendor bills."))

            # If the product is MTO, change the procure_method of the the closest move to purchase to MTS.
            # The purpose is to link the po that the user will manually generate to the existing moves's chain.
            if order.state in ('draft', 'sent', 'to approve'):
                for order_line in order.order_line:
                    if order_line.move_dest_ids:
                        siblings_states = (order_line.move_dest_ids.mapped('move_orig_ids')).mapped('state')
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            order_line.move_dest_ids.write({'procure_method': 'make_to_stock'})
                            order_line.move_dest_ids._recompute_state()

            if not_done_pick or received_line_order:
                for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                    pick.action_cancel()

        self.write({'state': 'cancel'})

    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve(force=force)
        # Нэхэмжлэх үүсгэх
        for po in self:
            if po.company_id.auto_create_vendor_bill and po.order_line:
                if po.order_line[0].product_id.purchase_method == 'purchase':
                    invoice = po.create_auto_invoice('purchase')
                    if po.company_id.auto_validate_vendor_bill and invoice:
                        invoice.action_post()
        return res

    def get_purchase_method(self, purchase_method):
        return purchase_method

    def create_auto_invoice(self, from_purchase_method, picking=False):
        self.ensure_one()
        purchase_method = self.get_purchase_method(from_purchase_method)
        po_lines = self.order_line
        origin = self.name or ''
        invoice_date = fields.Date.context_today(self)
        if picking:
            origin +=(' /'+picking.invoice_number if picking.invoice_number else '')
            # stock_moves = picking.move_lines.filtered(lambda m: m.quantity_done > 0)
            po_lines = picking.move_lines.filtered(lambda m: m.state == 'done').mapped('purchase_line_id')
            invoice_date = picking.scheduled_date
        
        # create invoice line values
        invoice_line_ids = []
        for line in po_lines:
            accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=self.fiscal_position_id)
            qty_inv = 0
            if purchase_method == 'purchase' or line.product_id.type in ['service','consu']:
                qty_inv = line.product_qty-line.qty_invoiced if (line.product_qty-line.qty_invoiced)>0 else 0
            elif purchase_method == 'receive':
                qty_inv = line.qty_received-line.qty_invoiced if (line.qty_received-line.qty_invoiced)>0 else 0
            if qty_inv>0:
                invoice_line_ids.append(
                    (0, 0, {
                        'product_id': line.product_id.id,
                        'account_id': accounts['expense'].id,
                        'quantity': qty_inv,
                        'product_uom_id': line.product_uom.id,
                        'price_unit': line.price_unit,
                        'tax_ids': [(6, 0, line.taxes_id.ids)],
                        'purchase_line_id': line.id,
                        'analytic_account_id':line.account_analytic_id and line.account_analytic_id.id or False
                    })
                )
        if invoice_line_ids:
            invoice = self.env['account.move'].create({
                'ref': origin,
                'type': 'in_invoice',
                'company_id': self.company_id.id,
                'partner_id': self.partner_id.id,
                'fiscal_position_id': self.fiscal_position_id.id,
                'invoice_payment_term_id': self.payment_term_id.id,
                'currency_id': self.currency_id.id,
                'invoice_line_ids': invoice_line_ids,
                'invoice_date': invoice_date,
                'date': invoice_date,
            })

            # Compute invoice_origin.
            origins = set(invoice.line_ids.mapped('purchase_line_id.order_id.name'))
            invoice.invoice_origin = ','.join(list(origins))

            # Compute ref.
            # refs = set(invoice.line_ids.mapped('purchase_line_id.order_id.partner_ref'))
            # refs = [ref for ref in refs if ref]
            # invoice.ref = ','.join(refs)

            # Compute _invoice_payment_ref.
            # if len(refs) == 1:
            #     invoice._invoice_payment_ref = refs[0]

            invoice._onchange_currency()
            invoice.invoice_partner_bank_id = invoice.bank_partner_id.bank_ids and invoice.bank_partner_id.bank_ids[0]
        else:
            invoice = False
        return invoice


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_received(self):
        super(PurchaseOrderLine, self)._compute_qty_received()
        for line in self:
            if line.qty_received_method == 'stock_moves':
                total = 0.0
                # In case of a BOM in kit, the products delivered do not correspond to the products in
                # the PO. Therefore, we can skip them since they will be handled later on.
                for move in line.move_ids:
                    if move.state == 'done':
                        if move.location_dest_id.usage == "supplier":
                            if move.to_refund:
                                total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        elif (
                            move.location_dest_id.usage == "internal"
                            and move.to_refund
                            and move.location_dest_id
                            not in self.env["stock.location"].search(
                                [("id", "child_of", move.warehouse_id.view_location_id.id)]
                            )
                        ):
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        else:
                            total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                line.qty_received = total

    # Хөнгөлөлт
    discount = fields.Float('Хөн.%')
    price_unit_without_discount = fields.Float(
        string='Нэгж үнэ (хөнгөлөлтгүй)',
        required=True, default=0,
        digits='Product Price')

    tracking = fields.Selection(related='product_id.tracking', String="Хөтлөлт")
    lot_id = fields.Many2one('stock.production.lot', 'Цуврал')
    lot_life_date = fields.Datetime(related='lot_id.life_date', string="Дуусах хугацаа", readonly=False)
    is_diff_receive_inv = fields.Boolean('Хүлээж авсан Нэхэмжилсэн зөрүүтэй', compute='_compute_rec_qty_inv', search='_search_rec_qty_inv')
    is_diff_qty_inv = fields.Boolean('Захиалсан тоо Нэхэмжилсэн зөрүүтэй', compute='_compute_rec_qty_inv', search='_search_qty_inv')

    # @api.depends(')
    def _compute_rec_qty_inv(self):
        for item in self:
            if item.qty_received!=item.qty_invoiced:
                item.is_diff_receive_inv = True
            else:
                item.is_diff_receive_inv = False
            
            if item.product_qty!=item.qty_invoiced:
                item.is_diff_qty_inv = True
            else:
                item.is_diff_qty_inv = False

    def _search_rec_qty_inv(self, operator, value):
        ids = []
        for item in self.env['purchase.order.line'].search([]):
            if item.is_diff_receive_inv:
                ids.append(item.id)
        return [('id', 'in', ids)]

    def _search_qty_inv(self, operator, value):
        ids = []
        for item in self.env['purchase.order.line'].search([]):
            if item.is_diff_qty_inv:
                ids.append(item.id)
        return [('id', 'in', ids)]

    @api.onchange('discount', 'price_unit_without_discount')
    def onchange_discount_price_unit(self):
        self.price_unit = self.price_unit_without_discount * (1 - (self.discount or 0.0) / 100.0)

    # Хөнгөлөлттэй холбоотой функц
    @api.onchange('price_unit')
    def onchange_main_price_unit(self):
        if not self.price_unit_without_discount and self.price_unit:
            self.price_unit_without_discount = self.price_unit

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        self.price_unit_without_discount = 0.0
        return res

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        price_unit = self.price_unit
        res = super(PurchaseOrderLine, self)._onchange_quantity()
        if price_unit != self.price_unit:
            self.price_unit_without_discount = self.price_unit
        return res

    def _product_id_change(self):
        super(PurchaseOrderLine, self)._product_id_change()

        # ХА-н х.н-г үндсэнээр авах
        if self.env.company.is_change_po_uom_to_uom:
            self.product_uom = self.product_id.uom_id

        # Хөнгөлөлтийн хувийг харилцагчаас авах
        self.discount = self.partner_id.discount_percent

    # Захиалга дээр татвар сонгох
    def _compute_tax_id(self):
        # Override
        for line in self:
            line.taxes_id = line.order_id.taxes_id

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        return res
