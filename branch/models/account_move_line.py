# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval

class account_move_line(models.Model):

    _inherit = 'account.move.line'






    @api.model
    def _query_get(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(str(domain)) or []
        date_field = 'date'
        branch_id = 'branch_id'            
        if context.get('aged_balance'):
                date_field = 'date_maturity'
                 
        if context.get('branch_ids'):
                domain += [(branch_id, '=', context['branch_ids'])]

        if context.get('date_to'):
                domain += [(date_field, '<=', context['date_to'])]
        if context.get('date_from'):
                if not context.get('strict_range'):
                    domain += ['|', (date_field, '>=', context['date_from']), ('account_id.user_type_id.include_initial_balance', '=', True)]
                elif context.get('initial_bal'):
                    #Түр дансдын эхний үлдэгдлийг оны эхнээс авах.
    #                 domain += [(date_field, '<', context['date_from'])]
    #                 Оны 01 сарын 01 ээс бол эхний үлдэгдэл < дээр 0 гарна. 
                    domain += ['|','&', ('account_id.user_type_id.include_initial_balance', '=', True),
                               (date_field, '<', context['date_from']),
                               '&',
#                                ('account_id.user_type_id.include_initial_balance', '=', False),buruu garch bn
                               (date_field, '<', context['date_from']),
#                                (date_field, '>=', context['date_from'].split('-')[0]+'-01-01')
                               (date_field, '>=', str(context['date_from'].year)+'-01-01')
                               ]
                      
#хур ашиг тооцох
#                     domain += [
#                                 '|','|','&',
#                                 ('account_id.user_type_id.include_initial_balance', '=', True),
#                                (date_field, '<', context['date_from']),
#                                '&',
# #                                ('account_id.user_type_id.include_initial_balance', '=', False),buruu garch bn
#                                (date_field, '<', context['date_from']),
#                                (date_field, '>=', context['date_from'].split('-')[0]+'-01-01'),
#                                 '|',
#                                 ('account_id.id', '=', 3800),
#                                 ('account_id.user_type_id.include_initial_balance', '=', False),
#                                (date_field, '<', context['date_from']),
#                                ]
#                             (AND) OR (AND) OR (AND)
                       
#                     domain += ['|','&',('journal_id.special', '=', True),
#                            (date_field, '<=', context['date_from']),
#                            '&',
#                            (date_field, '<', context['date_from']),
#                            (date_field, '>=', context['date_from'].split('-')[0]+'-01-01')]

                else:
                    domain += [(date_field, '>=', context['date_from'])]

        if context.get('journal_ids'):
                domain += [('journal_id', 'in', context['journal_ids'])]

        state = context.get('state')
        if state and state.lower() != 'all':
                domain += [('move_id.state', '=', state)]

        if context.get('company_id'):
                domain += [('company_id', '=', context['company_id'])]

        if 'company_ids' in context:
                domain += [('company_id', 'in', context['company_ids'])]

        if context.get('reconcile_date'):
                domain += ['|', ('reconciled', '=', False), '|', ('matched_debit_ids.create_date', '>', context['reconcile_date']), ('matched_credit_ids.create_date', '>', context['reconcile_date'])]

        if context.get('account_tag_ids'):
                domain += [('account_id.tag_ids', 'in', context['account_tag_ids'].ids)]

        if context.get('analytic_tag_ids'):
                domain += ['|', ('analytic_account_id.tag_ids', 'in', context['analytic_tag_ids'].ids), ('analytic_tag_ids', 'in', context['analytic_tag_ids'].ids)]

        if context.get('analytic_account_ids'):
                domain += [('analytic_account_id', 'in', context['analytic_account_ids'].ids)]

        where_clause = ""
        where_clause_params = []
        tables = ''
        if domain:
                query = self._where_calc(domain)
                tables, where_clause, where_clause_params = query.get_sql()
        return tables, where_clause, where_clause_params

