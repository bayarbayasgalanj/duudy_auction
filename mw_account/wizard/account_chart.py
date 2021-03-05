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
class account_chart(models.TransientModel):
    _name = "account.chart"
    _description = "Account chart"
 
    date_from= fields.Date('date from',required=True, )
    date_to= fields.Date('date to',required=True, )
    target_move= fields.Selection([('posted', 'All Posted Entries'),
                                         ('all', 'All Entries'),
                                        ], 'Target Moves', required=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    
#     _defaults = {
#         'date_from': lambda *a: time.strftime('%Y-%m-%d'),
#         'date_to': lambda *a: time.strftime('%Y-%m-%d'),
#         'target_move': 'posted'
#     }
        
    def account_chart_open_window(self):
#         mod_obj = self.env['ir.model.data']
#         act_obj = self.env['ir.actions.act_window']
#         context = {}
#         result = mod_obj.get_object_reference('mw_account', 'action_account_tree')
#         id = result and result[1] or False
#         result = act_obj.read()
        
#             mod_obj = self.env['ir.model.data']        
#             search_res = mod_obj.get_object_reference('mw_stock_product_report', 'product_income_expense_report_search')
#             search_id = search_res and search_res[1] or False
#             pivot_res = mod_obj.get_object_reference('mw_stock_product_report', 'product_income_expense_report_pivot2')
#             pivot_id = pivot_res and pivot_res[1] or False
        
#         result_context = safe_eval(result.get('context', '{}'))
        result_context=dict(self._context or {})
        data = self.read()
        print ('self.date_from1',self.date_from)
        if self.date_from:
            result_context.update({'date_from': self.date_from})
        if self.date_to:
            result_context.update({'date_to': self.date_to})
        result_context.update({'company_id': self.company_id.id})
#         if data['target_move']:
#             result_context.update({'state': data['target_move']})
        result_context.update({'strict_range': True})
#         result['context'] = str(result_context)
        
#         res = self.env['ir.actions.act_window'].for_xml_id('mw_account', 'action_account_tree')
# #         res['domain'] = [('res_model', '=', 'hr.expense'), ('res_id', 'in', self.ids)]
#         res['context'] =  str(result_context)
#         return res
    
        ir_model_obj = self.env['ir.model.data']
        model, action_id = ir_model_obj.get_object_reference('mw_account', 'action_account_form_mn')
        # print 'action_id ',action_id
        [action] = self.env[model].browse(action_id).read()
        print ('result_context ',result_context)
        action['context'] = result_context
        print ('action ',action)
#         if ctx.get('use_domain', False):
#             action['domain'] = ['|', ('journal_id', '=', self.id), ('journal_id', '=', False)]
#             action['name'] += ' for journal ' + self.name
        return action
    

#         return {
#                 'name': 'open',
#                 'view_type': 'form',
#                 'view_mode': 'pivot',
#                 'res_model': 'product.income.expense.report',
#                 'view_id': False,
#                 'views': [(pivot_id, 'pivot')],
#                 'search_view_id': search_id,
#                 'domain': [('id','in',result_ids)],
#                 'type': 'ir.actions.act_window',
#                 'target': 'current'
#             }        

#         return result
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
