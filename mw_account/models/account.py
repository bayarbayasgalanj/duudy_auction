# -*- coding: utf-8 -*-

import time
import math

from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round
from odoo.tools import float_is_zero, float_compare
import datetime

# Шинжилгээний дансны тохируулга
class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouse")
    product_ids = fields.Many2many('product.template', string='Product templates')

    
    def write(self, vals):
        res = super(AccountAnalyticAccount, self).write(vals)
        objs = self.env['account.analytic.account'].search([
            ('warehouse_ids','in',self.warehouse_ids.ids),
            ('product_ids','in',self.product_ids.ids)])
        if len(objs) > 1:
            raise UserError(('Агуулах, барааны мэдээлэл давхардсан байна!'))
        return res

class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account"

    name = fields.Char(required=True, index=True, translate=True, )
    cmtype_ids = fields.Many2many('account.cash.move.type', 'account_account_cmt_rel', 'account_id', 'cmt_id', string="Cash move types", copy=False)
    analytic_account_ids = fields.Many2many('account.analytic.account', 'account_analytic_rel', 'account_id', 'analytic_id', string="Analytic accounts", copy=False)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic accounts", copy=False)
    is_temporary = fields.Boolean('Is temporary?') 
    
    is_stock = fields.Boolean('Is stock?') 
    is_recpay = fields.Boolean('On partner report?') 
    is_sale_return = fields.Boolean('Is sale return?') 
    is_employee_recpay = fields.Boolean('Ажилтны авлага?') 

    def repair_hierarchy(self,params):
        # print "repair_hierarchy",params
#         self._parent_store_compute(cr)
        return True

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
#         print 'args-- ',args
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()

            
    def _compute_data(self):
        mapping = {
            'balance': "COALESCE(SUM(l.debit),0) " \
                       "- COALESCE(SUM(l.credit), 0) as balance",
            'debit': "COALESCE(SUM(l.debit), 0) as debit",
            'credit': "COALESCE(SUM(l.credit), 0) as credit"
        }
        cr = self.env.cr
#         children_and_consolidated = self._get_children_and_consol()
        accounts = {}
        accounts2 = {}
        sums = {}
        sums2 = {}
        check_initial = True
        field_names=['debit', 'credit', 'balance']
#         if children_and_consolidated:
        context = dict(self._context or {})
#         print ('context+++++++++:  ',context)
        MoveLine = self.env['account.move.line']
        tables, where_clause, where_params = MoveLine._query_get()
        # print 'where_params ',where_params
#             params = (tuple(children_and_consolidated),) + tuple(where_params)
        # print 'self',self.ids
        params =  (tuple(self.ids),) + tuple(where_params)
#            Тайлант хугацаа
        
#             aml_query = self.env['account.move.line')._query_get(cr, uid, context=context)
        partner_where=""
        partner_id=context.get('partner_id',False) 
        if partner_id:
            partner_where=" AND l.partner_id={0} ".format(partner_id)
        wheres = [""]
        print ('partner_where ',partner_where)
        if where_clause.strip():
            wheres.append(where_clause.strip())

#            Эцсийн үлдэгдэл
        filters = " AND ".join(wheres)
#         print ('wheres------------- ',wheres)
        filters = filters.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
#             logger.debug('addons.'+account_obj._name, netsvc.LOG_DEBUG,
#                                       'Filters: %s'%filters)
#         _logger.info('addons.'+str(self.ids)+'Filters: %s'%filters)
        
        request = ("SELECT l.account_id as id, " +\
                   ', '.join(map(mapping.__getitem__, field_names)) +
                   " FROM account_move_line l left join " \
                   "       account_move m on l.move_id=m.id " \
                   " WHERE l.account_id IN %s " \
                        + filters +" "+ partner_where+
                   " GROUP BY l.account_id")
        self.env.cr.execute(request, params)

        for res in self.env.cr.dictfetchall():
            accounts[res['id']] = res
#            Эхний үлдэгдэл. Өмнөх жилийн Хаалт хийсэн бөгөөд тайлангийн эхний огноо
#             жилийн эхний огноотой давхцаж байвал.
#                 
# #            Зөвхөн эхний үлдэгдлийн бичилтийг шүүх
#         1031
#         if self.user_type_id.
        state=context.get('target_move',False) and context['target_move'] or context.get('state',False) and context['state'] or 'posted'
        date_from=context.get('date_from',False) and context['date_from'] or time.strftime('%Y-%m-%d')
        company_id=context.get('company_id',False) and context['company_id'] or self.env.user.company_id and self.env.user.company_id.id or 1
        if not isinstance(date_from, datetime.datetime):
            if isinstance(date_from,str):
                date_from=datetime.date(int(date_from.split('-')[0]),int(date_from.split('-')[1]),int(date_from.split('-')[2]))
        tables_start, where_clause_start, where_params_start = MoveLine.with_context(date_from=date_from, 
                                                                      state=state,
                                                                      date_to=False, strict_range=True, initial_bal=True)._query_get()
        params_start = (tuple(self.ids),) + tuple(where_params_start)
#            Тайлант хугацаа
#             print "self.env.context+++++++++++++++++ ",self.env.context
        
#             aml_query = self.env['account.move.line')._query_get(cr, uid, context=context)
        wheres_start = [""]
        if where_clause_start.strip():
            wheres_start.append(where_clause_start.strip())

        filters_start = " AND ".join(wheres_start)
        filters_start = filters_start.replace('account_move_line__move_id', 'm').replace('account_move_line', 'l')
#             logger.debug('addons.'+account_obj._name, netsvc.LOG_DEBUG,
#                                       'Filters: %s'%filters)
#         _logger.info('addons.'+str(self.ids)+'filters_start: %s'%filters_start)
        request_start = ("SELECT l.account_id as id, " +\
                   ', '.join(map(mapping.__getitem__, field_names)) +
                   " FROM account_move_line l left join " \
                   "       account_move m on l.move_id=m.id " \
                   " WHERE l.account_id IN %s " \
                        + filters_start + " "+partner_where+
                   " GROUP BY l.account_id")
        field_names.append('starting_balance')
        self.env.cr.execute(request_start, params_start)
#             self.logger.notifyChannel('addons.'+account_obj._name, netsvc.LOG_DEBUG,
#                                       'Status: %s'%self.env.cr.statusmessage)
#             _logger.info('addons.'+self.name+'Status: %s'%self.env.cr.statusmessage)

        for res in self.env.cr.dictfetchall():
            accounts2[res['id']] = res

#             self.env.cr.execute(request_start, params)
# #            Шүүгдсэн дансны эхний үлдэгдлийн журналд бичигдсэн бичилтийг шүүх 
#         children_and_consolidated.reverse()
#         brs = list(self.browse(children_and_consolidated))
#             print "children_and_consolidated ",children_and_consolidated
        currency_obj = self.env['res.currency']
#         while brs:
#             current = brs.pop(0)
        for current in self:
            # print 'account---- ',current
            for fn in field_names:
#                    'starting_balance'-д balance ийн дүнг өгнө
                if fn=='starting_balance':
                    sums.setdefault(current.id, {})[fn] = accounts2.get(current.id, {}).get('balance', 0.0)
                else:
                    sums.setdefault(current.id, {})[fn] = accounts.get(current.id, {}).get(fn, 0.0)
#                 for child in current.child_id:
#                     if child.company_id.currency_id.id == current.company_id.currency_id.id:
#                         sums[current.id][fn] += sums[child.id][fn]
#                     else:
#                         sums[current.id][fn] += currency_obj.compute(cr, self._uid, child.company_id.currency_id.id, current.company_id.currency_id.id, sums[child.id][fn], context=context)
        res = {}
        #0.0 оор цэнэглэж {'credit': 0.0, 'balance': 0.0, 'debit': 0.0} хэлбэрийн dic үүсгэх
#        field_names.extend(report_fields)
        null_result = dict((fn, 0.0) for fn in field_names)
        unaffected_earnings_type = self.env.ref("account.data_unaffected_earnings")
#         print ('unaffected_earnings_type ',unaffected_earnings_type)
#         print ('company_id ',company_id)
        earning_accounts=self.search([('user_type_id','=',unaffected_earnings_type.id),('company_id','=',company_id)])
#         print ('a',earning_accounts)
        if len(earning_accounts)!=1:
            raise UserError((u'Энэ компани дээр хуримтлагдсан ашиг төрөлтэй данс байхгүй эсвэл олон байна. Эсвэл компаний мэдээллээ буруу сонгосон байна'))
        earning_account=earning_accounts[0]
        for id in self.ids: 
            #earnings түр дансдын зөрүүгээр харуулдаг данс, хаах илүү үйлдэл хийхгүй.
            #Хэрэв 410100 данс дээр тайлант үед гүйлгээ гарсан бол дараагийн тайлант хугацаанд хэрхэн харуулахыг засах шаардлагатайм байна.
            #Ер нь бол өмнөх үеийнхруу бичүүлэх нь зөв байх.
            if id==earning_account.id:
                
#                            "    AND l.date < %s  AND  l.date >= %s " \
# date_from.split('-')[0]+'-01-01',
                #түр дансдын нийлбэр дүн гарна. Тиймээс өмнөх үеийн гүйлгээг энд бичхгүй байх.
                if state =='all':
                    state_where=' AND m.state in (\'draft\',\'posted\')'
                else:
                    state_where=' AND m.state=\'posted\''
#                 params3=(earning_account.id,earning_account.id,date_from.split('-')[0]+'-01-01',company_id)
                params3=(earning_account.id,earning_account.id,str(date_from.year)+'-01-01',company_id)
                request3 = ("SELECT %s as id, " +\
                           "COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance " \
                           " FROM account_move_line l " \
                           "       left join account_move m "
                           "           on l.move_id=m.id " \
                           "       left join account_account a " \
                           "            on l.account_id = a.id " \
                           "       LEFT JOIN account_account_type at " \
                           "         ON at.id = a.user_type_id " \
                           " WHERE l.account_id <> %s " \
                           "    AND at.include_initial_balance = FALSE " \
                           "    AND l.date < %s " \
                           "    AND l.company_id=%s " \
                           " "+state_where)
                self.env.cr.execute(request3, params3)
                for r in self.env.cr.dictfetchall():
                    sums[r['id']]['starting_balance'] = r['balance']
            #earnings
            res[id] = sums.get(id, null_result)
        for s in self:
            s.balance=res[s.id]['balance']+res[s.id]['starting_balance']
            s.balance_start=res[s.id]['starting_balance']
            s.debit=res[s.id]['debit']
            s.credit=res[s.id]['credit']
#             print ('s.code ',s.code)
#             print ('s.balance ',s.balance)
                        
    balance = fields.Float(compute='_compute_data', string='Balance')
    balance_start = fields.Float(compute='_compute_data', string='Balance start')
    debit = fields.Float(compute='_compute_data', string='Debit')
    credit = fields.Float(compute='_compute_data', string='Credit')
                
#             res += account_obj.currency_equalize(account_ids1,form.date, 
#                     form.company_id, form.journal_id.id, form.name)

    def currency_equalize_mn(self, date, company, journal_id, narration):
#         if context is None:
#             context = {}
        cur_obj = self.env['res.currency']
        amove_line_obj = self.env['account.move.line']
        amove_obj = self.env['account.move']

        res = []
        ctx = self.env.context.copy()
        ctx['date_from'] = date.split('-')[0]+'-01-01'
        ctx['date_to'] = date
        ctx['state'] = 'posted'
        ctx['company_id'] = company.id
#         ctx['fiscalyear'] = period.fiscalyear_id.id

        # Тайлант хугацааны гадаад валютаарх үлдэгдлийг тооцоолох
        self.env.cr.execute("SELECT l.account_id, COALESCE(SUM(l.amount_currency), 0) "
                   "FROM account_move_line l "
                   "LEFT JOIN account_account a ON l.account_id = a.id "
                   "LEFT JOIN account_move m ON m.id = l.move_id "
                   "WHERE m.state = 'posted' "
                   "AND l.date <= %s and l.company_id = %s "
                   "AND l.account_id in %s "
                   "GROUP BY l.account_id ",
            (date, company.id, tuple(self.ids)))
        amount_currency_dict = dict(self.env.cr.fetchall())
        for account_id in self:
#         for account in self.browse(cr, uid, ids, context=ctx) :
            account=account_id.with_context(ctx) 

            if not account.currency_id or account.currency_id.id == company.currency_id.id :
                continue

            # Тайлант хугацааны төгрөгөөрх үлдэгдэл
            if account.user_type_id.balance_type in ('active') :
                balance = account.debit - account.credit
            else :
                balance = account.credit - account.debit
#             print 'balance ',balance
            amount_currency = amount_currency_dict.get(account.id, 0)
#             print 'amount_currency ',amount_currency
#             converted_amount = cur_obj.compute(cr, uid, account.currency_id.id, company.currency_id.id,
#                         amount_currency, context={'date':date, 'lang':context.get('lang', 'en_US')})
            converted_amount = self.env['res.currency'].with_context(date=date)._compute(account.currency_id, company.currency_id, amount_currency, round=False)
#             print 'account ',account.code
#             print 'converted_amount ',converted_amount
            diff_amount = converted_amount - balance
            if diff_amount==0:
#             if cur_obj.is_zero(cr, uid, company.currency_id, diff_amount) :
                # Ханшийн зөрүү үүсээгүй болно.
                continue
# 
#             move_id = amove_obj.create({
#                         'journal_id': journal_id,
# #                         'period_id': period.id,
#                         'date': date,
#                         'narration': narration
#             })
#             res.append(move_id)
            if diff_amount > 0 :
                # Ханшийн зөрүүний ашиг
                a = company.income_currency_exchange_account_id.id
                if not a :
                    raise osv.except_osv(_('Warning!'), _('There is no income currency rate account defined for this company : %s') % company.name)
            else :
                # Ханшийн зөрүүний алдагдал
                a = company.expense_currency_exchange_account_id.id
                if not a :
                    raise osv.except_osv(_('Warning!'), _('There is no expense currency rate account defined for this company : %s') % company.name)

            # Ханшийн зөрүүг журналд бичих
            line_vals=[]
#                 new_line_id1 = account_move_line_obj.create({
            line_vals.append([0,0,{
                'name': u'%s дансны ханшийн тэгшитгэл' % account.name,
                'debit': (diff_amount < 0 and -diff_amount) or 0.0,
                'credit': (diff_amount > 0 and diff_amount) or 0.0,
                'account_id': a,
                'partner_id': False,
                'amount_currency': 0,
                'company_id': company.id,
                'currency_id': False,
#                 'move_id': move_id,
                'date': date,
                'journal_id': journal_id,
#                 'period_id': period.id
            }])
            line_vals.append([0,0,{
                'name': u'%s дансны ханшийн тэгшитгэл' % account.name,
                'debit': (diff_amount > 0 and diff_amount) or 0.0,
                'credit': (diff_amount < 0 and -diff_amount) or 0.0,
                'account_id': account.id,
                'partner_id': False,
                'amount_currency': 0,
                'company_id': company.id,
                'currency_id': account.currency_id.id,
#                 'move_id': move_id,
                'date': date,
                'journal_id': journal_id,
#                 'period_id': period.id
            }])

            move_id = amove_obj.create({
                'journal_id': journal_id,
    #                         'period_id': period.id,
                'date': date,
                'narration': narration,
#                'name': u'%s ханш тэгшитгэл' % (line.account_id.code+' '+form.name or '',),
                'line_ids': line_vals
            })
#                 print 'move_id ',move_id
            res.append(move_id.id)
        return res
                    
class AccountCashMoveType(models.Model):
    _name = 'account.cash.move.type'
    _description = 'Cash Move Type'

    TYPE_SELECTION = [
        ('activities_income', 'Cash flows income from operating activities'),
        ('activities_expense', 'Cash flows expense from operating activities'),
        ('investing_income', 'Cash flows income from investing activities'),
        ('investing_expense', 'Cash flows expense from investing activities'),
        ('financing_income', 'Cash flows income from financing activities'),
        ('financing_expense', 'Cash flows expense from financing activities'),
        ('dummy', 'Non affects in statements')
    ]

#     def name_get(self,context=None):
#         if context is None:
#             context = {}
#         def _name_get(d):
#             name = d.get('name','')
#             code = d.get('code',False)
#             if code:
#                 name = '[%s] %s' % (code,name)
#             return (d['id'], name)
# 
#         result = []
#         for group in self:
#                 mydict = {
#                           'id': group.id,
#                           'name': group.name_mn,
#                         #    'code': group.code,
#                           }
#                 result.append(_name_get(mydict))
#         return result

    INCOME_SELECTION = [
        ('income','Income'),
        ('expense','Expense'),
        (' ',' '),
    ]

    name = fields.Char('Name', size=100, required=True)
    #  'group = fields.selection(TYPE_SELECTION, 'Group', required=True)
    group_name = fields.Selection(TYPE_SELECTION, 'Group', required=True)
    sequence = fields.Integer('Sequence', help="This sequence is used when generate statement of cash flows report. Sequence is ordered into the groups.")
    name_en = fields.Char('Name mn', size=100, required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    is_income = fields.Selection(INCOME_SELECTION, 'TYPE', required=True)
    number = fields.Char('Number', size=10, required=True)
    bank_line_ids = fields.One2many('account.bank.statement.line', 'cash_type_id', string='Lines',)


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('number', '=ilike', '%' + name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()

    @api.depends('name', 'number')
    def name_get(self):
        result = []
        for account in self:
            name = account.number + ' ' + account.name
            result.append((account.id, name))
        return result
    
class AccountCashSkipConf(models.Model):
    _name = 'account.cash.skip.conf'
    _description = 'Cash Move skip config'

    name = fields.Char('Name', size=100, required=True)
    skip_journal_ids = fields.Many2many('account.journal', relation='account_cash_flow_skip_journals')

    
class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
    _description = "Bank Statement line"

    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")
    

class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    balance_type = fields.Selection([
        ('active', 'Active'),
        ('passive', 'Passive'),
    ],  default='active',)

    close_method = fields.Selection([
        ('none', 'none'),
        ('balance', 'balance'),
        ('unreconciled', 'unreconciled'),
    ],  default='none',)
    

# class AccountMoveLineReconcile(models.TransientModel):
#     _inherit = 'account.move.line.reconcile'
#     _description = 'Account move line reconcile'
# 
#     
#     def trans_rec_get(self):
#         context = self._context or {}
#         credit = debit = 0
#         lines = self.env['account.move.line'].browse(context.get('active_ids', []))
#         for line in lines:
#             if not line.full_reconcile_id:
#                 credit += line.credit
#                 debit += line.debit
#         precision = self.env.user.company_id.currency_id.decimal_places
#         writeoff = float_round(debit - credit, precision_digits=precision)
#         credit = float_round(credit, precision_digits=precision)
#         debit = float_round(debit, precision_digits=precision)
#         return {'trans_nbr': len(lines), 'credit': credit, 'debit': debit, 'writeoff': abs(writeoff)}
      

class account_move(models.Model):
    _inherit  = 'account.move'
     

    from_ref = fields.Boolean("From ref")

    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        
        _get_fields_onchange_subtotal_model д нийт дүнг дахин валютаар бодоход дэд дүнгүүдийн нийлбэрээс зөрж байгаа тул хүчээр тулгах
1,920,716.40    0.00    696.00    696.00    2,759.65    1,920,716.4000                0.0000    1,920,716.4000
4,532,725.13    0.00    1,642.50    1,642.50    2,759.65    4,532,725.1300                0.0050    4,532,725.1250
6,342,338.02    0.00    2,298.24    2,298.24    2,759.65    6,342,338.0200                0.0040    6,342,338.0160
11,535,337.00    0.00    4,180.00    4,180.00    2,759.65    11,535,337.0000                0.0000    11,535,337.0000
12,453,196.59    0.00    4,512.60    4,512.60    2,759.65    12,453,196.5900                0.0000    12,453,196.5900
14,047,722.36    0.00    5,090.40    5,090.40    2,759.65    14,047,722.3600                0.0000    14,047,722.3600
21,172,034.80    0.00    7,672.00    7,672.00    2,759.65    21,172,034.8000                0.0000    21,172,034.8000
22,871,979.20    0.00    8,288.00    8,288.00    2,759.65    22,871,979.2000                0.0000    22,871,979.2000
22,949,249.40    0.00    8,316.00    8,316.00    2,759.65    22,949,249.4000                0.0000    22,949,249.4000
30,491,372.85    0.00    11,049.00    11,049.00    2,759.65    30,491,372.8500                0.0000    30,491,372.8500
35,334,558.60    0.00    12,804.00    12,804.00    2,759.65    35,334,558.6000                0.0000    35,334,558.6000
37,006,906.50    0.00    13,410.00    13,410.00    2,759.65    37,006,906.5000                0.0000    37,006,906.5000
37,255,275.00    0.00    13,500.00    13,500.00    2,759.65    37,255,275.0000                0.0000    37,255,275.0000
37,503,643.50    0.00    13,590.00    13,590.00    2,759.65    37,503,643.5000        378196896.6        0.0000    37,503,643.5000
39,585,799.43    0.00    14,344.50    14,344.50    2,759.65    39,585,799.4300        137045.24        0.0050    39,585,799.4250
43,194,041.80    0.00    15,652.00    15,652.00    2,759.65    43,194,041.8000        2759.65        0.0000    43,194,041.8000
378,196,896.57            137,045.24    2,759.65    378,196,896.58    378,196,896.57            0.0140    378,196,896.5660      
20200413 butsaaj neev  
        '''
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(['debit', 'credit', 'move_id'])
        self.env['account.move'].flush(['journal_id'])
#         print ('self.ids ',self.ids)
#         for b in self:
#             print ('b------ ',b)
#             for l in b.line_ids:
#                 print ('l ',l)
#                 print ('lmove_id---- ',l.move_id)
#                 print ('ldebit ',l.debit)
#                 print ('lcredit ',l.credit)
#                 print ('l ',l.name)
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(debit - credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(debit - credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
#         print ('query_res ',query_res)
        if query_res:
#             print ('query_res ',query_res)
            is_po_stock = False
            if self.stock_move_id.purchase_line_id:
                is_po_stock = True
            for line in self:
                is_inv=line.is_invoice(include_receipts=True)
#             is_inv=self.is_invoice(include_receipts=True)
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
#             print ('sums ',sums)
#             print ('is_inv ',is_inv)
            if is_inv or is_po_stock:#Худалдан авалтын нэхэмжлэх бол валюттай бол.
                if abs(sums[0])<50.5:#Бага зөрүүтэй бол
                    #ХА лт
#                     print (a)
                    if self.type=='in_invoice' or self.type=='entry':
                        for ll in self.line_ids.filtered(lambda line: line.debit>0):
                        # for ll in self.line_ids.filtered(lambda line: line.debit>0 and line.amount_currency!=0):
                            # үүний дараа write д _check_balanced дахин шалгаад 0 бол батлагдана
                            ll.debit = ll.debit-sums[0]
#                             print ('ll.debit ',ll.debit)
#                             print ('sums[0] ',sums[0])
                            break
#                         self._check_balanced()
#                 Дахин шалгах
                
                self.env['account.move.line'].flush(['debit', 'credit', 'move_id'])
                self.env['account.move'].flush(['journal_id'])
                self._cr.execute('''
                    SELECT line.move_id, ROUND(SUM(debit - credit), currency.decimal_places)
                    FROM account_move_line line
                    JOIN account_move move ON move.id = line.move_id
                    JOIN account_journal journal ON journal.id = move.journal_id
                    JOIN res_company company ON company.id = journal.company_id
                    JOIN res_currency currency ON currency.id = company.currency_id
                    WHERE line.move_id IN %s
                    GROUP BY line.move_id, currency.decimal_places
                    HAVING ROUND(SUM(debit - credit), currency.decimal_places) != 0.0;
                ''', [tuple(self.ids)])
        
                query_res_d = self._cr.fetchall()
                if not query_res_d:
                    return True
#             print (a)
            if abs(sums[0])>0.05:
                raise UserError(_("Cannot create unbalanced journal entry. 22 Ids: %s\nDifferences debit - credit: %s") % (ids, sums))
            else:
                return True


    def _reverse_move_vals(self, default_values, cancel=True):
        ''' Reverse values passed as parameter being the copied values of the original journal entry.
        For example, debit / credit must be switched. The tax lines must be edited in case of refunds.

        :param default_values:  A copy_date of the original journal entry.
        :param cancel:          A flag indicating the reverse is made to cancel the original journal entry.
        :return:                The updated default_values.
        '''
        self.ensure_one()
        
        move_vals=super(account_move, self)._reverse_move_vals(default_values, cancel)
        for line_command in move_vals.get('line_ids', []):
            line_vals = line_command[2]  # (0, 0, {...})

            # ==== Inverse debit / credit / amount_currency ====
            balance = line_vals['credit'] - line_vals['debit']
            if move_vals['type']== 'out_refund':
                if not line_vals.get('tax_repartition_line_id') and balance<0: #super deer bol :balance>0:
#                     print ('-----------------------------------------')
                    account_id=self.env['account.account'].search([('is_sale_return','=',True)],limit=1)
                    if account_id:
                        line_vals.update({
                            'account_id': account_id.id,
                        })
                
        return move_vals
            
    def self_partner(self,ids):
        line=self.browse(ids)
        partner=''
        if line.partner_id:
            partner = line.partner_id.name
        return partner

    
    def get_order_line_ttjv(self, ids):
        context=self._context
        print_payment=False
        if context.get('print_payment',False):
            print_payment=True
        if print_payment:
            headers = [
            u'Date',
#            u'Account type',
            u'Name',
            u'Account name',
            u'Currency',
            u'Amount currency',
            u'Debit',
            u'Credit',
            u'Payment amount',
            u'Journal number',
            u'Transaction text',
            u'Our bank',
            ]
        else:
            headers = [
            u'Date',
            u'Account type',
            u'Ledger Account',
            u'Account name',
            u'Currency',
            u'Amount currency',
            u'Debit',
            u'Credit',
            u'department',
            u'Journal number',
            u'Transaction text',
            ]
        datas = []
        report_id = self.browse(ids)

        i = 1

        lines = report_id.line_ids
        sum1 = 0
        sum2 = 0
        sum3 = 0
#         print 'lines ',lines
        for line in lines:
            if print_payment:
                temp = [
#                 (report_id.date),
                        '',
#                 (line.account_id.internal_type), 
                (line.partner_id and line.partner_id.name or ''), 
               (line.account_id.name), 
                (line.currency_id and line.currency_id.name or 'MNT'),
                (line.amount_currency!=0 and abs(line.amount_currency) or ''),
                u'<p style="text-align: right;">'+("{0:,.2f}".format(line.debit) or '')+u'</p>',
                u'<p style="text-align: right;">'+("{0:,.2f}".format(line.credit) or '')+u'</p>',
                u'<p style="text-align: right;">'+''+u'</p>',
#                 (line.analytic_account_id and line.analytic_account_id.code or ''),
                (report_id.name),
                (line.name[:50]+' ..'),
                u'<p style="text-align: right;">'+''+u'</p>',
                ]
                datas.append(temp)
                if line.matched_debit_ids:
                    for pline in  line.matched_debit_ids:
                        pay=0
                        jcode=''
                        if pline.debit_move_id:
                            mline=pline.debit_move_id
#                         else:
#                             mline=pline.debit_move_id
                        if mline.credit:
                            pay=mline.credit
                        elif mline.debit:
                            pay=mline.debit
                        if mline.journal_id.code:
                            jcode=mline.journal_id.code
                        temp = [
                        (mline.date),
        #                 (line.account_id.internal_type), 
                        (mline.partner_id and mline.partner_id.name or ''), 
                       (mline.account_id.name), 
                        (mline.currency_id and mline.currency_id.name or 'MNT'),
                        (mline.amount_currency!=0 and abs(mline.amount_currency) or ''),
                        u'<p style="text-align: right;">'+''+u'</p>',
                        u'<p style="text-align: right;">'+''+u'</p>',
                        u'<p style="text-align: right;">'+("{0:,.2f}".format(pay) or '')+u'</p>',
        #                 (line.analytic_account_id and line.analytic_account_id.code or ''),
                        (mline.move_id.name),
                        (mline.name[:50]+' ..'),
                        (jcode),
                        ]   
                        datas.append(temp)
                if line.matched_credit_ids:
                    for pline in  line.matched_credit_ids:
                        pay=0
                        jcode=''
                        if pline.credit_move_id:
                            mline=pline.credit_move_id
#                         else:
#                             mline=pline.debit_move_id
                        if mline.credit:
                            pay=mline.credit
                        elif mline.debit:
                            pay=mline.debit
                        if mline.journal_id.code:
                            jcode=mline.journal_id.code
                        temp = [
                        (mline.date),
        #                 (line.account_id.internal_type), 
                        (mline.partner_id and mline.partner_id.name or ''), 
                       (mline.account_id.name), 
                        (mline.currency_id and mline.currency_id.name or 'MNT'),
                        (mline.amount_currency!=0 and abs(mline.amount_currency) or ''),
                        u'<p style="text-align: right;">'+''+u'</p>',
                        u'<p style="text-align: right;">'+''+u'</p>',
                        u'<p style="text-align: right;">'+("{0:,.2f}".format(pay) or '')+u'</p>',
        #                 (line.analytic_account_id and line.analytic_account_id.code or ''),
                        (mline.move_id.name),
                        (mline.name[:50]+' ..'),
                        (jcode),
                        ]   
                        datas.append(temp)
            else:
                temp = [
                (report_id.date),
                (line.account_id.internal_type), 
                (line.account_id.code), 
               (line.account_id.name), 
                (line.currency_id and line.currency_id.name or 'MNT'),
                (line.amount_currency!=0 and abs(line.amount_currency) or ''),
                u'<p style="text-align: right;">'+("{0:,.2f}".format(line.debit) or '')+u'</p>',
                u'<p style="text-align: right;">'+("{0:,.2f}".format(line.credit) or '')+u'</p>',
                (line.analytic_account_id and line.analytic_account_id.code or ''),
                (report_id.name),
                (line.name[:50]+' ..'),
                ]
                datas.append(temp)
            i += 1
        
        # datas.append(temp)
        res = {'header': headers, 'data':datas}
        return res
     

    def get_order_line(self, ids):
        context=self._context
        print_payment=False
        if context.get('print_payment',False):
            print_payment=True
        if print_payment:
            headers = [
            u'Date',
#            u'Account type',
            u'Name',
            u'Account name',
            u'Currency',
            u'Amount currency',
            u'Debit',
            u'Credit',
            u'Payment amount',
            u'Journal number',
            u'Transaction text',
            u'Our bank',
            ]
        else:
            headers = [
            u'№',
            u'Огноо',
            u'Дугаар',
            u'Гүйлгээний утга',
            u'Дебет',
            u'Кредит',
            ]
        datas = []
        report_ids = self.search([('id','in',ids)])
#         print ('report_ids ',report_ids)
        i = 1
        for report_id in report_ids:
            lines = report_id.line_ids
            sum1 = 0
            sum2 = 0
            sum3 = 0
    #         print 'lines ',lines
            for line in lines:
                temp = [
                (str(i)),
                str(report_id.date),
                (report_id.name), 
                (line.name), 
                u'<p style="text-align: right;">'+("{0:,.2f}".format(line.debit) or '')+u'</p>',
                u'<p style="text-align: right;">'+("{0:,.2f}".format(line.credit) or '')+u'</p>',
#                 (line.debit), 
#                 (line.credit), 
#                 (line.name[:50]+' ..'),
                ]
                datas.append(temp)
                i += 1
        
        # datas.append(temp)
        res = {'header': headers, 'data':datas}
        return res
    

    def get_order_line_xl(self, ids):
        context=self._context
        print_payment=False
        if context.get('print_payment',False):
            print_payment=True
        datas = []
        report_ids = self.search([('id','in',ids)], order='date')
#         print ('report_ids ',report_ids)
        i = 1
        for report_id in report_ids:
            lines = report_id.line_ids
            sum1 = 0
            sum2 = 0
            sum3 = 0
    #         print 'lines ',lines
            for line in lines:
                temp = [
                (str(i)),
                str(report_id.date),
                (report_id.name), 
                (line.name), 
                (line.debit),
                (line.credit),
#                 (line.debit), 
#                 (line.credit), 
#                 (line.name[:50]+' ..'),
                ]
                datas.append(temp)
                i += 1
        
        # datas.append(temp)
        res = {'data':datas}
        return res    
        
    def do_print_move(self):
        context=self._context
        print_payment=False
        if context.get('print_payment',False):
            print_payment=True
        counter = 1
        line_ids = self.env['account.move'].search([('id','in',self.ids)])
        journal=''
        ref=''
        journal_id=False
        for move in line_ids:
            if not journal_id:
                journal_id=move.journal_id.id
                if move.journal_id.type=='cash':
                    for line in move.line_ids:
                        if line.statement_id:
                            ref=line.statement_id.name
                else:
                    ref=move.ref
            elif journal_id!=move.journal_id.id:
                raise UserError(_(u'Өөр журналын гүйлгээг нэг зэрэг хэвэх боломжгүй!'))
                
            journal=move.company_id.name
            
        first_picking = line_ids[0]
        html = u'''
        <table style="width: 100%;">
            <tbody>
            <tr style="height: 25px; border-bottom:1pt solid black;" >
            <td style='border-bottom:1pt solid black' colspan="2">
            <p style="text-align: center;"><strong><span style="font-size: 14pt;">Ерөнхий журнал</span></strong></p>
            </td>
            </tr>
            <tr style="height: 16px;">
            <td style="width: 31%; height: 16px;"><span style="font-size: 11pt;">Байгууллагын нэр: {0}</span><br /></td>
            <td style="width: 98.5987%; height: 16px;"><span style="font-size: 8pt;">Огноо: 2020-01-01 - 2020-07-30</span><br /></td>
            </tr>
            </tbody>
            </table>
        '''.format(journal,ref)
        
        for item in line_ids:
#             item.write({'printed': True, 'printed_count': item.printed_count+1})

            template = False
            model_id = self.env['ir.model'].sudo().search([('model','=','account.move')], limit=1)
            template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','default_multi')], limit=1)
            print ('template ',template)
            if template:
#                 res = template.sudo().print_template(self.id)
#                 return res
                pttrn_name='<th '
                template_html = template.sudo().get_template_data_html(item.id)
                if template_html:
                    template_html = template_html.replace(pttrn_name, '<th style="font-weight: normal;" ')
 
                pttrn_name = 'border: 1px solid #dddddd;'
                if template_html:
                    template_html = template_html.replace(pttrn_name, 'border: 1px solid #777777;')
                    # template_html = template_html.replace(pttrn_name, 'border: 1px dashed #777777;')
                    # template_html = template_html.replace(pttrn_name, 'border: 1px dashed black;')
 
                    if first_picking.id!=item.id:
#                         if counter % 2 != 0 and first_picking.print_type=='type2' and item.print_type=='type2':
#                             html += u'<br/><br/><br/>---------------------------------'+template_html+'</div>'
#                         elif counter % 2 == 0 and first_picking.print_type=='type2' and item.print_type=='type2':
#                             html += u'<div class="break_page">'+template_html+''
#                         elif counter % 2 == 0 and first_picking.print_type!='type2' and item.print_type=='type2':
#                             html += u'<div class="break_page">'+template_html+''
#                         else:
                            html += u'<div class="break_page">'+template_html+'</div>'
                         
                    else:
#                         if item.print_type=='type2':
#                             html += u'<div class="break_page">'+template_html+''
#                         else:
                            html += u'<div class="break_page">'+template_html+'</div>'
                    first_picking = item
                    # html += u'<div class="break_page">'+template_html+'</div>'
                    counter+=1
 
            else:
                raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))
        return template.sudo().print_template_html(html)
    
    
    def get_company_logo(self, ids):
        
        report_id = self.browse(ids)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        url = "/web/image/res.company/%d/logo"
        img_url = base_url+url%report_id.company_id.id
        if img_url:
            image_str = '<img alt="Embedded Image" width="400" src="'+img_url+'" />'
            return image_str
        image_buf = report_id.company_id.logo_web
        image_str = '<img alt="Embedded Image" width="400" src="data:image/png;base64,'+image_buf+'" />'
        return image_str
         
class AccountManyConfirm(models.TransientModel):
    _name = "account.move.many.confirm"
    _description = "Account many confirm with print"
    # package_qty = fields.Float('Package qty')
# 
    print_payment = fields.Boolean('Print payment', default=False)

    def action_done(self):
        obj_ids = self.env['account.move'].browse(self._context['active_ids'])
        return obj_ids.with_context(print_payment=self.print_payment).do_print_move()
    

class AccountPartialReconcile(models.Model):
    _inherit = "account.partial.reconcile"
    _description = "Partial Reconcile"

    @api.model
    def create_exchange_rate_entry_old(self, aml_to_fix, amount_diff, diff_in_currency, currency, move):
        """
        Automatically create a journal items to book the exchange rate
        differences that can occure in multi-currencies environment. That
        new journal item will be made into the given `move` in the company
        `currency_exchange_journal_id`, and one of its journal items is
        matched with the other lines to balance the full reconciliation.

        :param aml_to_fix: recordset of account.move.line (possible several
            but sharing the same currency)
        :param amount_diff: float. Amount in company currency to fix
        :param diff_in_currency: float. Amount in foreign currency `currency`
            to fix
        :param currency: res.currency
        :param move: account.move
        :return: tuple.
            [0]: account.move.line created to balance the `aml_to_fix`
            [1]: recordset of account.partial.reconcile created between the
                tuple first element and the `aml_to_fix`
        analytic_account
        """
        partial_rec = self.env['account.partial.reconcile']
        aml_model = self.env['account.move.line']

        amount_diff = move.company_id.currency_id.round(amount_diff)
        diff_in_currency = currency and currency.round(diff_in_currency) or 0
        created_lines = self.env['account.move.line']
        for aml in aml_to_fix:
            #create the line that will compensate all the aml_to_fix

            line_to_rec = aml_model.with_context(check_move_validity=False).create({
                'name': _('Currency exchange rate difference'),
                'debit': amount_diff < 0 and -aml.amount_residual or 0.0,
                'credit': amount_diff > 0 and aml.amount_residual or 0.0,
                'account_id': aml.account_id.id,
                'move_id': move.id,
                'currency_id': currency.id,
                'amount_currency': diff_in_currency and -aml.amount_residual_currency or 0.0,
                'partner_id': aml.partner_id.id,
            })
            #create the counterpart on exchange gain/loss account
            exchange_journal = move.company_id.currency_exchange_journal_id
            analytic_account=False
            if exchange_journal.default_debit_account_id.internal_type=='expense' \
                or exchange_journal.default_credit_account_id.internal_type=='expense':
                if exchange_journal.default_debit_account_id.analytic_account_id:
                    analytic_account=exchange_journal.default_debit_account_id.analytic_account_id.id
            aml_model.with_context(check_move_validity=False).create({
                'name': _('Currency exchange rate difference'),
                'debit': amount_diff > 0 and aml.amount_residual or 0.0,
                'credit': amount_diff < 0 and -aml.amount_residual or 0.0,
                'account_id': amount_diff > 0 and exchange_journal.default_debit_account_id.id or exchange_journal.default_credit_account_id.id,
                'move_id': move.id,
                'currency_id': currency.id,
                'amount_currency': diff_in_currency and aml.amount_residual_currency or 0.0,
                'partner_id': aml.partner_id.id,
                'analytic_account_id':analytic_account
            })

            #reconcile all aml_to_fix
            partial_rec |= self.with_context(skip_full_reconcile_check=True).create(
                self._prepare_exchange_diff_partial_reconcile(
                        aml=aml,
                        line_to_reconcile=line_to_rec,
                        currency=currency)
            )
            created_lines |= line_to_rec
        return created_lines, partial_rec
    
    @api.model
    def create_exchange_rate_entry(self, aml_to_fix, move):
        """
        Automatically create a journal items to book the exchange rate
        differences that can occur in multi-currencies environment. That
        new journal item will be made into the given `move` in the company
        `currency_exchange_journal_id`, and one of its journal items is
        matched with the other lines to balance the full reconciliation.
        :param aml_to_fix: recordset of account.move.line (possible several
            but sharing the same currency)
        :param move: account.move
        :return: tuple.
            [0]: account.move.line created to balance the `aml_to_fix`
            [1]: recordset of account.partial.reconcile created between the
                tuple first element and the `aml_to_fix`
        """
        partial_rec = self.env['account.partial.reconcile']
        aml_model = self.env['account.move.line']

        created_lines = self.env['account.move.line']
        for aml in aml_to_fix:
            #create the line that will compensate all the aml_to_fix
            line_to_rec = aml_model.with_context(check_move_validity=False).create({
                'name': _('Currency exchange rate difference'),
                'debit': aml.amount_residual < 0 and -aml.amount_residual or 0.0,
                'credit': aml.amount_residual > 0 and aml.amount_residual or 0.0,
                'account_id': aml.account_id.id,
                'move_id': move.id,
                'currency_id': aml.currency_id.id,
                'amount_currency': aml.amount_residual_currency and -aml.amount_residual_currency or 0.0,
                'partner_id': aml.partner_id.id,
            })
            #create the counterpart on exchange gain/loss account
            exchange_journal = move.company_id.currency_exchange_journal_id
            analytic_account=False
            if exchange_journal.default_debit_account_id.internal_type=='expense' \
                or exchange_journal.default_credit_account_id.internal_type=='expense':
                if exchange_journal.default_debit_account_id.analytic_account_id:
                    analytic_account=exchange_journal.default_debit_account_id.analytic_account_id.id            
            aml_model.with_context(check_move_validity=False).create({
                'name': _('Currency exchange rate difference'),
                'debit': aml.amount_residual > 0 and aml.amount_residual or 0.0,
                'credit': aml.amount_residual < 0 and -aml.amount_residual or 0.0,
                'account_id': aml.amount_residual > 0 and exchange_journal.default_debit_account_id.id or exchange_journal.default_credit_account_id.id,
                'move_id': move.id,
                'currency_id': aml.currency_id.id,
                'amount_currency': aml.amount_residual_currency and aml.amount_residual_currency or 0.0,
                'partner_id': aml.partner_id.id,
                'analytic_account_id':analytic_account                
            })

            #reconcile all aml_to_fix
            partial_rec |= self.create(
                self._prepare_exchange_diff_partial_reconcile(
                        aml=aml,
                        line_to_reconcile=line_to_rec,
                        currency=aml.currency_id or False)
            )
            created_lines |= line_to_rec
        return created_lines, partial_rec
    
    

# class AccountPartialReconcile(models.Model):
#     _inherit = "account.partial.reconcile"
#     _description = "Partial Reconcile"
# 
#     @api.model
#     def _prepare_exchange_diff_partial_reconcile(self, aml, line_to_reconcile,line_to_rec_pay, currency):
#         """Ханшийн тэгшитгэл бол валютаарх дүн 0 байх ёстой
#         """
#         print '1 ',self.env.context.get('is_exchange',False)
#         print 'aml----------------- ',aml
#         print 'line_to_reconcile ',line_to_reconcile
#         curr=0
# #         if aml.amount_residual or aml.amount_residual_currency:
#         exchange_amount=abs(aml.amount_residual)
#         if not self.env.context.get('is_exchange',False):
#             curr=abs(aml.amount_residual_currency)
#         if self.env.context.get('exchange_amount',False):
#             exchange_amount=self.env.context.get('exchange_amount',False)
#         return {
# #             'debit_move_id': aml.credit and line_to_reconcile.id or aml.id,
# #             'credit_move_id': aml.debit and line_to_reconcile.id or aml.id,
#             'debit_move_id': line_to_rec_pay.credit and line_to_reconcile.id or line_to_rec_pay.id,
#             'credit_move_id': line_to_rec_pay.debit and line_to_reconcile.id or line_to_rec_pay.id,
# #             'amount': abs(aml.amount_residual),#Бүх үлдэгдлээр үүсгэхэд aml residual_amount 0 болоод дараа тэгшитгэхэд буруу гарах
#             'amount':abs(exchange_amount),
#             'amount_currency': curr,#self.env.context.get('is_exchange',False) and 0 or abs(aml.amount_residual_currency),
#             'currency_id': currency.id,
#         }
# 
#     @api.model
#     def create_exchange_rate_entry(self, aml_to_fix, amount_diff, diff_in_currency, currency, move):
#         """
#         Automatically create a journal items to book the exchange rate
#         differences that can occure in multi-currencies environment. That
#         new journal item will be made into the given `move` in the company
#         `currency_exchange_journal_id`, and one of its journal items is
#         matched with the other lines to balance the full reconciliation.
# 
#         :param aml_to_fix: recordset of account.move.line (possible several
#             but sharing the same currency)
#         :param amount_diff: float. Amount in company currency to fix
#         :param diff_in_currency: float. Amount in foreign currency `currency`
#             to fix
#         :param currency: res.currency
#         :param move: account.move
#         :return: tuple.
#             [0]: account.move.line created to balance the `aml_to_fix`
#             [1]: recordset of account.partial.reconcile created between the
#                 tuple first element and the `aml_to_fix`
#        
#        1. analytic_account
#        2. Хугацааны дундуур төлөхөд тэгшитгэх. 
#        amount_diff нь төлөлт болон анхны өглөг 2 ын зөрүү
#            Тайлбар:
#                Өглөг бол
#                Хагас:
#                 1. total_debit  1620000.0
#                 total_credit  2500000.0
#                 Бүтэн:
#                 total_debit  2700000.0
#                 total_credit  2500000.0 # Анх үүссэн нийт
#                 Авлага эсрэгээр
#                2. aml_to_fix Анхны өглөгийн өчилт, 2 дахь үлдэгдэл төлөхөд нийт төлөлтүүд
#                    Бүтэн үед тэгшитгэж байвал. default
#                                    1. 1620 000
#                                    2. (1620 000 + 1 120 000) -2 500 000 -  240 000 = 0
#                     Төлөлт бүрээс mn_account
#                                 1. 1 620 000 - 1 620 000 /2,5 саяас/ - 120 000= -120 000
#                                 2. ()
#                3. self.debit_move_id.amount_currency :600 өглөг бол төлөлт хийх мөр
#                self.credit_move_id.amount_currency : -600.0 Авлага бол - төлөлт
#                
#         """
#         partial_rec = self.env['account.partial.reconcile']
#         aml_model = self.env['account.move.line']
# 
#         amount_diff = move.company_id.currency_id.round(amount_diff)
#         print 'amount_diff--------: ',amount_diff
#         print 'aml_to_fix ',aml_to_fix
#         print 'diff_in_currency ',diff_in_currency
#         
# #         print 'create_exchange_rate_entry---->: self ',self
#         type='vendor'
#         if self.credit_move_id.id>self.debit_move_id.id:
#             type='customer'
#         print 'create_exchange_rate_entry---->: self debit_move_id ',self.debit_move_id.id#+' debit :'+self.debit_move_id
#         print 'create_exchange_rate_entry---->: self credit_move_id ',self.credit_move_id.id
#         print ' self.credit_move_id.amount_currency :',self.credit_move_id.amount_currency
#         print ' self.debit_move_id.amount_currency :',self.debit_move_id.amount_currency
#         diff_in_currency = currency and currency.round(diff_in_currency) or 0
#         current_payment=0
#         line_to_rec_pay=False#Тэгшитгэл нь үндсэн дүн бус төлөлт хийж буй гүйлгээг тулгаж recidual_amount д нөлөөлнө
#         
#         if type=='vendor':
#             pay_date=self.debit_move_id.date
#             line_to_rec_pay=self.debit_move_id
#             if self.debit_move_id:
#                 print 'self.debit_move_id.company_id.currency_id. ',self.debit_move_id.company_id.currency_id
#                 print 'self.debit_move_id.currency_id ',self.debit_move_id.currency_id
#                 print 'self.debit_move_id.amount_currency ',self.debit_move_id.amount_currency
#                 current_payment = self.debit_move_id.company_id.currency_id.with_context(date=self.debit_move_id.date).compute(self.debit_move_id.amount_currency, self.debit_move_id.currency_id)
#                 current_payment = self.env['res.currency'].with_context(date=self.debit_move_id.date)._compute(self.debit_move_id.currency_id,self.debit_move_id.company_id.currency_id,  self.debit_move_id.amount_currency, round=False)
#             start_payment=0
#             if self.credit_move_id:
#                 #Тухайн төлөлтийг дүнг анх үүссэн ханшаар авах
#     #             start_payment = self.credit_move_id.company_id.currency_id.with_context(date=self.credit_move_id.date).compute(self.debit_move_id.amount_currency, self.credit_move_id.currency_id)
#                 start_payment = self.env['res.currency'].with_context(date=self.credit_move_id.date)._compute(self.debit_move_id.currency_id,self.debit_move_id.company_id.currency_id,  self.debit_move_id.amount_currency, round=False)
# 
#         else:
#             pay_date=self.credit_move_id.date
#             line_to_rec_pay=self.credit_move_id
#             
#             if self.credit_move_id:
#                 print 'self.debit_move_id.currency_id ',self.credit_move_id.currency_id
#                 print 'self.debit_move_id.amount_currency ',self.credit_move_id.amount_currency
#                 current_payment = self.credit_move_id.company_id.currency_id.with_context(date=self.credit_move_id.date).compute(self.credit_move_id.amount_currency, self.credit_move_id.currency_id)
#                 current_payment = self.env['res.currency'].with_context(date=self.credit_move_id.date)._compute(self.credit_move_id.currency_id,self.credit_move_id.company_id.currency_id,  self.credit_move_id.amount_currency, round=False)
#             start_payment=0
#             if self.debit_move_id:
#                 #Тухайн төлөлтийг дүнг анх үүссэн ханшаар авах
#     #             start_payment = self.credit_move_id.company_id.currency_id.with_context(date=self.credit_move_id.date).compute(self.debit_move_id.amount_currency, self.credit_move_id.currency_id)
#                 start_payment = self.env['res.currency'].with_context(date=self.debit_move_id.date)._compute(self.credit_move_id.currency_id,self.credit_move_id.company_id.currency_id,  self.credit_move_id.amount_currency, round=False)
# 
#         print 'current_payment ',current_payment
#         print 'start_payment ',start_payment
#         
#         #Өглөг ханш өссөн start_payment-current_payment<0 else buursan
#         exchange_amount = start_payment-current_payment
#         print 'exchange_amount ',exchange_amount
#         dt=False
#         if exchange_amount<0 and type=='vendor':#Өссөн
#             dt=True
#         if exchange_amount<0 and type=='customer':#Авлага буурсан бол Дт
#             dt=True
#         created_lines = self.env['account.move.line']
#         for aml in aml_to_fix:
#             #create the line that will compensate all the aml_to_fix
#             print 'aml.amount_residual ',aml
#             print 'aml.amount_residual_currency ',aml.amount_residual_currency
#             # Бүтэн төлөлт дуусахад ханш тэгшитгэдэг тул үлдэгдэл дүнгээр бүтнээр төлөлт хийж дуусгаж байна.
#             line_to_rec = aml_model.with_context(check_move_validity=False).create({
#                 'name': _('Currency exchange rate difference'),
# #                 'debit': amount_diff < 0 and -aml.amount_residual or 0.0,   
# #                 'credit': amount_diff > 0 and aml.amount_residual or 0.0,
#                 'debit': not dt and abs(exchange_amount) or 0.0,   
#                 'credit': dt and abs(exchange_amount) or 0.0,#Өглөг, ханш өссөн бол Кр
#                 'account_id': aml.account_id.id,
#                 'move_id': move.id,
#                 'currency_id': currency.id,
#                 'amount_currency':0,# diff_in_currency and -aml.amount_residual_currency or 0.0,#Ханш тэгшитгэл тул валют 0 байх ёстой уг нь
#                 'partner_id': aml.partner_id.id,
#             })
#             #create the counterpart on exchange gain/loss account
#             exchange_journal = move.company_id.currency_exchange_journal_id
#             analytic_account=False
#             if exchange_journal.default_debit_account_id.internal_type=='expense' \
#                 or exchange_journal.default_credit_account_id.internal_type=='expense':
#                 if exchange_journal.default_debit_account_id.analytic_account_id:
#                     analytic_account=exchange_journal.default_debit_account_id.analytic_account_id.id
#             aml_model.with_context(check_move_validity=False).create({
#                 'name': _('Currency exchange rate difference'),
# #                 'debit': amount_diff > 0 and aml.amount_residual or 0.0,
# #                 'credit': amount_diff < 0 and -aml.amount_residual or 0.0,
#                 'debit': dt and abs(exchange_amount) or 0.0,   
#                 'credit': not dt and abs(exchange_amount) or 0.0,#Өглөг, ханш өссөн бол Кр
#                 'account_id': amount_diff > 0 and exchange_journal.default_debit_account_id.id or exchange_journal.default_credit_account_id.id,
#                 'move_id': move.id,
#                 'currency_id': currency.id,
#                 'amount_currency': 0,#diff_in_currency and aml.amount_residual_currency or 0.0,
#                 'partner_id': aml.partner_id.id,
#                 'analytic_account_id':analytic_account
#             })
#             #reconcile all aml_to_fix
#             print 'exchange_amount ',exchange_amount
#             print 'line_to_rec ',line_to_rec
#             v=self.with_context(is_exchange=True,
#                                 exchange_amount=exchange_amount,
#                                 
#                                 )._prepare_exchange_diff_partial_reconcile(
#                         aml=aml,
#                         line_to_reconcile=line_to_rec,
#                         line_to_rec_pay=line_to_rec_pay,
#                         currency=currency)
#             print 'vv',v
#             partial_rec |= self.with_context(skip_full_reconcile_check=True).create(
#                 v
#             )
#             created_lines |= line_to_rec
#             
# 
#         #Хэрэгжээгүй ханш
# #         equalizationnext=self.env['account.currency.equalizationnext'].create({'company_id':1,
# #                                                               'journal_id':17,
# #                                                               'currency_id':currency.id,
# # #                                                               'partner_id':
# #                                                               'type':'partner',
# #                                                               'date':pay_date,
# #                                                               'rate_date':pay_date,
# #                                                                     })
# #         print 'equalizationnext ',equalizationnext
# #         print 'aml.account_id.id ',aml.account_id.code
# #         equalizationnext.onchange_date()
# #         account_ids=[aml.account_id.id]
# #         order_by = 'p.name, aa.code, aa.name'
# #         date_start = equalizationnext.find_start_date(account_ids)
# #         print 'date_start ',date_start
# #         lines = self.env['account.move.line'].with_context(partner_ids=[aml.partner_id.id],order_by=order_by).get_all_balance(self.company_id.id, account_ids, 
# #                                                                                          date_start[0], pay_date, 'posted')
# #         print 'lines ',lines
# #         equalizationnext.create_line(lines)
# #         equalizationnext.action_equalize()
# #         
#         return created_lines, partial_rec
#     
# 
#     def _compute_partial_lines(self):
#         if self._context.get('skip_full_reconcile_check'):
#             #when running the manual reconciliation wizard, don't check the partials separately for full
#             #reconciliation or exchange rate because it is handled manually after the whole processing
#             print '222'
#             return self
#         #check if the reconcilation is full
#         #first, gather all journal items involved in the reconciliation just created
#         aml_set = aml_to_balance = self.env['account.move.line']
#         total_debit = 0
#         total_credit = 0
#         total_amount_currency = 0
#         #make sure that all partial reconciliations share the same secondary currency otherwise it's not
#         #possible to compute the exchange difference entry and it has to be done manually.
#         currency = self[0].currency_id
#         maxdate = '0000-00-00'
# 
#         seen = set()
#         todo = set(self)
#         print 'todo111111 ',todo
#         while todo:
#             partial_rec = todo.pop()
#             seen.add(partial_rec)
#             if partial_rec.currency_id != currency:
#                 #no exchange rate entry will be created
#                 currency = None
#             print 'partial_rec ',partial_rec
#             for aml in [partial_rec.debit_move_id, partial_rec.credit_move_id]:
#                 print 'aml ',aml.id
#                 if aml not in aml_set:
#                     print 'aml.amount_residual ',aml.amount_residual #холбоотой үлдэгдэлтэй гүйлгээнүүдийг тулгах
#                     if aml.amount_residual or aml.amount_residual_currency:
#                         aml_to_balance |= aml
#                     maxdate = max(aml.date, maxdate)
#                     total_debit += aml.debit
#                     total_credit += aml.credit
#                     aml_set |= aml
#                     if aml.currency_id and aml.currency_id == currency:
#                         total_amount_currency += aml.amount_currency
#                     elif partial_rec.currency_id and partial_rec.currency_id == currency:
#                         #if the aml has no secondary currency but is reconciled with other journal item(s) in secondary currency, the amount
#                         #currency is recorded on the partial rec and in order to check if the reconciliation is total, we need to convert the
#                         #aml.balance in that foreign currency
#                         total_amount_currency += aml.company_id.currency_id.with_context(date=aml.date).compute(aml.balance, partial_rec.currency_id)
# 
#                 for x in aml.matched_debit_ids | aml.matched_credit_ids:
#                     if x not in seen:
#                         todo.add(x)
# 
#         partial_rec_ids = [x.id for x in seen]
#         aml_ids = aml_set.ids
#         #then, if the total debit and credit are equal, or the total amount in currency is 0, the reconciliation is full
#         digits_rounding_precision = aml_set[0].company_id.currency_id.rounding
#         print 'aml_to_balance ',aml_to_balance
# #         print 'aml_to_balance ',aml_to_balance.amount_currency
#         print 'total_amount_currency ',total_amount_currency
#         print 'currency1 ',currency
#         print 'total_debit ',total_debit
#         print 'total_credit ',total_credit
#         # хувааж төлсөн ч тэгшитгэх
#         exchange_move = self.env['account.move'].create(
#                     self.env['account.full.reconcile']._prepare_exchange_diff_move(move_date=maxdate, company=aml_to_balance[0].company_id))
#         rate_diff_amls, rate_diff_partial_rec = self.create_exchange_rate_entry(aml_to_balance, total_debit - total_credit, total_amount_currency, currency, exchange_move)
#         
#         if (currency and float_is_zero(total_amount_currency, precision_rounding=currency.rounding)) or float_compare(total_debit, total_credit, precision_rounding=digits_rounding_precision) == 0:
#             exchange_move_id = False
#             print 'currency ',currency
#             if currency and aml_to_balance:
# #                 exchange_move = self.env['account.move'].create(
# #                     self.env['account.full.reconcile']._prepare_exchange_diff_move(move_date=maxdate, company=aml_to_balance[0].company_id))
# #                 #eventually create a journal entry to book the difference due to foreign currency's exchange rate that fluctuates
# #                 rate_diff_amls, rate_diff_partial_rec = self.create_exchange_rate_entry(aml_to_balance, total_debit - total_credit, total_amount_currency, currency, exchange_move)
# #                 aml_ids += rate_diff_amls.ids
#                 partial_rec_ids += rate_diff_partial_rec.ids
#                 exchange_move.post()
#                 exchange_move_id = exchange_move.id
#             #mark the reference of the full reconciliation on the partial ones and on the entries
#             self.env['account.full.reconcile'].create({
#                 'partial_reconcile_ids': [(6, 0, partial_rec_ids)],
#                 'reconciled_line_ids': [(6, 0, aml_ids)],
#                 'exchange_move_id': exchange_move_id,
#             })
    

class AccountCashCheck(models.Model):
    _name = 'account.cash.move.check'
    _description = 'Cash Move Type Check'

    name = fields.Char('Name', size=100, required=True)
    bank_line_ids = fields.One2many('account.bank.statement.line', 'cash_type_id', string='Lines',)
    line_ids = fields.One2many('account.cash.move.check.line', 'parent_id', 'Мөр')
    null_line_ids = fields.One2many('account.cash.move.check.null.line', 'parent_id', 'Мөр')
    state = fields.Selection([('draft','Ноорог'),('done','Confirm')], 'state', default='draft')
    company_id = fields.Many2one('res.company', 'Company',required=True)


    def update(self):
        count=0
        for e in self:#.browse(ids):
            for l in e.account_line_ids:
                count+=1
#                print '-----------',count,'==',l.aml_credit_id.id
                if l.aml_credit_id.id:
#                     l.aml_credit_id.write({'credit':l.amount})
                    query = """
                            update account_move_line set credit={0} where id={1}""" .format(l.amount,l.aml_credit_id.id)
                    self.env.cr.execute(query)
                    self.env.cr.commit()
#                     query_result = cr.dictfetchall()
                if l.aml_debit_id.id:
#                     l.aml_debit_id.write({'debit':l.amount})
                    query = """
                            update account_move_line set debit={0} where id={1}""" .format(l.amount,l.aml_debit_id.id)
                    self.env.cr.execute(query)
                    self.env.cr.commit()
#                     query_result = cr.dictfetchall()
#         cr.commit()
        return True
    
    
    def compute(self):
        incomes = ('activities_income','investing_income', 'financing_income')
        expenses= ('activities_expense', 'investing_expense', 'financing_expense')

        for e in self:#.browse(cr,uid,ids):
            categ_where=""
            warehouse_where=""
            query = """
                    select bl.id as bsl_id,cash_type_id,amount,is_income,group_name 
                    from account_bank_statement_line bl left join 
                        account_cash_move_type t on bl.cash_type_id=t.id 
                    where is_income='expense' and amount>0 and bl.account_id<>{0}
                    union 
                    select bl.id as bsl_id,cash_type_id,amount,is_income,group_name 
                    from account_bank_statement_line bl left join 
                        account_cash_move_type t on bl.cash_type_id=t.id 
                    where is_income<>'expense' and amount<0 and bl.account_id<>{0}""".format(self.company_id.transfer_account_id.id)

            print ('query ',query)
            self._cr.execute(query)
            query_result = self._cr.dictfetchall()
#             print 'query_result ',query_result
            if  e.line_ids:
                raise ValidationError((u'Мөрүүд үүссэн байна'))
            
            for r in query_result:
                print ('rrr ',r)
                    
                line_pool=self.env['account.cash.move.check.line']
                line_pool.create({
                                                'name':r['bsl_id'],
#                                                'debit':r['debit'],
#                                                'credit':r['credit'],
                                                'amount': r['amount'],
#                                                 'unit_price': r['price_unit'],
                                                'parent_id':e.id,
#                                                 'account_id':debit_id,
                                                'cash_type_id':r['cash_type_id'],
                                                'bank_line_id':r['bsl_id'],
                                                'is_income':r['is_income'],
                                                       })
   
   
        return True
    

    def compute_null(self):
        incomes = ('activities_income','investing_income', 'financing_income')
        expenses= ('activities_expense', 'investing_expense', 'financing_expense')

        for e in self:#.browse(cr,uid,ids):
            categ_where=""
            warehouse_where=""
#             query = """
#                         select (debit-credit) as amount,debit,credit, date,id from account_move_line 
#                         where account_id in 
#                                 (select id from account_account where internal_type ='liquidity' and 
#                                 (is_temporary isnull or is_temporary='f'))
#                                 and cash_type_id isnull and account_id<>{0}""".format(self.company_id.transfer_account_id.id)

            query = """
                        select amount as amount, date,id from account_bank_statement_line 
                        where cash_type_id isnull and account_id<>{0}""".format(self.company_id.transfer_account_id.id)


            print ('query ',query)
            self._cr.execute(query)
            query_result = self._cr.dictfetchall()
#             print 'query_result ',query_result
            if  e.null_line_ids:
                raise ValidationError((u'Мөрүүд үүссэн байна'))
            
            for r in query_result:
                print ('rrr2 ',r)
                    
                line_pool=self.env['account.cash.move.check.null.line']
                line_pool.create({
                                                'name':r['id'],
#                                                 'debit':r['debit'],
#                                                 'credit':r['credit'],
                                                'amount': r['amount'],
#                                                 'unit_price': r['price_unit'],
                                                'parent_id':e.id,
#                                                 'account_id':debit_id,
#                                                 'cash_type_id':r['cash_type_id'],
                                                'bsl_id':r['id'],
#                                                 'is_income':r['is_income'],
                                                       })
   
   
        return True    
class AccountCashCheckLine(models.Model):
    _name = 'account.cash.move.check.line'
    _description = u'Line'



    INCOME_SELECTION = [
        ('income','Income'),
        ('expense','Expense'),
        (' ',' '),
    ]

    name = fields.Char('Name')
    parent_id = fields.Many2one('account.cash.move.check', 'Толгой', ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')

    amount = fields.Float('Amount')
    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")
    bank_line_id = fields.Many2one('account.bank.statement.line', string='Bank line',)
    is_income = fields.Selection(INCOME_SELECTION, 'TYPE')
    date = fields.Date("Start Date",related='bank_line_id.date', store=True)
    
    

class AccountCashCheckNullLine(models.Model):
    _name = 'account.cash.move.check.null.line'
    _description = u'Line'

    INCOME_SELECTION = [
        ('income','Income'),
        ('expense','Expense'),
        (' ',' '),
    ]

    name = fields.Char('Name')
    parent_id = fields.Many2one('account.cash.move.check', 'Толгой', ondelete='cascade')
    account_id = fields.Many2one('account.account', 'Account')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')

    amount = fields.Float('Amount')
    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")
    aml_id = fields.Many2one('account.move.line', string='Move line',)
    bsl_id = fields.Many2one('account.bank.statement.line', string='Statement line',)
#     is_income = fields.Selection(INCOME_SELECTION, 'TYPE')
    date = fields.Date("Start Date",related='aml_id.date', store=True)    
        
