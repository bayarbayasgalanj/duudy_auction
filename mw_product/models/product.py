# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons import decimal_precision as dp

# class PricelistItem(models.Model):
#     _inherit = "product.pricelist"
#     def _get_default_company_id(self):
#         return self.env.company.id
#     company_id = fields.Many2one('res.company', 'Company', default=_get_default_company_id, )

class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product', ondelete='cascade', check_company=False,
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")
    product_id = fields.Many2one(
        'product.product', 'Product Variant', ondelete='cascade', check_company=False,
        help="Specify a product if this rule only applies to one product. Keep empty otherwise.")
    
class ProductTemplate(models.Model):
    _inherit = "product.template"
    
    def _get_default_category_id(self):
        return super(ProductTemplate, self)._get_default_category_id()
        
    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    name = fields.Char('Name', index=True, required=True, translate=True, track_visibility='onchange')
    type = fields.Selection([
        ('consu', _('Consumable')),
        ('service', _('Service')),
        ('product', 'Stockable Product')
        ], string='Product Type', track_visibility='onchange',default='product')
    categ_id = fields.Many2one(
        'product.category', 'Internal Category',
        change_default=True, default=_get_default_category_id,
        required=True, help="Select category for the current product", track_visibility='onchange')

    
    # price fields
    list_price = fields.Float(
        'Sales Price', default=1.0,
        digits=dp.get_precision('Product Price'),
        help="Base price to compute the customer price. Sometimes called the catalog price.", track_visibility='onchange')
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('product.template'), index=1, track_visibility='onchange')
 
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the product without removing it.", track_visibility='onchange')
 
    product_code = fields.Char('Product code', index=True, track_visibility='onchange')

    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for all stock operations.", track_visibility='onchange')
    uom_po_id = fields.Many2one(
        'uom.uom', 'Purchase Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for purchase orders. It must be in the same category as the default unit of measure.", track_visibility='onchange')
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')], string="Tracking", help="Ensure the traceability of a storable product in your warehouse.", default='none', required=True, track_visibility='onchange')
    
    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч')
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч')
    sequence = fields.Integer('Sequence', default=1000, help='Gives the sequence order when displaying a product list')
    
    _sql_constraints = [('product_template_product_code_mw_uniq', 'unique (company_id,product_code)', 'Product code must unique MW')]

class ProductProduct(models.Model):
    _inherit = "product.product"
    
    default_code = fields.Char('Internal Reference', index=True, track_visibility='onchange')
    active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the product without removing it.", track_visibility='onchange')
    barcode = fields.Char(
        'Barcode', copy=False,
        help="International Article Number used for product identification.", track_visibility='onchange')

    product_code = fields.Char(related='product_tmpl_id.product_code')
    company_id = fields.Many2one('res.company', related='product_tmpl_id.company_id', store=True, readonly=True)

    _sql_constraints = [('product_product_default_code_mw_uniq', 'unique (company_id,default_code)', 'Default code must unique MW')]

    # def name_get(self):
    #     # TDE: this could be cleaned a bit I think

    #     def _name_get(d):
    #         name = d.get('name', '')
    #         code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
    #         p_code = d.get('product_code', False) or False
    #         if code:
    #             name = '[%s] %s' % (code,name)
    #         if p_code:
    #             p_name = '[%s] ' % (p_code)+''+name
    #             name = p_name
    #         return (d['id'], name)

    #     partner_id = self._context.get('partner_id')
    #     if partner_id:
    #         partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
    #     else:
    #         partner_ids = []
    #     company_id = self.env.context.get('company_id')

    #     # all user don't have access to seller and partner
    #     # check access and use superuser
    #     self.check_access_rights("read")
    #     self.check_access_rule("read")

    #     result = []

    #     # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
    #     # Use `load=False` to not call `name_get` for the `product_tmpl_id`
    #     self.sudo().read(['name', 'default_code', 'product_tmpl_id', 'attribute_value_ids', 'attribute_line_ids'], load=False)

    #     product_template_ids = self.sudo().mapped('product_tmpl_id').ids

    #     if partner_ids:
    #         supplier_info = self.env['product.supplierinfo'].sudo().search([
    #             ('product_tmpl_id', 'in', product_template_ids),
    #             ('name', 'in', partner_ids),
    #         ])
    #         # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
    #         # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
    #         supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
    #         supplier_info_by_template = {}
    #         for r in supplier_info:
    #             supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
    #     for product in self.sudo():
    #         # display only the attributes with multiple possible values on the template
    #         variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
    #         variant = product.attribute_value_ids._variant_name(variable_attributes)

    #         name = variant and "%s (%s)" % (product.name, variant) or product.name
    #         sellers = []
    #         if partner_ids:
    #             product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
    #             sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
    #             if not sellers:
    #                 sellers = [x for x in product_supplier_info if not x.product_id]
    #             # Filter out sellers based on the company. This is done afterwards for a better
    #             # code readability. At this point, only a few sellers should remain, so it should
    #             # not be a performance issue.
    #             if company_id:
    #                 sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
    #         if sellers:
    #             for s in sellers:
    #                 seller_variant = s.product_name and (
    #                     variant and "%s (%s)" % (s.product_name, variant) or s.product_name
    #                     ) or False
    #                 mydict = {
    #                           'id': product.id,
    #                           'name': seller_variant or name,
    #                           'default_code': s.product_code or product.default_code,
    #                           'product_code': product.product_code,
    #                           }
    #                 temp = _name_get(mydict)
    #                 if temp not in result:
    #                     result.append(temp)
    #         else:
    #             mydict = {
    #                       'id': product.id,
    #                       'name': name,
    #                       'default_code': product.default_code,
    #                       'product_code': product.product_code,
    #                       }
    #             result.append(_name_get(mydict))
    #     return result
    
    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     if not args:
    #         args = []
    #     if name:
    #         positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
    #         product_ids = []
    #         if operator in positive_operators:
    #             # product_ids = self._search([('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
    #             product_ids = self._search(['|',('product_tmpl_id.product_code','=',name),('default_code', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
    #             if not product_ids:
    #                 product_ids = self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid)
    #         if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
    #             # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
    #             # on a database with thousands of matching products, due to the huge merge+unique needed for the
    #             # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
    #             # Performing a quick memory merge of ids in Python will give much better performance
    #             # product_ids = self._search(args + [('default_code', operator, name)], limit=limit)
    #             product_ids = self._search(args + ['|',('product_tmpl_id.product_code', operator, name),('default_code', operator, name)], limit=limit)
    #             if not limit or len(product_ids) < limit:
    #                 # we may underrun the limit because of dupes in the results, that's fine
    #                 limit2 = (limit - len(product_ids)) if limit else False
    #                 product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)], limit=limit2, access_rights_uid=name_get_uid)
    #                 product_ids.extend(product2_ids)
    #         elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
    #             domain = expression.OR([
    #                 ['&', ('default_code', operator, name), ('name', operator, name)],
    #                 ['&', ('default_code', '=', False), ('name', operator, name)],
    #             ])
    #             domain = expression.AND([args, domain])
    #             product_ids = self._search(domain, limit=limit, access_rights_uid=name_get_uid)
    #         if not product_ids and operator in positive_operators:
    #             ptrn = re.compile('(\[(.*?)\])')
    #             res = ptrn.search(name)
    #             if res:
    #                 product_ids = self._search([('default_code', '=', res.group(2))] + args, limit=limit, access_rights_uid=name_get_uid)
    #         # still no results, partner in context: search on supplier info as last hope to find something
    #         if not product_ids and self._context.get('partner_id'):
    #             suppliers_ids = self.env['product.supplierinfo']._search([
    #                 ('name', '=', self._context.get('partner_id')),
    #                 '|',
    #                 ('product_code', operator, name),
    #                 ('product_name', operator, name)], access_rights_uid=name_get_uid)
    #             if suppliers_ids:
    #                 product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit, access_rights_uid=name_get_uid)
    #     else:
    #         product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
    #     return self.browse(product_ids).name_get()


class StockReportDetail(models.Model):
    _inherit = "stock.report.detail"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч')
    product_code = fields.Char(string='Код' ,readonly=True)

    def _select(self):
        select_str = super(StockReportDetail, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
        
    def _select2(self):
        select_str = super(StockReportDetail, self)._select2()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
        
    def _select3(self):
        select_str = super(StockReportDetail, self)._select3()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
    def _select4(self):
        select_str = super(StockReportDetail, self)._select4()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
    def _select_main(self):
        select_str = super(StockReportDetail, self)._select_main()
        select_str += """
            ,supplier_partner_id
            ,production_partner_id
            ,product_code
        """
        return select_str

class ProductBothIncomeExpenseReport(models.Model):
    _inherit = "product.both.income.expense.report"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    product_code = fields.Char(string='Код' ,readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч', readonly=True)

    def _select(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
        
    def _select2(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select2()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
        
    def _select3(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select3()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
    def _select4(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select4()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
    def _select_main(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select_main()
        select_str += """
            ,supplier_partner_id
            ,production_partner_id
            ,product_code
        """
        return select_str

class ProductIncomeExpenseReport(models.Model):
    _inherit = "product.income.expense.report"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    product_code = fields.Char(string='Код' ,readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч', readonly=True)

    def _select(self):
        select_str = super(ProductIncomeExpenseReport, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str


class ProductBalancePivotReport(models.Model):
    _inherit = "product.balance.pivot.report"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    product_code = fields.Char(string='Код' ,readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч', readonly=True)

    def _select(self):
        select_str = super(ProductBalancePivotReport, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
    def _select2(self):
        select_str = super(ProductBalancePivotReport, self)._select2()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str