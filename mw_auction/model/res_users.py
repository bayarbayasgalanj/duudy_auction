# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from ast import literal_eval
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.tools.misc import ustr
from odoo.tools.translate import html_translate

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    _description = 'Leads'

    image_pass = fields.Image('ID Card')    


class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Res partner'
 
    # Columns
    lastname = fields.Char('Last name')
    image_pass = fields.Image('ID Card')   
    ccode = fields.Char('Confirm code')

class WebCondiction(models.Model):
    _name = 'web.condition'
    _description = 'Web condiction'

    # Columns
    name = fields.Char('Name')
    content = fields.Html('Content', translate=html_translate, sanitize=False)
    
class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Res users'
# 
#     # Columns
#     lastname = fields.Char('Last name')
#     image_pass = fields.Image('ID Card')    


# 
#     @api.model
#     def create(self, vals_list):
# #         print ('vals_list ',vals_list)
#         new_recs = super(ResUsers, self).create(vals_list)
# #         print ('new_recs ',new_recs)
# #         print (a)
#         return new_recs    



    def _create_user_from_template(self, values):
        template_user_id = literal_eval(self.env['ir.config_parameter'].sudo().get_param('base.template_portal_user_id', 'False'))
        template_user = self.browse(template_user_id)
        if not template_user.exists():
            raise ValueError(_('Signup: invalid template user'))

        if not values.get('login'):
            raise ValueError(_('Signup: no login given for new user'))
        if not values.get('partner_id') and not values.get('name'):
            raise ValueError(_('Signup: no name or partner given for new user'))

        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
        try:
            with self.env.cr.savepoint():
                tmp = template_user.with_context(no_reset_password=True).copy(values)
                print ('tmp ',tmp)
                print ('tmp2 ',tmp.partner_id)
                self.env['crm.lead'].sudo().create({'name':'New user: '+tmp.partner_id.name,
                                                    'partner_id':tmp.partner_id.id,
                                                    'type':'opportunity'})
                return tmp
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))