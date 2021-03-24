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
            print ('wl ',wl)
            if wl:
                wl.write({'auction_id':record.id})
            record.state = 'confirmed'
            record.notify_auction_state()
        return True

