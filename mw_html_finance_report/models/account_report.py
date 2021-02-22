# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import time
import datetime
from datetime import datetime


class AccountReportReport(models.TransientModel):
    _name = 'mw.account.report'
    _description = 'Account test report'
    
    name = fields.Char("Name")
#     wizard_id = fields.Integer('ID')
    account_id = fields.Many2one('account.account', 'Account')
    date_from = fields.Date("Start Date",default=time.strftime('%Y-%m-01'))
    date_to = fields.Date("End Date",default=time.strftime('%Y-%m-%d'))

    def get_data_js(self):
        print ('self123 ',self)
        result = {
            'line_ids': [],
        }

        time_line = []
        print (',self.wizard_id.account_id ',self.date_from)
        print (',self.wizard_id.account_id ',self.account_id)
        for item in self.env['account.move.line'].search([('account_id','=',self.account_id.id),
                                                          ('date','>',self.date_from),
                                                          ('date','<',self.date_to),
                                                          ]):
                print ('item' ,item)
#             for line in item:
                time_line.append({
                    'date': item.date,
                    'debit': item.debit,
                    'name':item.name,
                    'credit':item.credit,
                })

        result['line_ids'] = time_line


        return result
        