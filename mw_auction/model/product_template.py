from odoo import models
from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_model_id = fields.Many2one(
        'product.model.category',
        string='Model',
        help='Select a model for this product'
    )

    product_make_id = fields.Many2one(
        'product.make.category',
        string='Make',
        help='Select a make for this product'
    )    
    

class ProductModelCategory(models.Model):
    _name = "product.model.category"
    _description = "Product model Category"

    name = fields.Char("Category Name", required=True, translate=True)
    sequence = fields.Integer("Sequence", default=10, index=True)




class ProductMakeCategory(models.Model):
    _name = "product.make.category"
    _description = "Product make Category"

    name = fields.Char("Manufacturer Name", required=True, translate=True)
    sequence = fields.Integer("Sequence", default=10, index=True)

class ProductWishlist(models.Model):
    _inherit = 'product.wishlist'

    auction_id = fields.Many2one('wk.website.auction', string='Auction')

    @api.model
    def _add_to_wishlist(self, pricelist_id, currency_id, website_id, price, product_id, partner_id=False):
        if product_id:
            product = self.env['product.product'].browse(product_id)
            auctions=product.tmpl_auction_ids.filtered(lambda m: m.state == 'confirmed')
            print ('auctions',auctions)
        wish = self.env['product.wishlist'].create({
            'partner_id': partner_id,
            'product_id': product_id,
            'currency_id': currency_id,
            'pricelist_id': pricelist_id,
            'price': price,
            'website_id': website_id,
            'auction_id':auctions and auctions[0].id
        })
        
        return wish        
    