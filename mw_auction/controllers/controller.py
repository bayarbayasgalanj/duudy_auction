# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
import werkzeug
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale as  website_sale
from odoo.addons.website_virtual_product.controllers.main import website_virtual_product
from odoo.addons.website_auction.models.website_auction_exception import *

from werkzeug.exceptions import Forbidden, NotFound
from odoo.addons.website_sale.controllers.main import TableCompute as  TableCompute

import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import Warning
from odoo.addons.sale.controllers.portal import CustomerPortal
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.osv import expression
class WebsiteSale(website_sale):

    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def _get_search_domain(self, search, category, attrib_values, model_values=None,make_values=None, search_in_description=True):
        domains = [request.website.sale_product_domain()]
        if search:
            for srch in search.split(" "):
                subdomains = [
                    [('name', 'ilike', srch)],
                    [('product_variant_ids.default_code', 'ilike', srch)]
                ]
                if search_in_description:
                    subdomains.append([('description', 'ilike', srch)])
                    subdomains.append([('description_sale', 'ilike', srch)])
                domains.append(expression.OR(subdomains))

        if category:
            domains.append([('public_categ_ids', 'child_of', int(category))])
#         print ('model_values22 ',model_values)
        if model_values:
            mdls = None
            ids = []
            for value in model_values:
                ids.append(value[0])
            if ids:
                domains.append([('product_model_id','in',ids)])
                
        if make_values:
            mdls = None
            ids = []
            for value in make_values:
                ids.append(value[0])
            if ids:
                domains.append([('product_make_id','in',ids)])
                                
                
        return expression.AND(domains)
    
    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        add_qty = int(post.get('add_qty', 1))
        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = request.env['website'].get_current_website().shop_ppg or 20

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        attrib_list = request.httprequest.args.getlist('attrib')
#         print ('attrib_list ',attrib_list)
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
#         print ('attributes_ids ',attributes_ids)
#model
        model_list = request.httprequest.args.getlist('mdls')
        model_values = [[int(x) for x in v.split("-")] for v in model_list if v]
        model_ids = {v[0] for v in model_values}
        model_set = {v[1] for v in model_values}
#make
        make_list = request.httprequest.args.getlist('mks')
        make_values = [[int(x) for x in v.split("-")] for v in make_list if v]
        make_ids = {v[0] for v in make_values}
        make_set = {v[1] for v in make_values}

#         print ('model_values',model_values)
#         print ('attrib_values ',attrib_values)
        domain = self._get_search_domain(search, category, attrib_values,model_values,make_values)

        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list, order=post.get('order'))

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)
#         print ('domain ',domain)
        search_product = Product.search(domain, order=self._get_search_order(post))
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            search_categories = Category.search([('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)

        product_count = len(search_product)
        pager = request.website.pager(url=url, total=product_count, page=page, step=ppg, scope=7, url_args=post)
        offset = pager['offset']
        products = search_product[offset: offset + ppg]
        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        PModel = request.env['product.model.category']
#         print ('model_ids ',model_ids)
#         if model_ids:
#             models = PModel.browse(model_ids)
#         else:
        models  = PModel.search([])
            
        PMake = request.env['product.make.category']
        makes  = PMake.search([])
                        
        print ('makes ',makes)

        layout_mode = request.session.get('website_sale_shop_layout_mode')
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'

        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg, ppr),
            'ppg': ppg,
            'ppr': ppr,
            'categories': categs,
            'attributes': attributes,
            'keep': keep,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'models':models,
            'model_set':model_set,
            'makes':makes,
            'make_set':make_set
        }
        print ('category123 ',category)
        if category:
            values['main_object'] = category
        return request.render("website_sale.products", values)
