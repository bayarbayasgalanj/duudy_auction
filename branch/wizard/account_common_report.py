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


class AccountCommonReport(models.TransientModel):
    _inherit = "account.common.report"

    branch_ids = fields.Many2one('res.branch', string='Branch')
                                          



    def _build_contexts(self, data):
        result = super(AccountCommonReport, self)._build_contexts(data)
        data = {}
        data['form'] = self.read(['branch_ids'])[0]
        result['branch_ids'] = \
            'branch_ids' in data['form'] \
            and data['form']['branch_ids'] or False
        branch_name_long = ''
        if result['branch_ids']:
                branch_name = self.env['res.branch'].browse(result['branch_ids'][0]).name
                branch_name_long += branch_name  
        result['branch_ids'] = branch_name_long
        return result







# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
