from odoo import api, fields, models, _


class Product(models.Model):
    _inherit = "product.product"
    
    def action_view_stock_move_lines_mw(self):
        self.ensure_one()
        action = self.env.ref('stock.stock_move_action').read()[0]
        domain_quant = action['domain']
        if domain_quant:
            domain_quant = []
        domain_quant.append(('product_id', '=', self.id))
        action['domain'] = domain_quant
        return action

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_view_stock_move_lines_mw(self):
        self.ensure_one()
        action = self.env.ref('stock.stock_move_action').read()[0]
        domain_quant = action['domain']
        if domain_quant:
            domain_quant = []
        domain_quant.append(('product_id.product_tmpl_id', 'in', self.ids))
        domain_quant.append(('company_id', 'child_of', self.env.user.company_id.id))
        action['domain'] = domain_quant
        return action