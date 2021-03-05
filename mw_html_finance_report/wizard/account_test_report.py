# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import time
import datetime
from datetime import datetime


class MWAccountTetsReport(models.TransientModel):
    _name = 'mw.account.test.report'
    _description = 'Account report'

    account_id = fields.Many2one('account.account', 'Account', domain=[('user_type_id.type','in',['payable','receivable'])])
    date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))
            
    def _prepare_report_data(self):
        data = {
            'account_id': self.account_id.id,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return data

    def print_report(self):
        self.ensure_one()
        data = self._prepare_report_data()
#         return self.env.ref('mw_html_finance_report.action_report_account_test').report_action(None, data=data)

        result_context=dict(self._context or {})
        data = self.read()
#         print ('self.date_from1',self.date_from)
#         if self.date_from:
#             result_context.update({'date_from': self.date_from})
#         if self.date_to:
#             result_context.update({'date_to': self.date_to})
#         result_context.update({'company_id': self.company_id.id})
#         result_context.update({'strict_range': True})
    
        ir_model_obj = self.env['ir.model.data']
        report_id = self.env['mw.account.report'].create({'name':'report1',
                                                                    'account_id':self.account_id.id,
                                                                    'date_from':self.date_from,
                                                                    'date_to':self.date_to
                                                                    })
        print ('report_id ',report_id)
        model, action_id = ir_model_obj.get_object_reference('mw_html_finance_report', 'action_mw_account_report')
        # print 'action_id ',action_id
        [action] = self.env[model].browse(action_id).read()
        action['context'] = result_context
        action['res_id'] = report_id.id
        print ('action ',action)
        return action
        

