from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time, datetime

class CashBoxOut(models.TransientModel):
    _inherit = 'cash.box.out'
    _description = 'Cash Box Out'


    @api.model
    def _get_default_date(self):
        context = dict(self.env.context)
        active_id = self.env['account.bank.statement'].browse(context.get('active_id'))
        return active_id.date

    
    partner_id = fields.Many2one('res.partner', u'Харилцагч')
    account_id = fields.Many2one('account.account', u'Данс')
    branch_id = fields.Many2one('res.branch', u'Салбар')
    date = fields.Date(u'огноо',default=_get_default_date)
    
    def _calculate_values_for_statement_line(self, record):
        res=super(CashBoxOut , self )._calculate_values_for_statement_line(record)
        if self.partner_id:
            res.update({'partner_id':self.partner_id.id})
        if self.account_id:
            res.update({'account_id':self.account_id.id})
        if self.branch_id:
            res.update({'branch_res_id':self.branch_id.id})
        if self.date:
            res.update({'date':self.date})
            
        return res




class CashBoxTranfer(CashBoxOut):
    _name = 'cash.box.tranfer'
    
#     @api.model
#     def default_get(self, fields):
#         res = super(CashBoxTranfer, self).default_get(fields)
#         if 'account_id' in fields:
#             res.update({'account_id': 18479})
#         return res
# 
# 
#     @api.multi
#     @api.depends('name_id')
#     def compute_name(self):
#         for f in self:
#             name=''
#             if not f.name and f.name_id:
#                 f.name = f.name_id.name
#             elif not f.name:
#                 f.name=u'Шилжүүлэг'
# #                 if f.id:
# #                     f.write({'name':f.name_id.name})
#                     
#     @api.model
#     def create(self,vals):
#         if not vals.has_key('name'):
#             if vals.has_key('name_id'):
#                 names=self.env['account.cashbox.name']
#                 vals['name']=names.browse(vals['name_id']).name
#         return super(CashBoxTranfer, self).create(vals)
                    
#     name = fields.Char('Name', compute='compute_name', store=True)
    income_statement_id = fields.Many2one('account.bank.statement', string='Statement',domain=[('state','in',('draft','open')),])
    type = fields.Selection([('income',u'Орлого'),('expense',u'Зарлага')], string='Type',default='expense')
#     name_id = fields.Many2one('account.cashbox.name', string='Name')
    date = fields.Date("Date",default=time.strftime('%Y-%m-%d'))
#     @api.onchange('name_id')
#     def onchange_name_id(self):
#         for f in self:
#             name=''
#             f.name = f.name_id.name

    def _calculate_values_for_statement_line(self, record,account_id):
#         if not record.journal_id.company_id.transfer_account_id:
#             raise UserError(_("You should have defined an 'Internal Transfer Account' in your cash register's journal!"))
        amount = self.amount
        if self.type=='income':
            amount = self.amount
        elif self.type=='expense':
            amount = -self.amount
        return {
            'date': self.date,
            'statement_id': record.id,
            'journal_id': record.journal_id.id,
            'amount':amount,
            'partner_id': self.partner_id.id or False,
            'account_id': record.journal_id.company_id.transfer_account_id.id,
            'name': self.name,
#             'transfer_account_id':account_id,
#             'branch_res_id':record.branch_id.id or False
            'branch_res_id':self.branch_id and self.branch_id.id or record.branch_id and record.branch_id.id or False,
        }
        

    def _calculate_values_for_statement_income_line(self, record,account_id,id):
#         if not record.journal_id.company_id.transfer_account_id:
#             raise UserError(_("You should have defined an 'Internal Transfer Account' in your cash register's journal!"))
#         amount = self.amount or 0.0
        amount = self.amount
        if self.type=='income':
            amount = -self.amount
        elif self.type=='expense':
            amount = self.amount
        return {
            'date': self.date,
            'statement_id': record.id,
            'journal_id': record.journal_id.id,
            'amount': amount,
            'partner_id': self.partner_id.id or False,
#             'account_id': self.account_id.id,
            'account_id':record.journal_id.company_id.transfer_account_id.id,
            'name': self.name,
            'branch_res_id':self.branch_id and self.branch_id.id or record.branch_id and record.branch_id.id or False,
#             'transfer_account_id':account_id,
            'transfer_line_id':id[0].id
        }
        
        
    def run(self):
        if self.date:
            # end=time.strftime('%Y-%m-{0}'.format(str(calendar.monthrange(int(time.strftime('%y')),int(time.strftime('%m')))[1])))
            bks=self.env['account.bank.statement'].search([('id','=',self.income_statement_id.id),
                                                           ('state','=','open')])
            # print '------------------',bks, '---------'
            if len(bks)>0:
                dt1 = str(bks.date.year)+'-'+str(bks.date.month)
                dt2 = str(self.date.year)+'-'+str(self.date.month)
                # print '-----------------aaaaaaaaaaaaaa-',dt1, dt2
                if dt1 != dt2:
                    raise UserError(_(u'Таны хийж буй гүйлгээний сар шилжүүлж буй касс эсвэл харилцахын сараас зөрж байна.!\n Тухайн сарын гүйлгээ тухайн сардаа хийгдэнэ.'))
                else:
                    context = dict(self._context or {})
                    active_model = context.get('active_model', False)
                    active_ids = context.get('active_ids', [])
                    records = self.env[active_model].browse(active_ids)
                    return self._run(records)
            else:
                raise UserError(_(u'Тухайн сарын касс байхгүй байна.! \n Мөнгөн хөрөнгийн нягтланд хандана уу.'))
        else:
            raise UserError(_(u'Огноо оруулна уу.!'))

    def _run(self, records):
#         print ('records ',records)
        context = dict(self._context or {})
        active_model = context.get('active_model', False)
        active_ids = context.get('active_ids', [])
        records = self.env[active_model].browse(active_ids)

#         records = self.env['account.bank.statement'].browse(records.income_statement_id)

        for box in self:
            for record in records:
                if not record.journal_id:
                    raise UserError(_("Please check that the field 'Journal' is set on the Bank Statement"))
#                 if not record.journal_id.company_id.transfer_account_id:
#                     raise UserError(_("Please check that the field 'Transfer Account' is set on the company."))
                self_account_id = box.income_statement_id.journal_id.default_debit_account_id.id
                id=box._create_bank_statement_self_line(record,self_account_id)
#                 transfer_account_id=record.journal_id.default_debit_account_id.id
                transfer_account_id = record.journal_id.company_id.transfer_account_id.id
                box._create_bank_statement_income_line(box.income_statement_id,transfer_account_id,id)
        return {}

    def _create_bank_statement_income_line(self, record,account_id,id):
        line_obj = self.env['account.bank.statement.line']
        if record.state == 'confirm':
            raise UserError(_("You cannot put/take money in/out for a bank statement which is closed."))
        values = self._calculate_values_for_statement_income_line(record,account_id,id)
        id=line_obj.create(values)
        return id
#         return record.write({'line_ids': [(0, False, values[0])]})

    def _create_bank_statement_self_line(self, record,account_id):
        line_obj = self.env['account.bank.statement.line']
        if record.state == 'confirm':
            raise UserError(_("You cannot put/take money in/out for a bank statement which is closed."))
        values = self._calculate_values_for_statement_line(record,account_id)
        id=line_obj.create(values)
        return id