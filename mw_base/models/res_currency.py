# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class Currency(models.Model):
    _inherit = "res.currency"
    _description = "Currency"

    @api.model
    def _get_conversion_rate(self, from_currency, to_currency, company, date):
        currency_rates = (from_currency + to_currency)._get_rates(company, date)
        res = currency_rates.get(from_currency.id) / currency_rates.get(to_currency.id)
        return res
