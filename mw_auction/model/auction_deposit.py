# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from ast import literal_eval
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.tools.misc import ustr
from odoo.tools.translate import html_translate

class WebDeposit(models.Model):
    _name = 'web.deposit'
    _description = 'Web deposit'
    _inherit = ['mail.thread']

    # Columns
    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', string='Partner')
    line_ids = fields.One2many('web.deposit.line', 'parent_id', string='Lines', copy=True)
    balance = fields.Float(compute='_end_balance', store=True,)
    purchase_limit = fields.Float('Purchase limit')

    @api.depends('line_ids', 'line_ids.in_amount','line_ids.ex_amount')
    def _end_balance(self):
        for statement in self:
            statement.balance = sum([line.in_amount for line in statement.line_ids])-sum([line.ex_amount for line in statement.line_ids])

class WebCondictionLine(models.Model):
    _name = 'web.deposit.line'
    _description = 'Web condiction'

    # Columns
    name = fields.Char('Name')
    in_amount = fields.Float('Income')
    ex_amount = fields.Float('Expense')
    date = fields.Date('Date')
    parent_id = fields.Many2one('web.deposit', string='Parent')
    
