# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import json
import math
import re

from werkzeug import urls

from odoo import fields as odoo_fields, http, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError
from odoo.http import content_disposition, Controller, request, route
from odoo.tools import consteq

from odoo.addons.portal.controllers.portal import CustomerPortal

import string
import random
# --------------------------------------------------
# Misc tools
# --------------------------------------------------


class CustomerPortalMW(CustomerPortal):

    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id", "lastname"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name","ufile","pfile","url_param","pass_img","clear_image","clear_pass_image"]
# 
#     @route(['/my', '/my/home'], type='http', auth="user", website=True)
#     def home(self, **kw):
#         values = self._prepare_home_portal_values()
#         return request.render("portal.portal_my_home", values)

    def _prepare_user_values(self, **kwargs):
        kwargs.pop('edit_translations', None) # avoid nuking edit_translations
        values = {
            'user': request.env.user,
            'is_public_user': request.website.is_public_user(),
            'validation_email_sent': request.session.get('validation_email_sent', False),
            'validation_email_done': request.session.get('validation_email_done', False),
        }
        values.update(kwargs)
        return values
    
    @route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })
        print ('post111 ',post)
        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
            if not error:
                values = {key: post[key] for key in self.MANDATORY_BILLING_FIELDS}
                values.update({key: post[key] for key in self.OPTIONAL_BILLING_FIELDS if key in post})
                for field in set(['country_id', 'state_id']) & set(values.keys()):
                    try:
                        values[field] = int(values[field])
                    except:
                        values[field] = False
                values.update({'zip': values.pop('zipcode', '')})
                print ('values1 ',values)
#                 if  values.get('ufile',False):
#                     image = values.get('ufile').read()
# #                     print ('image4 ',image)
# #                     values['image_1920'] = base64.b64encode(image)
#                     request.env.user.sudo().write({'image_1920':base64.b64encode(image)})
# #                     del values['url_param']
#                     del values['ufile']
#                 if values.get('pfile',False):
# #                     print ('values3 ',post)
#                     image = values.get('pfile').read()
#                     request.env.user.sudo().write({'image_pass':base64.b64encode(image)})
#                     lead = request.env['crm.lead'].sudo().search([('partner_id','=',partner.id)])
#                     if lead:
# #                         image = data.get('pfile').read()
#                         lead.sudo().write({'image_pass':base64.b64encode(image)})
#                     
#                     del values['pass_img']
#                     del values['pfile']
                if 'url_param' in values.keys():
                    del values['url_param']
                if 'pass_img' in values.keys():
                    del values['pass_img']
                if 'ufile' in values.keys():
                    del values['ufile']
                if 'pfile' in values.keys():
                    del values['pfile']
                    
                if 'clear_image' in values.keys():
                    del values['clear_image']
                    request.env.user.sudo().write({'image_1920':''})
                if 'clear_pass_image' in values.keys():
                    del values['clear_pass_image']
                    request.env.user.sudo().write({'image_pass':''})
                    
                print ('values2 ',values)
                partner.sudo().write(values)
                
                if redirect:
                    return request.redirect(redirect)
#                 return request.redirect('/my/home')
                #Хэрэв форм пост хийсэн бол дараагийн зураг алхам
                return request.redirect('/my/idcard')

        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        print ('post ',post)
        values.update({
            'partner': partner,
            'countries': countries,
            'states': states,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
            'user':request.env.user,
            'url_param': post.get('url_param'),
        })

        response = request.render("portal.portal_my_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @route(['/my/idcard'], type='http', auth='user', website=True)
    def account_card(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })
#         print ('post333 ',post)
#         print ('partner ',partner)
        vals={}
        if post and request.httprequest.method == 'POST':
#             error, error_message = self.details_form_validate(post)
#             values.update({'error': error, 'error_message': error_message})
            values.update(post)
#             if not error:
            if  values.get('ufile',False):
                image = values.get('ufile').read()
#                 print ('image ',image)
#                     request.env.user.sudo().write({'image_1920':base64.b64encode(image)})
                partner.write({'image_1920':base64.b64encode(image)})
#                     del values['url_param']
                del values['ufile']
            if values.get('pfile',False):
#                     print ('values3 ',post)
                image = values.get('pfile').read()
#                     request.env.user.sudo().write({'image_pass':base64.b64encode(image)})
                partner.write({'image_pass':base64.b64encode(image)})
                lead = request.env['crm.lead'].sudo().search([('partner_id','=',partner.id)])
                if lead:
#                         image = data.get('pfile').read()
                    lead.sudo().write({'image_pass':base64.b64encode(image)})
                
#                     del values['pass_img']
#                     del values['pfile']
#                 if 'url_param' in values.keys():
#                     del values['url_param']
#                 if 'pass_img' in values.keys():
#                     del values['pass_img']
#                 if 'ufile' in values.keys():
#                     del values['ufile']
#                 if 'pfile' in values.keys():
#                     del values['pfile']
                
            if 'clear_image' in values.keys():
                del values['clear_image']
                partner.sudo().write({'image_1920':''})
            if 'clear_pass_image' in values.keys():
                del values['clear_pass_image']
                partner.sudo().write({'image_pass':''})
                
#             print ('values2 ',values)
#             partner.sudo().write(vals)
            
            if redirect:
                return request.redirect(redirect)
#                 return request.redirect('/my/home')
            #Хэрэв форм пост хийсэн бол дараагийн зураг алхам
            return request.redirect('/my/ccode')

#         print ('post ',post)
        values.update({
            'partner': partner,
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
            'user':request.env.user,
            'url_param': post.get('url_param'),
        })

        response = request.render("mw_auction.portal_my_card_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response


    @route(['/my/ccode'], type='http', auth='user', website=True)
    def account_code(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })
        print ('post444 ',post)
        print ('partner ',partner)
        vals={}
        if post and request.httprequest.method == 'POST':
#             error, error_message = self.details_form_validate(post)
#             values.update({'error': error, 'error_message': error_message})
            values.update(post)
            
            if redirect:
                return request.redirect(redirect)
#                 return request.redirect('/my/home')
            #Хэрэв форм пост хийсэн бол дараагийн зураг алхам
            if post.get('ccode'):
#                 print ('partner.ccode ',partner.ccode)
                if post['ccode']==partner.ccode:
                    print ('heviin')
                else:
                    values.update({'error': {'ccode':'error'}, 'error_message': 'wrong code'})                
                    response = request.render("mw_auction.portal_my_code_details", values)
                    response.headers['X-Frame-Options'] = 'DENY'
                    return response            
            code_values={'success':True,'msg':'Code accepted!'}
            response = request.render("portal.portal_my_home", code_values)
            response.headers['X-Frame-Options'] = 'DENY'
            return response

#             return request.redirect('/my/home')

#         print ('post ',post)
        cc=''
        if post.get('ccode'):
#             print ('partner.ccode ',partner.ccode)
            if post['ccode']==partner.ccode:
                print ('heviin')
            else:
                values.update({'error': 'ccode', 'error_message': 'wrong code'})                
        else:
            letters = string.ascii_lowercase
            cc= ''.join(random.choice(letters) for i in range(5))
            partner.sudo().write({'ccode':cc})
        
        values.update({
            'partner': partner,
            'phone': partner.phone and partner.phone[:4]+'** ****' or '',
            'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'my_details',
            'user':request.env.user,
            'url_param': post.get('url_param'),
            'ccode':cc
        })

        response = request.render("mw_auction.portal_my_code_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def details_form_validate(self, data):
        error = dict()
        error_message = []

        # Validation
        for field_name in self.MANDATORY_BILLING_FIELDS:
#             print ('data ',data)
            if not data.get(field_name):
#                 print ('field_name ',field_name)
                #darmaa
                if field_name not in ('url_param','pass_img'):
#                     if data.get('ufile',False):
#                         data[field_name]=data.get('ufile',False)
#                     else:
#                         error[field_name] = 'missing'
#                 else:
#                     error[field_name] = 'missing'
#                 if field_name=='pass_img':
#                     if data.get('pfile',False):
#                         data[field_name]=data.get('pfile',False)
#                     else:
#                         error[field_name] = 'missing'
#                 else:
                    error[field_name] = 'missing'
#         print ('error 1 ',error)
        # email validation
        if data.get('email') and not tools.single_email_re.match(data.get('email')):
            error["email"] = 'error'
            error_message.append(_('Invalid Email! Please enter a valid email address.'))

        # vat validation
        partner = request.env.user.partner_id
#       Зурагийг 2 ашиглаж болохгүй тул
#         lead = request.env['crm.lead'].sudo().search([('partner_id','=',partner.id)])
#         if lead:
#             image = data.get('pfile').read()
#             lead.sudo().write({'image_pass':base64.b64encode(image)})
            
        if data.get("vat") and partner and partner.vat != data.get("vat"):
            if partner.can_edit_vat():
                if hasattr(partner, "check_vat"):
                    if data.get("country_id"):
                        data["vat"] = request.env["res.partner"].fix_eu_vat_number(int(data.get("country_id")), data.get("vat"))
                    partner_dummy = partner.new({
                        'vat': data['vat'],
                        'country_id': (int(data['country_id'])
                                       if data.get('country_id') else False),
                    })
                    try:
                        partner_dummy.check_vat()
                    except ValidationError:
                        error["vat"] = 'error'
            else:
                error_message.append(_('Changing VAT number is not allowed once document(s) have been issued for your account. Please contact us directly for this operation.'))

        # error message for empty required fields
        print ('error ',error)
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        unknown = [k for k in data if k not in self.MANDATORY_BILLING_FIELDS + self.OPTIONAL_BILLING_FIELDS]
        print ('unknown22 ',unknown)
        if unknown:
            error['common'] = 'Unknown field'
            error_message.append("Unknown field '%s'" % ','.join(unknown))

        return error, error_message



    @route(['/my/condition'], type='http', auth='user', website=True)
    def condition(self, redirect=None, **post):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        values.update({
            'error': {},
            'error_message': [],
        })
        print ('post222 ',post)
        if post and request.httprequest.method == 'POST':
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values.update(post)
        print ('post ',post)
        
        conditions = request.env['web.condition'].sudo().search([],limit=1)
#         print ('conditions ',conditions)
        values.update({
            'partner': partner,
            'condition': len(conditions) and conditions[0] or 'Empty conditions',
#             'states': states,
#             'has_check_vat': hasattr(request.env['res.partner'], 'check_vat'),
            'redirect': redirect,
            'page_name': 'condition_details',
            'user':request.env.user,
            'url_param': post.get('url_param'),
        })

        response = request.render("mw_auction.condition_details", values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
