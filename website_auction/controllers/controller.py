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

import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import Warning
from odoo.addons.sale.controllers.portal import CustomerPortal

class WebsiteAccount(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        partner_id = request.website._get_website_partner().id

        Auction = request.env['wk.website.auction']

        domain = [
            ('state','in',['complete','finish']),
            # ('winner_id', '=', partner_id)
        ]
        auctions = Auction.search(domain)
        auctions = auctions.filtered(lambda auction:auction.winner_id.id==partner_id)
        values.update({
            'win_auction_count': len(auctions),
        })
        return values

    @http.route(
        [
        '/my/auctions',
        '/my/auctions/page/<int:page>',
        ],
         type='http', auth="user", website=True)
    def portal_my_auctions(self, page=1, **kw):
        values = self._prepare_portal_layout_values()
        partner_id = request.website._get_website_partner().id

        Auction = request.env['wk.website.auction']
        domain = [
            ('state','in',['complete','finish']),
            # ('winner_id', '=', partner_id)
        ]
        auction_count = Auction.search_count(domain)
        pager = request.website.pager(
            url='/my/auctions',
            total=auction_count,
            page=page,
            step=5
        )
        auctions = Auction.search(domain, limit=5, offset=pager['offset'],order='id desc')
        auctions = auctions.filtered(lambda auction:auction.winner_id.id==partner_id)

        if not len(auctions):
            values['no_auctions']=1
        values['won_auctions'] = auctions
        values['pager'] = pager
        values['page_name'] = 'auctions'
        values['default_url'] ='/my/auctions'
        return  request.render("website_auction.my_auction", values)
    @http.route(
        [
            '/my/bids',
            '/my/bids/page/<int:page>',
        ],
         type='http', auth="user", website=True)
    def portal_my_bids(self, page=1, state=None,**kwargs):
        partner_id = request.website._get_website_partner().id
        values = self._prepare_portal_layout_values()
        Bidder = request.env['wk.auction.bidder'].sudo()
        domain = [('partner_id','=',partner_id)]
        if state=='active':
            domain+= [('state', '=', 'active')]
        else:
            domain+= [('state', '!=', 'active')]
        bid_count = Bidder.search_count(domain)
        pager = request.website.pager(
            url='/my/bids',
            total=bid_count,
            page=page,
            url_args={'state': state},

            step=5
        )
        # search the count to display, according to the pager data
        bids = Bidder.search(domain, limit=5, offset=pager['offset'],order='id desc')
        if state=='active' :
            values['no_active_bids']=not len(bids)
            values['active_bids'] = bids
        else:
            values['no_bids']=not len(bids)
            values['all_bids'] = bids
        values['pager'] = pager
        values['page_name'] = 'auctions'
        return  request.render("website_auction.my_auction", values)

class WebsiteSale(website_sale):

    @http.route(['/shop/confirm_order'], type='http', auth="public", website=True)
    def confirm_order(self, **post):
        order = request.website.sale_get_order()

        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection


        order.onchange_partner_shipping_id()
        order.order_line._compute_tax_id()
        request.session['sale_last_order_id'] = order.id
        request.website.sale_get_order(update_pricelist=False)
        extra_step = request.env.ref('website_sale.extra_info_option')
        if extra_step.active:
            return request.redirect("/shop/extra_info")

        return request.redirect("/shop/payment")

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        r = super(WebsiteSale, self).product(product, category, search, **kwargs)
        wk_auction = product.sudo()._get_nondraft_auction()
        if wk_auction and not(wk_auction.product_sale):
            wk_auction.sudo().set_auction_state();
            r.qcontext.update(wk_auction.get_publish_fields())
        return r

    @http.route(
        ['/auction/place/bid'],
        type='http', auth="public", website=True)
    def auction_place_bid(self,**post):
        auction_obj=request.env['wk.website.auction'].sudo().browse(int(post.get('auction_fk')))
        referrer  =request.httprequest.referrer and request.httprequest.referrer or '/shop/product/%s'%(auction_obj.product_tmpl_id.id)
        website_partner=request.website._get_website_partner()
        if not website_partner:
            return werkzeug.utils.redirect(referrer+ "#loginfirst")
        if auction_obj.state not in ['running', 'extend']:
            return werkzeug.utils.redirect(referrer+ "#bid_notallow")
        try:
            res = auction_obj.create_bid(post.get('bid_type'),float(post.get('bid_offer')),website_partner.id)
            return werkzeug.utils.redirect(referrer + "#bidsubmit" )
        except MinimumBidException as e:
            return werkzeug.utils.redirect(referrer + "#minbid" )
        except AutoBidException as e:
            return werkzeug.utils.redirect(referrer + "#autobid" )
        except Exception as e:
            _logger.info("Auction Error %r",e)
            return werkzeug.utils.redirect(referrer + "#biderr" )
        return werkzeug.utils.redirect(referrer)

    @http.route(
        ['/auction/buy/now/<model("wk.website.auction"):auction_obj>'],
        type='http', auth="public", website=True)
    def auction_buy_now(self,auction_obj,**post):
        order = request.website.sale_get_order(force_create=1)
        res = request.env['website.virtual.product'].sudo().add_virtual_product(
            order_id=order.id,
            product_id=auction_obj.product_id,
            product_price=auction_obj.buynow_price,
            virtual_source='wk_website_auction',
        )
        return werkzeug.utils.redirect('/shop/cart' + "#create" )


    @http.route(
        ['/auction/cart/create/<model("wk.website.auction"):auction_obj>',
        '/auction/cart/update/<model("wk.website.auction"):auction_obj>'],
        type='http', auth="public", website=True)
    def auction_cart_create(self,auction_obj,**post):
        auction_obj = auction_obj.sudo()
        referrer  =request.httprequest.referrer and request.httprequest.referrer or '/shop/product/%s'%(auction_obj.product_tmpl_id.id)
        if auction_obj.state=='complete':
            order = request.website.sale_get_order(force_create=1)
            res = request.env['website.virtual.product'].sudo().add_virtual_product(
                order_id=order.id,
                product_id=auction_obj.product_id,
                product_price=auction_obj.current_price,
                virtual_source='wk_website_auction',
            )
            if res:
                auction_obj.order_id=order.id
                auction_obj.action_finish_auction()
        return werkzeug.utils.redirect(referrer + "#create" )

    @http.route(
        ['''/auction/unsubscribe/<model("wk.website.auction"):auction_obj>/<string:deactivate_token>'''],
        type='http', auth="public", website=True)
    def auction_unsubscribe(self,auction_obj,deactivate_token=None,**post):
        referrer  =request.httprequest.referrer and request.httprequest.referrer or '/shop/product/%s'%(auction_obj.product_tmpl_id.id)
        partner = request.website._get_website_partner()
        if not partner:
            return werkzeug.utils.redirect(referrer+ "#loginfirst")
        subscriber_obj =  request.env['wk.auction.subscriber']
        template_unsubscribe =request.env.ref('website_auction.notify_subscriber_unsubscribe', False)
        try:
            subscriber= auction_obj.sudo().get_active_subscriber().filtered(lambda subscriber: subscriber.deactivate_token==deactivate_token)
            if subscriber:
                subscriber.sudo().write({'subscribe':False})
                template_unsubscribe.sudo().send_mail(subscriber.id, force_send=True)
            return werkzeug.utils.redirect(referrer+ "#unsubscribed")
        except Exception as e:
            return werkzeug.utils.redirect(referrer + "#biderr" )


        return werkzeug.utils.redirect(referrer)




    @http.route(
        ['''/auction/subscribe/<model("wk.website.auction","[('state','!=','close')]"):auction_obj>'''],
        type='http', auth="public", website=True)
    def auction_subscribe(self,auction_obj,deactivate_token=None,**post):

        referrer  =request.httprequest.referrer and request.httprequest.referrer or '/shop/product/%s'%(auction_obj.product_tmpl_id.id)
        partner = request.website._get_website_partner()
        if not partner:
            return werkzeug.utils.redirect(referrer+ "#loginfirst")
        subscriber_obj =  request.env['wk.auction.subscriber']
        template_subscribe =request.env.ref('website_auction.notify_subscriber_subscribe', False)
        try:
            if partner not in auction_obj.subscriber_ids.mapped('partner_id'):
                subscriber=subscriber_obj.sudo().create(
                            {'partner_id':partner.id,
                            'wk_auction_fk':auction_obj.id,
                            })
                if subscriber:template_subscribe.sudo().send_mail(subscriber.id, force_send=True)
                return werkzeug.utils.redirect(referrer+ "#subscribe")

            elif partner in auction_obj.subscriber_ids.filtered(lambda s: not s.subscribe).mapped('partner_id'):
                subscriber=subscriber_obj.sudo().search(
                            [('partner_id','=',partner.id),
                            ('wk_auction_fk','=',auction_obj.id)],order='create_date desc')
                if subscriber:
                    subscriber.sudo().write({'subscribe':True})
                    template_subscribe.sudo().send_mail(subscriber.id, force_send=True)
                return werkzeug.utils.redirect(referrer+ "#subscribe")
        except Exception as e:
            return werkzeug.utils.redirect(referrer + "#biderr" )


        return werkzeug.utils.redirect(referrer)


    @http.route(
        ['/product/auction/<model("wk.website.auction"):auction_obj>',
         '/product/auction/<model("wk.website.auction"):auction_obj>/page/<int:page>'
        ],
        type='http', auth="public", website=True)
    def auction_product_bids(self,auction_obj,page=1,**post):
        values={}
        values.update(auction_obj.sudo().get_publish_fields())
        bid_record=[]
        Bidder = request.env['wk.auction.bidder'].sudo()
        domain = [('bid_type','!=','auto'),('auction_fk', '=', auction_obj.id)]
        bid_count = Bidder.search_count(domain)
        pager = request.website.pager(
            url='/product/auction/%s'%(auction_obj.id),
            # url_args={'date_begin': date_begin, 'date_end': date_end},
            total=bid_count,
            page=page,
            step=5
        )
        # search the count to display, according to the pager data
        bidders = Bidder.search(domain, limit=5, offset=pager['offset'],order='id desc')
        values['bidders'] = bidders
        values['pager'] = pager
        return request.render("website_auction.product_auction",values )


class website_virtual_product(website_virtual_product):
    def wk_website_auction_product_remove(self,temp):
        sale_order_line=request.env['sale.order.line'].sudo().search(
            [('id', '=', temp),('virtual_source','=','wk_website_auction')]
        )
        if sale_order_line:
            auction_ids=request.env['wk.website.auction'].search([
                ('winner_id','=',request.website._get_website_partner().id),
                ('order_id','=',sale_order_line.order_id.id),
                ('state','in',['complete','finish']),
            ])
            if auction_ids:
                for auction_obj in auction_ids:
                    auction_obj.order_id=None
                    auction_obj.action_complete_auction()#='complete'
        return sale_order_line.unlink()
