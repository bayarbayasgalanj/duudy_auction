# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class ResUsers(models.Model):
    _inherit = 'res.users'
    _description = 'Res users'

    # Columns
    warehouse_ids = fields.Many2many('stock.warehouse','user_warehouses_rel','user_id','warehouse_id',
        string='Warehouse',
    )
    warehouse_id = fields.Many2one('stock.warehouse',
        string='Warehouse',
    )
    department_ids = fields.Many2many('hr.department', 'user_department_rel', 'user_id', 'department_id', 'Departments')

class HrDepartment(models.Model):
    _inherit = 'hr.department'
    user_ids = fields.Many2many('res.users', 'user_department_rel', 'department_id', 'user_id', 'Users')

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'
    _description = 'Stock warehouse'

    # Columns
    access_user_ids = fields.Many2many('res.users','user_warehouses_rel','warehouse_id','user_id',
        string='Access users',)
