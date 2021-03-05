# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError, ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Res users'

    # Columns
    manager_user_ids = fields.Many2many('res.users','res_user_manager_users_rel','user_id','manager_id',
        string='Батлах хэрэглэгчид',
    )

class DynamicFlow(models.Model):
    _name = 'dynamic.flow'
    _description = 'Dynamic Flow'
    _order = 'sequence, id'

    name = fields.Char(string='Name', required=True, translate=True)
    description = fields.Text(translate=True)
    sequence = fields.Integer(default=1)
    branch_ids = fields.Many2many('res.branch', string='Салбарууд', )
    line_ids = fields.One2many('dynamic.flow.line', 'flow_id', string='Line', required=True, copy=True)
    categ_ids = fields.Many2many('product.category', 'dynamic_flow_product_categ_rel', 'flow_id', 'categ_id', string='Category', copy=True)
#     type = fields.Selection([('purchase_request','Purchase Request')], string='Type',)
    model_id = fields.Many2one('ir.model', string="Model name", help="Your model name")
    is_amount = fields.Boolean(string="Мөнгөн дүгээс хамаарсан", default=False)
    user_ids = fields.Many2many('res.users', 'dynamic_flow_allowed_users_rel', 'flow_id', 'user_id', string='Хэрэглэгчид')
    active = fields.Boolean(default=True)

class DynamicFlowLine(models.Model):
    _name = 'dynamic.flow.line'
    _description = 'Dynamic Flow Line'
    _order = 'sequence, id'
    _rec_name = 'stage_id'

    def _get_default_sequence(self):
        return self.env['ir.sequence'].next_by_code('dynamic.flow.line') or 1

    # name = fields.Char(string='Name', size=128)
    name = fields.Char(related='stage_id.name')
    stage_id = fields.Many2one('dynamic.flow.line.stage', string='Төлөв')
    flow_id = fields.Many2one('dynamic.flow', string='Dynamic Flow', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', required=True, default=_get_default_sequence)
    state_type = fields.Selection([
        ('draft','Draft'),
        ('sent','Sent'),
        ('done','Done'),
        ('cancel','Cancel'),
        ('invoice','Invoice'),
        ('master','Master'),
        ('parts_user','Parts user'),
        ('senior','Senior'),
        ('engineer','Engineer'),
        ('chief','Chief'),
    ], string='State type')
    amount_price_min = fields.Float(string='Мөнгөн дүнгээс бага', default=0)
    amount_price_max = fields.Float(string='Мөнгөн дүнгээс их', default=0)
    is_not_edit = fields.Boolean(string='Is Not Edit', default=False)
    type = fields.Selection([('fixed','Fixed'),('group','Group'),('user','User'),('all','All'),('none','None')], string='Type', required=True, default='group')
    user_id = fields.Many2one('res.users', string='User')
    user_ids = fields.Many2many('res.users', 'dynamic_flow_line_res_users_rel', 'flow_id', 'user_id', string='Хэрэглэгчид')
    group_id = fields.Many2one('res.groups', string='Group')
    is_print = fields.Boolean(string='Is Print', default=False)
    is_mail = fields.Boolean(string='Is Mail', default=False)
    check_type = fields.Selection([('department','Хэлтэсийн менежер'),('branch','Салбар менежер'),('manager','Тухайн хүний менежер')], string='Шалгах төрөл')

    flow_line_next_id = fields.Many2one('dynamic.flow.line', 'Дараагийн төлөв', compute='_compute_flow_line_id')
    flow_line_back_id = fields.Many2one('dynamic.flow.line', 'Өмнөх төлөв', compute='_compute_flow_line_id')


    @api.depends('sequence','flow_id','state_type')
    def _compute_flow_line_id(self):
        for item in self:
            item.flow_line_next_id = item._get_next_flow_line()
            item.flow_line_back_id = item._get_back_flow_line()


    def _get_flow_users(self, branch_id=False, department_id=False, user_id=False):
        ret_users = False
        print ('self.type ',self.type)
        print ('user_id ',user_id)
        if self.type in ['fixed','user']:
            ret_users = self.user_ids
        elif self.type=='group':
            ret_users = self.group_id.users
        elif self.type=='all':
            ret_users = self.user_ids + self.group_id.users

        if ret_users and self.check_type:
            if self.check_type=='department':
                if not department_id:
                    raise ValidationError(u'%s Урсгалд Хэлтэс явуулаагүй байна %s %s %s'%(self.name,branch_id, department_id, user_id))
                if not ret_users.filtered(lambda r: r.id == department_id.manager_id.user_id.id):
                    raise ValidationError(u'"%s" төлөвийн Хэлтэсийн менежер сонгогдоогүй байна'%(self.name))
                return ret_users.filtered(lambda r: r.id == department_id.manager_id.user_id.id)
            elif self.check_type=='branch':
                if not branch_id:
                    raise ValidationError(u'%s Урсгалд Салбар явуулаагүй байна'%(self.name))
                return ret_users.filtered(lambda r: r.id == branch_id.user_id.id )
            elif self.check_type=='manager':
                if self.env.user.id in ret_users.ids:
                    return self.env.user
                if not user_id:
                    raise ValidationError(u'%s Урсгалд Хэрэглэгч явуулаагүй байна'%(self.name))
                if not ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids):
                    raise ValidationError(u'"%s" төлөвийн %s Хэрэглэгч дээр менежер сонгогдоогүй байна'%(self.name,user_id.name))
                return ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
        return ret_users

    def _get_check_ok_flow(self, branch_id=False, department_id=False, user_id=False):
        if self.type=='none':
            return True
        check_users = self._get_flow_users(branch_id, department_id, user_id)
        if check_users:
            if self.env.user.id in check_users.ids:
                return True
        # if self.type=='fixed' and check_users:
        #     if self.env.user.id in check_users.ids:
        #         return True
        # if self.type=='group' and check_users:
        #     if self.env.user.id in self.group_id.users.ids:
        #         return True
        # if self.type=='all' and check_users:
        #     if self.env.user.id in self.user_ids.ids or self.env.user.id in self.group_id.users.ids:
        #         return True
        # if self.type=='none':
        #     return True
        return False


    def _get_next_flow_line(self):
        if self.id:
            next_flow_line_id = self.env['dynamic.flow.line'].search([
                ('flow_id','=',self.flow_id.id),
                ('id','!=',self.id),
                ('sequence','>',self.sequence),
                ('state_type','not in',['cancel']),
                ], limit=1)
            return next_flow_line_id
        else:
            return False

    def _get_back_flow_line(self):
        if self.id:
            back_flow_line_id = self.env['dynamic.flow.line'].search([
                ('flow_id','=',self.flow_id.id),
                ('id','!=',self.id),
                ('sequence','<',self.sequence),
                ('state_type','not in',['cancel']),
                ], limit=1, order="sequence desc")
            return back_flow_line_id
        return False

    def _get_cancel_flow_line(self):
        flow_line_id = self.env['dynamic.flow.line'].search([
            ('flow_id','=',self.flow_id.id),
            ('id','!=',self.id),
            ('state_type','=','cancel'),
            ], limit=1)
        return flow_line_id

    def _get_draft_flow_line(self):
        flow_line_id = self.env['dynamic.flow.line'].search([
            ('flow_id','=',self.flow_id.id),
            ('id','!=',self.id),
            ('state_type','=','draft'),
            ], limit=1)
        return flow_line_id

    def _get_done_flow_line(self):
        flow_line_id = self.env['dynamic.flow.line'].search([
            ('flow_id','=',self.flow_id.id),
            ('id','!=',self.id),
            ('state_type','=','done'),
            ], limit=1)
        return flow_line_id


    def send_chat(self, html, partner_ids, with_mail=False, subject_mail=False):
        if not partner_ids:
            if self.type=='none':
                return True
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')

        channel_obj = self.env['mail.channel']
        if self.flow_line_next_id and not with_mail:
            with_mail = self.flow_line_next_id.is_mail
            subject_mail = (str(self.flow_id.model_id.name) or '')+':'+(self.name or '')
        self.env['res.users'].send_chat(html, partner_ids, with_mail, subject_mail)

class DynamicFlowLineStage(models.Model):
    _name = 'dynamic.flow.line.stage'
    _description = 'Dynamic Flow Line Stage'
    _order = 'name'

    name = fields.Char('Нэр', required=True)

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!')
    ]
