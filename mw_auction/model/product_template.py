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


        