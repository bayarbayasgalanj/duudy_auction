# -*- encoding: utf-8 -*-
############################################################################################
#
#    Managewall-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2017 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#    $Id:  $
#
#    Менежволл-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
############################################################################################
import time, odoo.tools
from lxml import etree

# from odoo.osv import fields, osv
# from odoo.tools.translate import _
# import odoo.addons.decimal_precision as dp

from odoo.tools.safe_eval import safe_eval
# import odoo
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp

class account_currency_equalization(models.TransientModel):

    """
        Гадаад валютаар хийгдсэн журналын бичилтүүдэд ханшийн тэгшитгэл хийнэ.
    """
    _name = "account.currency.equalization"
    _description = "Currency Rate Equalization"
    
    company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env.user.company_id)
    type = fields.Selection([('liquidity', 'Liquidity Accounts'),('partner', 'Partner Balances')], 'Type', required=True,default='liquidity')
    date = fields.Date('Date', required=True,default=lambda *a: time.strftime('%Y-%m-%d'))
    name = fields.Char('Reason', size=128, required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    draft = fields.Boolean('Draft Entry', default=False, help="Check if this box, equalization entries to be generated draft state. Then you should valid them.")
    
    partner_id = fields.Many2one('res.partner', 'Partner', help="If you select any partner then system will do equalization on only the selected partner balance.")
    currency_id = fields.Many2one('res.currency', 'Currency',required=True, help="If you select any currency then system will do equalization on only selected currency.")
    line_ids=fields.One2many('account.currency.equalization.line', 'parent_id', 'Lines')

    state = fields.Selection([('new', 'New'),('done', 'Done')], 'State', required=True,default='new')

#    company_id = lambda self,cr,uid,c: self.env['res.company')._company_default_get(cr, uid, 'account.currency.equalization', context=c),
    

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(account_currency_equalization, self).fields_view_get(view_id, view_type, toolbar, submenu)
        context = self.env.context
#         print "context fields_view_get ",context
#         print "wizard_obj.state1 ",wizard_obj.state
        if context.has_key('obj_id'):
            ids = context['obj_id']
            wizard_obj = self.browse(ids)[0]
            if wizard_obj.state == 'done':
                arch_lst = [
                       '<?xml version="1.0"?>'
                            , '<form string="%s">' % (_('Currency Rate Equalization'))
                            , '<group colspan="4" states="new">'
                            , '<field name="date" required="1"/>'
                            , '</group>'
                            , '<group colspan="4" states="done">'
                            , '<field name="line_ids" colspan="4"/>'
                            , '</group>'
                            , '<group colspan="4" col="6">'
                            , '    <button icon="gtk-cancel" special="cancel" string="Close"/>'
                            , '    <label string="" colspan="2"/>'
                            , '    <button icon="gtk-execute" string="Do Generate" name="action_equalize_partner" type="object"/>'
#                             , '    <field name="state" invisible="1" readonly="1"/>'
                        ]
#                 if wizard_obj.state == 'new':
#                     arch_lst.append('<button name="next" string="%s" type="object" icon="gtk-ok"/>' % (_('Next')))
#                 elif wizard_obj.state == 'done':
#                     arch_lst.append('<button name="action_equalize" string="%s" type="object" icon="gtk-ok"/>' % (_('Equalize')))
                arch_lst.append('</group>')
                arch_lst.append('</form>')
                res['arch'] = '\n'.join(arch_lst).encode('utf8')
#         print "res ",res
        return res    

    def _get_datas(self):
        context = self.env.context
        account_obj = self.env['account.account']
        account_move_line_obj = self.env['account.move.line']
        account_move_obj = self.env['account.move']
        fiscalyear_obj = self.env['account.fiscalyear']
        form = self#.browse(cr, uid, ids[0], context=context)
        currency_obj=self.env['res.currency']
#         period_id = self.env['account.period').find(cr, uid, dt=form.date, context=context)[0]
#         period = self.env['account.period').browse(cr, uid, period_id, context=context)
        
        # Тэгшитгэл хийх шаардлагатай дансууд. Мөн өглөг, авлагын дансуудыг ялгана.
        account_ids2 = self.get_accounts(type=2)
        
        res = []
        
        # Мөнгөн хөрөнгийн гадаад валютын дансуудын балансыг тэгшитгэнэ.
        # Өглөг авлагын үлдэгдэл бүр дээр тэгшитгэнэ.
        if account_ids2 :
            # Өглөг, авлага бүртгэсэн гүйлгээг тодорхойлохдоо тухайн санхүүгийн жилд бүртгэгдсэнийг
            # тодорхойлно. Учир нь өмнөх жилийн гүйлгээнүүд бүгд хаагдсан байх ёстой.
            # Мөн зөвхөн тухайн компаний өглөг, авлагыг тэгшитгэнэ.
            partner_where = ""
            if form.partner_id:
                partner_where += " AND l.partner_id = %s " % form.partner_id.id
            if form.currency_id:
                partner_where += " AND l.currency_id = %s " % form.currency_id.id
            
#             fy_boj = fiscalyear_obj.browse(cr, uid, period.fiscalyear_id.id,context=context)
#             start_period_id = self.env['account.period'].search(cr,uid,[('fiscalyear_id','=',period.fiscalyear_id.id),('special','=',True)])
#             print "start_period_id ",start_period_id
#             start_move_ids=account_move_obj.search(cr,uid,[('period_id','=',start_period_id),('state','=','posted')])
#             print "start_move_ids ",start_move_ids
#             if len(start_move_ids)<>1:
#                 raise osv.except_osv(('Warning!'), (u'Эхний үлдэгдэл татаагүй, эсвэл мөчлөгийн тохиргоо буруу байна : %s') % period.fiscalyear_id.name)
                
            q="select sum(debit) as debit,sum(credit) as credit,sum(amount_currency),l.partner_id,l.account_id \
                     from \
                     account_move_line l left join account_move m on m.id=l.move_id\
                     where \
                         l.account_id in {0} \
                         and l.date<='{1}' \
                         and l.partner_id={2} \
                         and m.state='posted' \
                    group by l.account_id,l.partner_id".format(tuple(account_ids2),form.date,form.partner_id.id)
#                          and currency_id={1} \
#                     form.currency_id.id,
#             print 'qqqqqq ',q
            

            self.env.cr.execute(q)
            fetched = self.env.cr.fetchall()
            context=context.copy()
            context.update({
           'p_date':form.date,
           'journal_id':form.journal_id.id,
#            period_id = period_id
            })
#             print "fetchedfetched ",fetched
            if fetched:
                for r in fetched:
                    amount_curr=0
                    debit=0
                    credit=0
                    amount_equalize=0
                    amount_curr=r[2]
                    type='income'
                    context.update({'date':form.date})
#                     amount = currency_obj.compute(cr, uid, form.currency_id.id, form.company_id.currency_id.id, amount_curr, context=context)
                    amount = self.env['res.currency'].with_context(date=form.date)._compute(form.currency_id, form.company_id.currency_id, amount_curr, round=False)

                    if account_obj.browse(r[4]).internal_type=='payable':
                        credit=r[1]-r[0]
                        amount_equalize=credit+amount
                        if amount_equalize<0:
                            type='expense'
#                         rate=credit/amount_curr
                    else:
                        debit=r[0]-r[1]
                        amount_equalize=amount-debit
                        if amount_equalize>0:
                            type='expense'
#                         rate=debit/amount_curr
                        
                    res.append({'debit':debit,
                           'credit':credit,
                           'partner_id':r[3],
                           'account_id':r[4],
                           'credit':credit,
                           'amount_currency':amount_curr,
                           'calc_currency':amount,
                           'amount_equalize':amount_equalize,
                           'type':type})
        return res
    
    def next(self):
#         journal_obj = self.browse(cr, uid, ids)[0]
#         if not journal_obj.journal_id:
#             raise osv.except_osv(_('Error'), _('Please select a journal!'))
        return self._to_view( {
                                           'state': 'done'
#                                                 , 'journal = journal_obj.journal_id.name
#                                                 , 'registered_at = journal_obj.registered_date
                                            })
            

    def _to_view(self, args):
#         if context is None:
#             context = { }
    
#         print "args ",args
        context =self.env.context
#         print 'context ',context
        line_obj=self.env['account.currency.equalization.line']
        partner_obj=self.env['res.partner']
        account_obj=self.env['account.account']
        res=self._get_datas()
#         print "res ",res
        self_br=self#.browse(cr,uid,ids[0])
        
        if not self_br.company_id.income_currency_exchange_account_id:
            raise osv.except_osv(_('Configuration Error!'), _('There is no income currency rate account defined for this company : %s') % line.company_id.name)
        else:
            income_acc=self_br.company_id.income_currency_exchange_account_id.id
        if not self_br.company_id.expense_currency_exchange_account_id:
            raise osv.except_osv(_('Configuration Error!'), _('There is no expense currency rate account defined for this company : %s') % line.company_id.name)
        else:
            expense_acc=self_br.company_id.expense_currency_exchange_account_id.id
            
        for r in res:
            if r['type']=='income':
                account=income_acc
            else:
                account=expense_acc
                
            line_id=line_obj.create( {
                   'name':partner_obj.browse(r['partner_id']).name+' '+self_br.date+u'  ханш тэгшитгэл',
                   'parent_id':self.ids[0],
                   'account_id':r['account_id'],
                   'partner_id':r['partner_id'],
                   'currency_id':self_br.currency_id.id,
                   'debit':r['debit'],
                   'credit':r['credit'],
                   'amount_currency':r['amount_currency'],
                   'amount_calc':r['calc_currency'],
                   'amount_equalize':r['amount_equalize'],
                   'type':r['type'],
                   'inc_exp_account_id':account,
#                    debit':r['debit'],
            })
            
            
#         args.update(d)
        self.write(args)
#         print 'self.ids ',self.ids
        return {
            'name':_('Currency Rate Equalization')
            , 'view_type':'form'
            , 'view_mode':'form'
            , 'view_id':False
            , 'res_model':'account.currency.equalization'
            , 'domain':[]
#             , 'context':context
            , 'context': dict(context, obj_id=self.ids)
            , 'type':'ir.actions.act_window'
            , 'target':'new'
            , 'res_id':self.ids and self.ids[0] or False
        }


    def action_equalize_partner(self):
        '''  Компаний үндсэн валютаас ялгаатай валютаар тохируулагдсан бүх дансуудыг
                    олж тайлант хугацаа буюу сүүлд тэгшитгэсэн огнооноос хойшхи 
                        эхний үлдэгдэл,
                        орлого,
                        зарлага,
                        эцсийн үлдэгдэл
                    зэргийг тооцоолж эцсийн үлдэгдэл дээр ханшийн тэгшитгэл хийнэ.
        '''
        context = self.env.context
        account_obj = self.env['account.account']
        account_move_line_obj = self.env['account.move.line']
        account_move_obj = self.env['account.move']
        fiscalyear_obj = self.env['account.fiscalyear']
        form = self#.browse(cr, uid, ids[0], context=context)
        currency_obj=self.env['res.currency']
#         period_id = self.env['account.period'].find(cr, uid, dt=form.date, context=context)[0]
#         period = self.env['account.period').browse(cr, uid, period_id, context=context)
        
        res = []
        # Өглөг авлагын үлдэгдэл бүр дээр тэгшитгэнэ.
            # Өглөг, авлага бүртгэсэн гүйлгээг тодорхойлохдоо тухайн санхүүгийн жилд бүртгэгдсэнийг
            # тодорхойлно. Учир нь өмнөх жилийн гүйлгээнүүд бүгд хаагдсан байх ёстой.
            # Мөн зөвхөн тухайн компаний өглөг, авлагыг тэгшитгэнэ.

        for line in form.line_ids:
#             move_id = account_move_obj.create({
#                'journal_id':form.journal_id.id,
# #                'period_id':period_id,
#                'date': form.date,
#                'narration': u'%s ханш тэгшитгэл' % (line.account_id.code+' '+form.name or '',),
#                'name': u'%s ханш тэгшитгэл' % (line.account_id.code+' '+form.name or '',),
#             })
#             print 'move_id ',move_id
#             res.append(move_id.id)
            amount=abs(line.amount_equalize)
            account_id1=line.account_id.id
            account_id2=line.inc_exp_account_id.id
            if (line.type=='income' and line.account_id.internal_type=='payable') or (line.type=='expense' and line.account_id.internal_type=='receivable'):
                line_vals=[]
#                 new_line_id1 = account_move_line_obj.create({
                line_vals.append([0,0,{
               'name':line.name,
               'debit':amount,
               'credit':0,
               'account_id':account_id1,
               'partner_id':line.partner_id.id,
               'company_id':form.company_id.id,
               'amount_currency':0,
               'currency_id':line.currency_id.id,
#                'state':'valid',
#                'move_id':move_id.id,
               'date':form.date,
               'journal_id':form.journal_id.id,
                }])
#                 new_line_id2 = account_move_line_obj.create({
                line_vals.append([0,0,{
               'name':line.name,
               'debit':0,
               'credit':amount,
               'account_id':account_id2,
               'partner_id':line.partner_id.id,
               'company_id':form.company_id.id,
               'amount_currency':0,
               'currency_id':line.currency_id.id,
#                'state':'valid',
#                'move_id':move_id.id,
               'date':form.date,
               'journal_id':form.journal_id.id,
#                'analytic_account_id':11264,
                    }])

                move_id = account_move_obj.create({
                   'journal_id':form.journal_id.id,
    #                'period_id':period_id,
                   'date': form.date,
                   'narration': u'%s ханш тэгшитгэл' % (line.account_id.code+' '+form.name or '',),
                   'name': u'%s ханш тэгшитгэл' % (line.account_id.code+' '+form.name or '',),
                    'line_ids': line_vals
                })
#                 print 'move_id ',move_id
                res.append(move_id.id)

#                 move_vals = {
#                     'name': new_name,#self.name+'/'+str(datetime.strptime(self.date, '%Y-%m-%d').year),
#                     'date': self.date,
#                     'ref': self.name,
#                     'journal_id': self.journal_id.id,
#                     'line_ids': line_vals
#                 }                
            else:
                new_line_id1 = account_move_line_obj.create({
               'name':line.name,
               'debit':0,
               'credit':amount,
               'account_id':account_id1,
               'partner_id':line.partner_id.id,
               'company_id':form.company_id.id,
               'amount_currency':0,
               'currency_id':line.currency_id.id,
               'state':'valid',
               'move_id':move_id.id,
               'date':form.date,
               'journal_id':form.journal_id.id,
                 })
                new_line_id2 = account_move_line_obj.create({
               'name':line.name,
               'debit':amount,
               'credit':0,
               'account_id':account_id2,
               'partner_id':line.partner_id.id,
               'company_id':form.company_id.id,
               'amount_currency':0,
               'currency_id':line.currency_id.id,
               'state':'valid',
               'move_id':move_id.id,
               'date':form.date,
               'journal_id':form.journal_id.id,
#                'analytic_account_id':11264,
                    })
            
#         # Гүйлгээнүүдийг батлах
#         if len(res) > 0 and not form.draft :
#             account_move_obj.post(cr, uid, res, context=context)
        
        # Бичигдсэн журналын бичилтүүдийг дэлгэцэнд харуулах
        return {
       'name':_('Equalization Entries'),
       'view_type':'form',
       'view_mode':'tree,form',
       'res_model':'account.move',
       'view_id':False,
#        'context':"{'visible_id':%(j)s, 'journal_id = %(j)d, 'search_default_journal_id':%(j)d}" % ({'j':form.journal_id.id}),
       'type':'ir.actions.act_window',
            #'search_view_id = res_id,
       'domain':(len(res) > 0 and "[('id', 'in', ["+ ','.join(map(str, res)) +"])]") or "[('id','=',False)]"
        }
                            
    def get_accounts(self, type=1):
        ''' Ханшийн тэгшитгэл хийх шаардлагатай дансуудыг тодорхойлно.
                Үүнд : Авлага өглөгийн данс болон гадаад валюттай данс
        '''
        context = self.env.context
        cr=self.env.cr
        wizobj = self#.browse(cr, uid, ids[0], context=context)
        if type == 1 :
            query = "SELECT a.id FROM account_account a WHERE a.internal_type not in ('view','consolidation','receivable','payable') AND company_id = %s " % wizobj.company_id.id
            query += " AND (a.currency_id is not null and a.currency_id <> %s) " % wizobj.company_id.currency_id.id
            if wizobj.currency_id:
                query += " AND a.currency_id = %s " % wizobj.currency_id.id
        elif type == 2 :
            query = "select account_id from account_move_line\
                         where currency_id =%s and account_id in\
                          (select id from account_account where internal_type in ('receivable','payable')) \
                          and  company_id = %s\
                         group by account_id " % (wizobj.currency_id.id,wizobj.company_id.id)
#             query += " AND (a.type in ('receivable','payable')) "
#         print "queryquery  ",query
        self.env.cr.execute(query)
        res = self.env.cr.fetchall()
#         print "resres ",res
        return [r[0] for r in res]


    def action_equalize(self):
        ''' 1. Авлага, өглөгийн дансны бүх гүйлгээг шүүж хамгийн сүүлд тэгшитгэсэн
                ханшаас одоогийн ханшний зөрүүгээр гүйлгээг тэгшитгэнэ. Ингэхдээ
                бүх өглөг, авлага төрөлд хамрагдах дансанд гүйлгээ хийсэн account.move
                үүдийг шүүж олно.
            
            2. Компаний үндсэн валютаас ялгаатай валютаар тохируулагдсан бүх дансуудыг
                олж тайлант хугацаа буюу сүүлд тэгшитгэсэн огнооноос хойшхи 
                    эхний үлдэгдэл,
                    орлого,
                    зарлага,
                    эцсийн үлдэгдэл
                зэргийг тооцоолж эцсийн үлдэгдэл дээр ханшийн тэгшитгэл хийнэ.
       '''
        context = self.env.context
        account_obj = self.env['account.account']
        account_move_line_obj = self.env['account.move.line']
        account_move_obj = self.env['account.move']
        fiscalyear_obj = self.env['account.fiscalyear']
        form = self#.browse(cr, uid, ids[0], context=context)
        currency_obj=self.env['res.currency']
        
        # Тэгшитгэл хийх шаардлагатай дансууд. Мөн өглөг, авлагын дансуудыг ялгана.
        if form.type == 'liquidity':
            account_ids1 = self.get_accounts(type=1)
            account_ids2 = []
        else :
            account_ids1 = []
            account_ids2 = self.get_accounts(type=2)
        res = []
        
        # Мөнгөн хөрөнгийн гадаад валютын дансуудын балансыг тэгшитгэнэ.
#         print "account_ids1 ",account_ids1
#        print "account_ids2 ",account_ids2
        if account_ids1 :
            res += account_obj.browse(account_ids1).currency_equalize_mn(form.date, 
                    form.company_id, form.journal_id.id, form.name)
        
        return {
       'name':_('Equalization Entries'),
       'view_type':'form',
       'view_mode':'tree,form',
       'res_model':'account.move',
       'view_id':False,
#        'context':"{'visible_id':%(j)s, 'journal_id = %(j)d, 'search_default_journal_id':%(j)d, 'search_default_period_id':%(p)d}" % ({'j':form.journal_id.id, 'p':period_id}),
       'type': 'ir.actions.act_window',
            #'search_view_id = res_id,
       'domain':(len(res) > 0 and "[('id', 'in', ["+ ','.join(map(str, res)) +"])]") or "[('id','=',False)]"
        }

account_currency_equalization()


class account_currency_equalization_line(models.TransientModel):
    """
        Гадаад валютаар хийгдсэн журналын бичилтүүдэд ханшийн тэгшитгэл хийнэ.
    """
    _name = "account.currency.equalization.line"
    _description = "Currency Rate Equalization line"
    
    name = fields.Char('Reason', size=128, required=True)
    parent_id = fields.Many2one('account.currency.equalization', 'Parent')
    account_id = fields.Many2one('account.account', 'Account', required=True)
    partner_id = fields.Many2one('res.partner', 'Partner', )
    currency_id = fields.Many2one('res.currency', 'Currency',required=True,)

    debit = fields.Float('Debit',digits_compute=dp.get_precision('Account'))
    credit = fields.Float('Credit',digits_compute=dp.get_precision('Account'))
    amount_currency = fields.Float('Amount currency',digits_compute=dp.get_precision('Account'))
    amount_calc = fields.Float('Amount calc',digits_compute=dp.get_precision('Account'))
    amount_equalize = fields.Float('Amount equalize',digits_compute=dp.get_precision('Account'))
    inc_exp_account_id = fields.Many2one('account.account', 'Account', required=True)
    type = fields.Selection([('income','Income'),('expense','Expense')], 'Type')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
