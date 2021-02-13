# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "Website Auction",
  "summary"              :  "Using this module, add Auction feature on your Website.",
  "category"             :  "Website",
  "version"              :  "0.1",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "maintainer"           :  "Prakash Kumar",
  "website"              :  "https://store.webkul.com/Odoo-Website-Auction.html",
  "description"          :  """https://webkul.com/blog/odoo-website-auction/
  Module Provide Auction feature on Odoo eCommerce Website.""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=website_auction&version=12.0",
  "depends"              :  [
                             'website_sale',
                             'website_sale_management',
                             'website_mail',
                             'website_virtual_product',
                             'website_webkul_addons',
                            ],
  "data"                 :  [
                             'edi/wk_auction_bidder.xml',
                             'edi/wk_auction_subscriber.xml',
                             'edi/wk_auction_admin.xml',
                             'data/cron.xml',
                             'data/data.xml',
                             'views/website_auction.xml',
                             'views/product_template.xml',
                             'views/my_account_template.xml',
                             'views/inherited_virtual_product.xml',
                             'views/auction_res_config.xml',
                             'views/webkul_addons_config_inherit_view.xml',
                             'views/auction_product_bids_template.xml',
                             'security/ir.model.access.csv',
                            ],
  "demo"                 :  ['demo/demo.xml'],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  True,
  "installable"          :  True,
  "price"                :  149,
  "currency"             :  "EUR",
}
