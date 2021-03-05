# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json, requests


import logging

class res_partner(models.Model):
    _inherit = 'res.partner'

    def _partner_receivable_payable_get(self):
        for partner in self:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
#             where_params = [tuple(self.ids)] + where_params
            where_params = [partner.id] + where_params
            self._cr.execute("""SELECT l.partner_id, act.type, SUM(l.debit)-SUM(l.credit) as amount 
                          FROM account_move_line l  
                          left join account_move m on l.move_id=m.id 
                          LEFT JOIN account_account a ON (l.account_id=a.id)
                          LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                          WHERE 
                          a.is_employee_recpay ='t' 
                          AND m.state='posted' 
                          AND l.partner_id = %s 
                          """ + where_clause + """ and l.company_id={0} 
                          GROUP BY l.partner_id, act.type
                          """.format(self.env.user.company_id.id), where_params)
            res=self._cr.fetchall()
#             print ('res ',res)
            if res:
                partner.receivable_payable =res[0][2]
            else:
                partner.receivable_payable =0

    receivable_payable = fields.Monetary(compute='_partner_receivable_payable_get', 
        string='Total Receivable', help="Total amount this customer owes you.")
        


    def _partner_receivable_payable_extra(self):
        for partner in self:
            tables, where_clause, where_params = self.env['account.move.line']._query_get()
#             where_params = [tuple(self.ids)] + where_params
            where_params = [partner.id] + where_params
            self._cr.execute("""SELECT l.partner_id, act.type, l.debit as debit,l.credit as credit 
                          FROM account_move_line l  
                          left join account_move m on l.move_id=m.id 
                          LEFT JOIN account_account a ON (l.account_id=a.id)
                          LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                          WHERE 
                          m.state='posted' 
                          AND l.partner_id = %s 
                          """ + where_clause + """ and l.company_id={0} 
                          """.format(self.env.user.company_id.id), where_params)
            res=self._cr.fetchall()
#             print ('res ',res)
            return res
