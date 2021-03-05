# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json, requests


import logging
import re
atext = r"[a-zA-Z0-9!#$%&'*+\-/=?^_`{|}~]"
dot_atom_text = re.compile(r"^%s+(\.%s+)*$" % (atext, atext))

class res_partner(models.Model):
    _inherit = 'res.partner'
    
    vat = fields.Char(string='TIN', help="Tax Identification Number. "
                                         "Fill it if the company is subjected to taxes. "
                                         "Used by the some of the legal statements.", copy=False)
    group_invoice = fields.Boolean(string='Invoice line group', copy=False)
    

    # @api.model
    # def create(self, vals):
    #     if not vals.get('vat'):
    #         raise UserError(_(u'Регистр оруулана уу '))
            
    #     res = super(res_partner, self).create(vals)
    #     return res 
    
    
    @api.constrains('vat')
    def _check_partner_vat(self):
        for item in self:
            if self.env['res.partner'].sudo().search([('vat','=',item.vat),('id','!=',item.id)]) and item.vat and not item.parent_id:  
                raise UserError(_('%s Partner register is duplicated  '%(item.name)))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ search full name and barcode """
        if args is None:
            args = []
        recs = self.search(['|', ('name', operator, name), ('vat', operator, name)] + args, limit=limit)
        return recs.name_get()

    def name_get(self):
        res = []
        for partner in self:
            
            res_name = super(res_partner, partner).name_get()
            if partner.ref:
                res_name = u''+res_name[0][1]+u' ['+partner.ref+']'
                res.append((partner.id, res_name))
            else:
                res.append(res_name[0])
        return res

    def get_partner_vatpayer(self, number):
        '''
            ebarimt сайтруу хандаж нөат төлөгч эсэхийг шалгагч
        '''
        url="http://info.ebarimt.mn/rest/merchant/info?regno="+str(number)+""
        vat=''
        try:
            r = requests.get(url)
            n = r.json()
            vat = n['name']
        except Exception:
            r=' '
            vat=False
            return ''
        return vat
    
    @api.onchange('vat')
    def onchange_vat_set(self):
        for item in self:
            if item.vat and not item.name:
                name = self.get_partner_vatpayer(item.vat)
                item.name=name
            
class PartnerCategory(models.Model):
    _inherit = 'res.partner.category'
    
    partner_count = fields.Integer(
        '# Partners', compute='_compute_partner_count',
        help="The number of partners under this category (Does not consider the children categories)")
    
    def _compute_partner_count(self):
        partners = self.env['res.partner'].search([('category_id', 'in', self.ids)])
        for categ in self:
#             partner_count = 0
            categ.partner_count = len(partners)    
            



class Alias(models.Model):
    """
     """
    _inherit = 'mail.alias'

    @api.constrains('alias_name')
    def _alias_is_ascii(self):
        """ The local-part ("display-name" <local-part@domain>) of an
            address only contains limited range of ascii characters.
            We DO NOT allow anything else than ASCII dot-atom formed
            local-part. Quoted-string and internationnal characters are
            to be rejected. See rfc5322 sections 3.4.1 and 3.2.3
            UNICODE err
        """
        if self.alias_name and not dot_atom_text.match(self.alias_name):
            print ("You cannot use anything else than unaccented latin characters in the alias address mw.")
#             raise ValidationError(_("You cannot use anything else than unaccented latin characters in the alias address."))
