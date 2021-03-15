# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import datetime
import json
from datetime import timedelta, date
from odoo.http import request, Controller, route
from odoo.tools.safe_eval import safe_eval
from werkzeug.exceptions import NotFound
from odoo.exceptions import UserError
from odoo.addons.auth_signup.models.res_users import SignupError
import werkzeug

from odoo import http
import odoo
import logging
from odoo.tools.translate import _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.sale.controllers.variant import VariantController
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSale
from odoo.addons.website_sale_wishlist.controllers.main import WebsiteSaleWishlist
from psycopg2 import Error
import base64
from odoo.addons.emipro_theme_base.controller.main import EmiproThemeBase
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

class MWThemeBase(EmiproThemeBase):

#     @http.route('/web/login_custom', type='json', auth="none", methods=['GET', 'POST'],)
#     def web_login_custom(self, login, password, redirect=None, **kw):
#         values = {}
#         values['login_success'] = False
#         if not request.uid:
#             request.uid = odoo.SUPERUSER_ID
# 
#         values = request.params.copy()
#         try:
#             values['databases'] = http.db_list()
#         except odoo.exceptions.AccessDenied:
#             values['databases'] = None
# 
#         if request.httprequest.method == 'POST':
#             old_uid = request.uid
#             try:
#                 uid = request.session.authenticate(request.session.db, login, password)
#                 if uid:
#                     current_user = request.env['res.users'].sudo().search([('id', '=', uid)])
#                     if current_user.has_group('base.group_user'):
#                         values['user_type'] = 'internal'
#                     else:
#                         values['user_type'] = 'portal'
#                     values['login_success'] = True
# 
#             except odoo.exceptions.AccessDenied as e:
#                 request.uid = old_uid
#                 if e.args == odoo.exceptions.AccessDenied().args:
#                     values['error'] = _("Wrong login/password")
#                 else:
#                     values['error'] = e.args[0]
#         else:
#             if 'error' in request.params and request.params.get('error') == 'access':
#                 values['error'] = _('Only employee can access this database. Please contact the administrator.')
# 
#         if 'login' not in values and request.session.get('auth_login'):
#             values['login'] = request.session.get('auth_login')
# 
#         if not odoo.tools.config['list_db']:
#             values['disable_database_manager'] = True
#         return values
# def registration_submit(self, *args, **kw):
#         image = kw.get('image_1920', False)
# 
#         kw.update({
#             'free_member': True,
#             'image_1920': base64.encodestring(image.read()) if image else False
#         })
#         member = request.env['res.partner'].sudo().create(kw)
        
#     @http.route('/web/signup_custom', type='http', auth="user", methods=['POST'], website=True)
#     def web_auth_signup(self, **kw):
        
    @http.route('/web/signup_custom', type='json', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):

        qcontext = kw
        result = {}
        print ('aaammmmmm ')
        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                print ('qcontext ',qcontext)
#                 image = qcontext.get('ufile', False)
#                 print ('image ',image)
                values = {key: qcontext.get(key) for key in ('login', 'name', 'password')}#,'lastname'
#                 values.update({
#                             'free_member': True,
#                             'image_1920': base64.encodestring(image.read()) if image else False
#                         })
#                 print ('values ',values)
                if not values:
                    result.update({'is_success':False,'error':'The form was not properly filled in.'})
                    return result
                if values.get('password') != qcontext.get('confirm_password'):
                    result.update({'is_success': False, 'error': 'Passwords do not match; please retype them.'})
                    return result

                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    result.update({'is_success': False, 'error': 'Another user is already registered using this email address..'})
                    return result

                supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
                lang = request.context.get('lang', '').split('_')[0]
                if lang in supported_lang_codes:
                    values['lang'] = lang

                db, login, password = request.env['res.users'].sudo().signup(values, token=None)
                request.env.cr.commit()  # as authenticate will use its own cursor we need to commit the current transaction
                uid = request.session.authenticate(db, login, password)

                if not uid:
                    result.update({'is_success': False, 'error': 'Authentication Failed.'
                                   })
                    return result
                request.env.cr.commit()
                result.update({'is_success': True})
                return result

            except Error as e:
                result.update({'is_success': False, 'error': 'Could not create a new account.'})
                return result



# class AuthSignupMWHome(AuthSignupHome):
    

#     @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
#     def web_auth_signup(self, *args, **kw):
#         qcontext = self.get_auth_signup_qcontext()
#         print ('aaaaaaaa')
#         if not qcontext.get('token') and not qcontext.get('signup_enabled'):
#             raise werkzeug.exceptions.NotFound()
#         user_sudo=False
#         if 'error' not in qcontext and request.httprequest.method == 'POST':
#             try:
#                 self.do_signup(qcontext)
#                 # Send an account creation confirmation email
#                 if qcontext.get('token'):
#                     User = request.env['res.users']
#                     user_sudo = User.sudo().search(
#                         User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
#                     )
#                     print ('user_sudo ',user_sudo)
#                     template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
#                     if user_sudo and template:
#                         template.sudo().with_context(
#                             lang=user_sudo.lang,
#                             auth_login=werkzeug.url_encode({'auth_login': user_sudo.email}),
#                         ).send_mail(user_sudo.id, force_send=True)
#                 return self.web_login(*args, **kw)
#             except UserError as e:
#                 qcontext['error'] = e.name or e.value
#             except (SignupError, AssertionError) as e:
#                 if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
#                     qcontext["error"] = _("Another user is already registered using this email address.")
#                 else:
#                     _logger.error("%s", e)
#                     qcontext['error'] = _("Could not create a new account.")
#         print ('qcontext ',qcontext)
#         if user_sudo:
#             qcontext.update({'user':user_sudo})
#         else:
#             User = request.env['res.users']
#             user_sudo = User.sudo().search(
#                 [('id','=',1)], limit=1
#             )
#             
#             qcontext.update({'user':user_sudo})
#         response = request.render('auth_signup.signup', qcontext)
#         response.headers['X-Frame-Options'] = 'DENY'
#         print ('response---- ',response)
#         return response    

#     def do_signup(self, qcontext):
#         """ Shared helper that creates a res.partner out of a token """
#         
#         print ('qcontext22222 ',qcontext)
#         values = { key: qcontext.get(key) for key in ('login', 'name', 'password') }
#         if qcontext.get('ufile'):
#             image = qcontext.get('ufile').read()
#             values['image_1920'] = base64.b64encode(image)
#         
#         print ('values111 ',values)
#         if not values:
#             raise UserError(_("The form was not properly filled in."))
#         if values.get('password') != qcontext.get('confirm_password'):
#             raise UserError(_("Passwords do not match; please retype them."))
#         supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
#         lang = request.context.get('lang', '').split('_')[0]
#         if lang in supported_lang_codes:
#             values['lang'] = lang
#         self._signup_with_values(qcontext.get('token'), values)
#         request.env.cr.commit()
