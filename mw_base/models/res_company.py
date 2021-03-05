# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Res company'

    # Columns
    account_id = fields.Many2one('account.account', string='Зардлын данс')
    account_prepaid_id = fields.Many2one('account.account', string='Prepaid Account')
    account_payable_id = fields.Many2one('account.account', string='Payable Account')
    account_clearing_id = fields.Many2one('account.account', string='Clearing Account')
    account_partner_id = fields.Many2one('res.partner', string='Accounting partner')
    account_ndsh_id = fields.Many2one('account.account', string='Payable SHI')
    account_ndsh1_id = fields.Many2one('account.account', string='Expense SHI')
    journal_id = fields.Many2one('account.journal', string='Journal')
    account_pit_payable_id =fields.Many2one('account.account', string='PIT payable')
    account_employee_recievable_id =fields.Many2one('account.account', string='Employee receivable')
