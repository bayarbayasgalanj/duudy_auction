# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    useruud = fields.One2many('res.users', 'user_id', string='Хэрэглэгчид')

class ResUsers(models.Model):
    _inherit = 'res.users'

    def send_chat(self, html, partner_ids, with_mail=False, subject_mail=False):
        if not partner_ids:
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')
        channel_obj = self.env['mail.channel']
        messages = []
        for item in partner_ids:
            if item.useruud and self.env.user.company_id!=item.useruud[0].company_id:
                pass
            else:
                email = item.email or False
                if email and with_mail:
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
                if self.env.user.partner_id.id!=item.id:
                    channel_ids = channel_obj.search([
                        ('channel_partner_ids', 'in', [item.id])
                        ,('channel_partner_ids', 'in', [self.env.user.partner_id.id])
                        ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
                    if not channel_ids:
                        channel_ids = channel_obj.sudo().search([
                        ('channel_last_seen_partner_ids.partner_id', '=', item.id)
                        ,('channel_last_seen_partner_ids.partner_id', '=', self.env.user.partner_id.id)
                        ]).filtered(lambda r: len(r.channel_last_seen_partner_ids) == 2).ids
                    if not channel_ids:
                        vals = {
                            'channel_type': 'chat',
                            'name': u''+item.name+u', '+self.env.user.name,
                            'public': 'private',
                            'channel_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)],
                            'email_send': self.env.context.get('send_email',False)
                        }
                        new_channel = channel_obj.create(vals)
                        notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
                        new_channel.message_post(body=notification, message_type="notification", subtype="mail.mt_comment")
                        channel_info = new_channel.channel_info('creation')[0]
                        self.env['bus.bus'].sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info)
                        channel_ids = [new_channel.id]
                    if channel_ids:
                        mail_channel = channel_obj.browse(channel_ids[0])
                        message = mail_channel.with_context(mail_create_nosubscribe=True).message_post(body=html,message_type='comment',subtype='mail.mt_comment')
                        messages+=message
        return messages
