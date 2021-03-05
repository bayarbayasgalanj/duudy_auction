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
#
#
############################################################################################

from odoo import api, fields, models, _

class account_bank_line_change(models.TransientModel):
    _name = "account.bank.line.change"
    _description = "Line change"
 
    name= fields.Char('Name',required=True, )
    bank_account_id = fields.Many2one('res.partner.bank', string='Bank account',)
    bank_line_id = fields.Many2one('account.bank.statement.line', string='Bank line',)
    partner_id = fields.Many2one('res.partner', string='Bank partner',)
    cash_type_id = fields.Many2one('account.cash.move.type', string="Cash type")
    ref= fields.Char(u'Дугаар', )
    
    @api.model
    def default_get(self, fields):
        rec = super(account_bank_line_change, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
#         department_id=False
        if context.get('active_model',False) and context['active_model']=='account.bank.statement.line':
            statement_line=self.env['account.bank.statement.line']
            line=statement_line.browse(active_ids)[0]
            name=line.name
            rec['name'] = name
            if line.bank_account_id:
                bank_account_id=line.bank_account_id.id
                rec['bank_account_id'] = bank_account_id
            if line.partner_id:
                partner_id=line.partner_id.id
                rec['partner_id'] = partner_id
            if line.cash_type_id:
                cash_type_id=line.cash_type_id.id
                rec['cash_type_id'] = cash_type_id
            if line.ref:
                rec['ref'] = line.ref
            rec['bank_line_id']=line.id
        return rec

    def account_bank_line_change(self):
        result_context=dict(self._context or {})
        vals={}
        if self.name:
            vals.update({'name':self.name})
        if self.bank_account_id:
            vals.update({'bank_account_id':self.bank_account_id.id})
        if self.cash_type_id:
            vals.update({'cash_type_id':self.cash_type_id.id})
        if self.ref:
            vals.update({'ref':self.ref})
        self.bank_line_id.write(vals)
        return True
    
