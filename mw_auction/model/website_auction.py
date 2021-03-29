# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2017-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE URL <https://store.webkul.com/license.html/> for full copyright and licensing details.
#################################################################################
from lxml import etree
from dateutil.relativedelta import relativedelta
from datetime import date, datetime,timedelta
from pytz import timezone
import logging
from odoo import api, fields, models
from odoo.addons.website_auction.models.website_auction_exception import *
from odoo.exceptions import  ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import datetime 

_logger = logging.getLogger(__name__)


class WkWebsiteAuction(models.Model):

    _inherit = "wk.website.auction"

    wish_ids = fields.One2many(
        string='Whishlists',
        comodel_name='product.wishlist',
        inverse_name='auction_id',
        copy=False
    )
    

    @api.model
    def check_auction_time_cron(self):
        now = datetime.datetime.now()
        now_plus_10 = now + datetime.timedelta(minutes = 10)
        print ('now_plus_10 ',now_plus_10)
        auction_ids=self.env['wk.website.auction'].search([('state','in',['confirmed']),('start_date','<=',now_plus_10)])
        print ('auction_ids ',auction_ids)
        if auction_ids:
            for a in auction_ids:
                print ('a ',a.wish_ids)
                if a.wish_ids:
                    partner_ids=[]
                    for w in a.wish_ids:
                        partner_ids.append(w.partner_id)
                    print ('send email chat to {0}'.format(partner_ids))
                    for item in partner_ids:
                        email = item.email or False
                        if email:
                            subject_mail='Auction starting ...'
                            html = u'<b>Дуудлага худалдаа эхлэхэд 10 минут үлдлээ</b><br/>%s </br>'%(a.name)
                            try:
                                self.env['mail.mail'].create({
                                'body_html': html,
                                'subject': '%s' % (subject_mail or ''),
                                'email_to': email,
                                'auto_delete': False,
                                'state': 'outgoing'
                            }).send()
                            except Exception as e:
                                _logger.info('send mail aldaa %s'%(e))
                                pass                    




    def action_confirmed_auction(self):
        if self.filtered(lambda auction: auction.state != 'draft'):
            raise ValidationError('Only draft auction can set to confirm.')
        for record in self.filtered(lambda auction: auction.state == 'draft'):
            wl=self.env['product.wishlist'].search([('product_id','=',record.product_id.id)])
#             print ('wl ',wl)
            if wl:
                wl.write({'auction_id':record.id})
            record.state = 'confirmed'
            record.notify_auction_state()
        return True


# 
#     @api.model
#     def create_bid(self,bid_type,bid_offer,partner_id):
#         bidder_pool =  self.env['wk.auction.bidder']
#         deposit_pool =  self.env['web.deposit']
#         if partner_id:
# 
#             deposits=deposit_pool.search([('partner_id','=',partner_id)
#                                 ])
#             if deposits:
#                 query1 = """
#                                 select max(bid_offer),auction_fk 
#                                                             from wk_auction_bidder b 
#                                                                     left join wk_website_auction a on b.auction_fk=a.id 
#                                                             where b.state='active' and partner_id={0} and a.state='running' group by auction_fk;
#                             """.format(partner_id)
#                 
#                 self.env.cr.execute(query1)
#                 query_result = self.env.cr.dictfetchall()
#                 amount_bids=0
#                 if query_result:
#                     for re in query_result:
# #                         print ('re ',re)  
#                         amount_bids+=re['max']
# #                 bidders=bidder_pool.search([('partner_id','=',partner_id),
# #                                 ('state','=','active'),
# #                                 ('auction_fk.state','=','running')
# #                                 ])
# 
#                 if amount_bids:
#                     amount_bid = amount_bids#sum([x.bid_offer for x in bidders])
#                     print ('amount_bid ',amount_bid)
#                     amount_deposit = sum([x.purchase_limit for x in deposits])
#                     print ('amount_deposit ',amount_deposit)
#                     if amount_deposit<(amount_bid+bid_offer):
#                         result = dict(message='',err_type=None)
#                         result['message'] = 'Барьцаанаас хэтэрсэн байна. Лимит {0} нийт бит {1}'.format(amount_deposit,amount_bid+bid_offer)
#                         raise ValidationError(result['message'])
#                     
#         res = super(WkWebsiteAuction, self).create_bid(bid_type,bid_offer,partner_id)
#         return res


    @api.model
    def wk_create_bid(self,bid_type,bid_offer,partner_id):
#         auto_bidder,next_bid =self.get_bid_related_entity()
#         s_vals = dict(bid_type=bid_type,bid_offer=bid_offer,partner_id=partner_id,auction_fk=self.id)
#         res=self.env['wk.auction.bidder'].create(s_vals)
#         self.create_unique_subscriber(partner_id)#Create Subscriber
#         if self._context.get('auctual_bid_type','simple')!='auto':
#             self.notify_auction_bidder_subscriber(res.partner_id)#NOtify Bidder and subscriber
            
        bidder_pool =  self.env['wk.auction.bidder']
        deposit_pool =  self.env['web.deposit']
        if partner_id:
 
            deposits=deposit_pool.search([('partner_id','=',partner_id)
                                ])
            if deposits:
                #одоо хожиж яваа бид
                query = """select 
                            max(bid_offer),auction_fk,partner_id 
                                                            from wk_auction_bidder b 
                                                                    left join wk_website_auction a on b.auction_fk=a.id 
                                                            where b.state='active' and a.state='running' group by auction_fk,partner_id
                            """
                 
                self.env.cr.execute(query)
                query_result = self.env.cr.dictfetchall()
                amount_bids=0
                win_bids={}
                if query_result:
                    for re in query_result:
                        if win_bids.get('partner_id',False):
                            if win_bids['max']<re['max']:
                                win_bids['max']=re['max']
                                win_bids['partner_id']=re['partner_id']
                        else:
                            win_bids={'max':re['max'],
                                      'partner_id':re['partner_id'],
                                      'auction_fk':re['auction_fk'],
                                      }
#                         amount_bids+=re['max']
                print ('win_bids ',win_bids)
                #Нийт тавьсан барьцаа DARAA DUUSGAH         
                query1 = """
                                select max(bid_offer),auction_fk 
                                                            from wk_auction_bidder b 
                                                                    left join wk_website_auction a on b.auction_fk=a.id 
                                                            where a.id<>{1} and b.state='active' and partner_id={0} and a.state='running' group by auction_fk;
                            """.format(partner_id,self.id)
                 
                self.env.cr.execute(query1)
                query_result = self.env.cr.dictfetchall()
                amount_bids=0
                if query_result:
                    for re in query_result:
#                         print ('re ',re)  
                        amount_bids+=re['max']
#                 bidders=bidder_pool.search([('partner_id','=',partner_id),
#                                 ('state','=','active'),
#                                 ('auction_fk.state','=','running')
#                                 ])
 
                if amount_bids:
                    amount_bid = amount_bids#sum([x.bid_offer for x in bidders])
                    print ('amount_bid ',amount_bid)
                    amount_deposit = sum([x.purchase_limit for x in deposits])
                    print ('amount_deposit ',amount_deposit)
                    if amount_deposit<(amount_bid+bid_offer):
                        result = dict(message='',err_type=None)
                        result['message'] = 'Барьцаанаас хэтэрсэн байна. Лимит {0} нийт бит {1}'.format(amount_deposit,amount_bid+bid_offer)
                        raise ValidationError(result['message'])
                                 
        res = super(WkWebsiteAuction, self).wk_create_bid(bid_type,bid_offer,partner_id)
            
        return res
    
        
#     @api.model
#     def _validate_bid(self,bid_type,bid_offer):
#         result = dict(message='',err_type=None)
#         auto_bidder,next_bid =self.get_bid_related_entity()
#         _logger.info("111===auto_bidder: %r====next_bid: %r"%(auto_bidder,next_bid))
#         _logger.info("111===bid_offer: %r====%r"%(bid_offer,next_bid))
#         if bid_type=='simple' and bid_offer  < next_bid :
#             result['message'] = 'Your Bid %s Not Satisfying the  Minimum Bid Amount Criteria .\n It should be at-least %s.' % (bid_offer,next_bid)
#             raise MinimumBidException(result['message'])
#         elif bid_type=='auto':
#             auto_bid_offer = auto_bidder and auto_bidder.bid_offer or next_bid
#             auto_bid_increment = auto_bid_offer+self._get_next_autobid_increment()
#             _logger.info("2222===auto_bid_offer: %r====bid_offer: %r==auto_bid_increment: %r"%(auto_bid_offer,
#             bid_offer,auto_bid_increment))
#             if  auto_bid_offer>=bid_offer:
#                 print ('--------------------21')
#                 result['message'] = "You auto bid amount range [{0}] is already opt by some other bidder.\nPlease Increase your auto bid range to a large extent.".format(bid_offer)
#                 raise AutoBidException(result['message'])
#             elif  bid_offer< auto_bid_increment:
#                 print ('--------------------22')
#                 result['message'] = 'Your Bid Not Satisfying the  Minimum Auto Bid Amount Criteria .\n It should be at-least %s' % (next_bid)
#                 raise MinimumBidException(result['message'])
            