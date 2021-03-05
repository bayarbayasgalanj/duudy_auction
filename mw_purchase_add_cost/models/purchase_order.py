# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    date_currency = fields.Date('Ханш бодох огноо', states={'done': [('readonly', True)]}, default=fields.Date.context_today)
    current_rate = fields.Float('Бодогдох Ханш', readonly=True, compute='_compute_curent_rate', store=True)
    expenses_line = fields.One2many('purchase.order.expenses', 'order_id', 'Expenses line', states={'done': [('readonly', True)]}, copy=True)
    amount_expenses = fields.Monetary(string='Нийт Зардлын Дүн', store=True, readonly=True, compute='_amount_expenses_all', currency_field='company_currency_id')
    amount_expenses_in = fields.Monetary(string='Нийт Зардлын Дүн Хувиарлагдах', readonly=True, compute='_amount_expenses_all', currency_field='company_currency_id')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True,
        help='Utility field to express amount currency')

    @api.depends('currency_id','date_currency','state')
    def _compute_curent_rate(self):
        for item in self:
            date_order = item.date_currency or fields.Datetime.now()
            rr = self.env['res.currency']._get_conversion_rate(item.currency_id, item.company_id.currency_id, item.company_id, date_order)
            item.current_rate = rr

    @api.onchange('date_currency')
    def onchange_date_currency(self):
        for item in self.expenses_line:
            item.date_cur = self.date_currency
        self.make_expenses()

    def button_approve(self, force=False):
        self.make_expenses()
        return super(PurchaseOrder,self).button_approve()

    @api.depends('order_line.invoice_lines.move_id', 'expenses_line.invoice_id')
    def _compute_invoice(self):
        for order in self:
            super(PurchaseOrder, order)._compute_invoice()
            invoices = order.expenses_line.mapped('invoice_id')
            order.invoice_ids = order.invoice_ids | invoices
            order.invoice_count = len(order.invoice_ids)

    @api.depends('expenses_line.amount')
    def _amount_expenses_all(self):
        for order in self:
            amount_expenses = 0.0
            amount_expenses_in = 0.0
            for line in order.expenses_line:
                from_currency = line.currency_id
                to_currency = order.company_currency_id
                line.current_amount = self.env['res.currency'].with_context(date=line.date_cur)._compute(from_currency, to_currency, line.amount)
                amount_expenses += line.current_amount
                if not line.is_without_cost:
                    amount_expenses_in += line.current_amount

            order.update({
                'amount_expenses': order.currency_id.round(amount_expenses),
                'amount_expenses_in': order.currency_id.round(amount_expenses_in),
            })

    def make_portion(self, method, lines, amount, date_current, expenses_line_id):
        portion_dict = {}
        total = 0.0
        # Зардлыг хуваарилах

        from_currency = self.currency_id
        to_currency = self.company_currency_id

        currency_obj = self.env['res.currency']

        if method == 'price':
            for line in lines:
                total += line.price_unit
            coff = 0
            if total:
                coff = amount / total
            for line in lines:
                product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
                cur_price_unit = currency_obj.with_context(date=date_current)._compute(from_currency, to_currency, line.price_unit)
                portion_dict[line.id] = (cur_price_unit * coff) / product_uom_qty
        elif method == 'subtotal':

            for line in lines:
                product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
                price_unit = line._get_stock_move_price_unit_unit()
                price_total = product_uom_qty * price_unit

                cost_unit = expenses_line_id.current_amount
                coff = 0
                if price_total:
                    coff = price_total / amount
                portion_dict[line.id] = cost_unit * coff

        elif method == 'volume':
            for line in lines:
                product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
                total += (line.product_id.volume or 1) * product_uom_qty
            coff = 0
            if total:
                coff = amount / total
            for line in lines:
                portion_dict[line.id] = (line.product_id.volume or 1) * coff
        elif method == 'weight':  # weight
            for line in lines:
                product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
                total += (line.product_id.weight or 1) * product_uom_qty
            coff = 0
            if total:
                coff = amount / total
            for line in lines:
                portion_dict[line.id] = (line.product_id.weight or 1) * coff
        else:
            # Зардлыг өртөгт хуваарилахгүй
            pass

        return portion_dict
    
    def _prepare_invoice_line_from_expense_line(self, line):
        qty = 1
        taxes = line.taxes_id
        print ('line.get_po_id()',line.get_po_id())
        po_id = line.get_po_id() or line.order_id 
        invoice_line_tax_ids = po_id.fiscal_position_id.map_tax(taxes)
        invoice_line = self.env['account.move.line']
        journal_obj = self.env['account.journal']
        journal_id = journal_obj.search([('type', '=', 'purchase'), ('company_id', '=', po_id.company_id.id)], limit=1)
        if not journal_id:
            raise UserError(_('There is no purchase journal defined for this company: "%s" (id:%d)') % (po_id.company_id.name, po_id.company_id.id))
        # if not journal_id.default_debit_account_id:
        #     raise UserError(_('Please configure debit account on %s journal') % (journal_id.name))
        from_currency = line.currency_id
        to_currency = po_id.company_currency_id
        data = {
            'name': po_id.name + ': Expense ' + line.portion_method,
            'product_uom_id': line.product_id.uom_id.id,
            'product_id': line.product_id.id,
            # 'account_id' : invoice_line._get_computed_account()
            # 'account_id': journal_id.default_debit_account_id.id,
            'price_unit': line.amount,  # tuhain valutaar uusgeh
            'quantity': qty,
            'discount': 0.0,
            'tax_ids': invoice_line_tax_ids.ids
        }
        data['account_id'] = invoice_line.new(data)._get_computed_account()
        return (0, False, data)

    def create_expense_invoice(self):
        self.create_expense_invoice_hand(self.expenses_line, self.company_id, self.name)

    def create_expense_invoice_hand(self, expenses_line, company_id, name):
        partners = expenses_line.filtered(lambda r: not r.invoice_id or r.invoice_id.state == 'cancel').mapped('partner_id')
        currency_ids = expenses_line.filtered(lambda r: not r.invoice_id or r.invoice_id.state == 'cancel').mapped('currency_id')
        journal_obj = self.env['account.journal']
        n=1
        for partner in partners:
            for cur in currency_ids:
                invoice_line = []
                currency_id = cur
                reference_val = []
                expense_lines = expenses_line.filtered(lambda r: r.partner_id.id == partner.id and r.currency_id.id == cur.id)
                for expense_line in expense_lines:
                    invoice_line.append(self._prepare_invoice_line_from_expense_line(expense_line))
                    if expense_line.invoice_ref:
                        reference_val.append(expense_line.invoice_ref)
                a = partner.property_account_payable_id.id
                if not a:
                    raise UserError(_('There isn\'t any payable account defined in this partner. %s(id:%s)') % (partner.name, partner.id))
                journal_ids = journal_obj.search([('type', '=', 'purchase'), ('company_id', '=', company_id.id)], limit=1, order='id')
                if not journal_ids:
                    raise UserError(_('There is no purchase journal defined for this company: "%s" (id:%d)') % (company_id.name, company_id.id))

                inv_vals = {
                    # 'name': 'Exp: %s' % self.name,
                    'name': '/',
                    'ref': 'Exp: '+(', '.join(reference_val) or '')+' '+cur.display_name+' - '+name+' - '+str(n),
                    # 'account_id': a,
                    'type': 'in_invoice',
                    'partner_id': partner.id,
                    'journal_id': journal_ids.id or False,
                    'invoice_origin': name,
                    'invoice_line_ids': invoice_line,
                    'company_id': company_id.id,
                    'invoice_date': datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'user_id': self.env.user.id,
                    'currency_id': currency_id.id
                }
                created_invoice = self.env['account.move'].create(inv_vals)
                # zardal-iin nehemjleh shuud batlagddag bolgov
                # turdee jur deer butsaav
                # created_invoice.action_post()
                n+=1
                for inv_line in created_invoice.invoice_line_ids:
                    for expense_line in expense_lines:
                        if expense_line.is_without_cost:
                            account = inv_line._get_computed_account()
                            if account:
                                inv_line.account_id = account
                            else:
                                raise UserError('Өртөгд оруулахгүй барааны дансны тохиргоо байхгүй байна.')
                        else:
                            account_ids = []
                            account = inv_line._get_computed_account()
                            account_ids.append(account.id)
                            # for pol in self.order_line:
                            #     account = inv_line._get_computed_account()
                            #     account_ids.append(account.id)
                            account_ids = list(set(account_ids))
                            account_id = False
                            if len(account_ids) == 1:
                                account_id = account_ids[0]
                            else:
                                raise UserError(_('Өөр ангилалын барааг орлого авахад замд яваа бараа данснуудад өртөг салж хуваарилагдах ёстой [%s]') % (account_ids))
                            if account_id:
                                inv_line.account_id = account_id

                expenses_line.filtered(lambda r: r.partner_id.id == partner.id and r.currency_id.id == cur.id).write({'invoice_id': created_invoice.id})

    def make_expenses_line(self, expenses_line):
        for item in expenses_line:
            amount = 0.0
            selected_lines = item.purchase_lines
            if not selected_lines:
                selected_lines = self.order_line
            from_currency = item.order_id.currency_id
            to_currency = self.company_currency_id
            for pol in selected_lines:
                product_uom_qty = pol.product_uom._compute_quantity(pol.product_qty, pol.product_id.uom_id)
                price_unit = pol._get_stock_move_price_unit_unit()
                amount += product_uom_qty * price_unit

            portion_dict = self.make_portion(item.portion_method, selected_lines, amount, item.date_cur, item)
            for line in selected_lines:
                product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
                line.cost_unit += portion_dict[line.id] / product_uom_qty

    def make_expenses(self):
        self.order_line.update({'cost_unit': 0})
        self._amount_expenses_all()
        self.make_expenses_line(self.expenses_line.filtered(lambda r: not r.is_without_cost))


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    cost_unit = fields.Float(string='Зардлын Дүн', readonly=True, copy=False, digits=dp.get_precision('Product Price'))
    total_cost_unit = fields.Float(string='Нийт Зардлын Дүн', readonly=True, digits=dp.get_precision('Product Price'), compute='_compute_total_cost_unit')
    price_unit_product = fields.Float(string='Барааны үндсэн Өртөг', compute='_compute_price_unit_stock_move', readonly=True, digits=dp.get_precision('Product Price'))
    price_unit_stock_move = fields.Float(string='Өртөг', compute='_compute_price_unit_stock_move', readonly=True, digits=dp.get_precision('Product Price'))
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True, help='Utility field to express amount currency')

    @api.depends('cost_unit','product_qty','product_uom')
    def _compute_total_cost_unit(self):
        for item in self:
            product_uom_qty = item.product_uom._compute_quantity(item.product_qty, item.product_id.uom_id)
            item.total_cost_unit = item.cost_unit*item.product_uom_qty

    @api.depends('price_unit', 'product_id', 'taxes_id', 'order_id.date_currency', 'order_id.currency_id', 'cost_unit')
    def _compute_price_unit_stock_move(self):
        for line in self:
            line.price_unit_stock_move = line._get_stock_move_price_unit()
            line.price_unit_product = line.price_unit_stock_move - line.cost_unit
    
    def get_date_currency(self):
        return self.order_id.date_currency

    def _get_stock_move_price_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id, partner=line.order_id.partner_id)['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            if line.product_id.uom_id.factor != 0:
                price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            from_currency = order.currency_id
            to_currency = order.company_currency_id
            price_unit = self.env['res.currency'].with_context(date=self.get_date_currency())._compute(from_currency, to_currency, price_unit, round=False)
        if line.cost_unit:
            price_unit = price_unit + line.cost_unit
        return price_unit

    def _get_stock_move_price_unit_unit(self):
        self.ensure_one()
        line = self[0]
        order = line.order_id
        price_unit = line.price_unit
        if line.taxes_id:
            price_unit = line.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=line.order_id.currency_id, quantity=1.0, product=line.product_id, partner=line.order_id.partner_id
            )['total_excluded']
        if line.product_uom.id != line.product_id.uom_id.id:
            price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            from_currency = order.currency_id
            to_currency = order.company_currency_id
            price_unit = self.env['res.currency'].with_context(date=self.get_date_currency())._compute(from_currency, to_currency, price_unit, round=False)

        return price_unit
