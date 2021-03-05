# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError,ValidationError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)

class StockMoveLock(models.Model):
    _name = "stock.move.lock"
    _description = "Stock move lock"
    
    date_start = fields.Date('Эхлэх Огноо', required=True)
    date_end = fields.Date('Дуусгах Огноо', required=True)
    warehouse_ids = fields.Many2many('stock.warehouse', 'stock_move_lock_stock_warehouse_rel', 'lock_id', 'wh_id', 'Цоожлох агуулахууд', required=True)

    _order = 'date_start desc'

    @api.constrains('date_start', 'date_end', 'warehouse_ids')
    def _validate_range(self):
        for this in self:
            whs = this.warehouse_ids
            if len(whs) > 1:
                w_ids = str(tuple(whs.ids))
            else:
                w_ids = "("+str(whs[0].id)+")"

            SQL = """
                SELECT
                    sml.id
                FROM
                   stock_move_lock sml
                   left join stock_move_lock_stock_warehouse_rel r on (r.lock_id=sml.id)
                WHERE
                    DATERANGE(sml.date_start, sml.date_end, '[]') &&
                        DATERANGE('%s'::date, '%s'::date, '[]')
                    AND sml.id != %s
                    AND r.wh_id in %s
                    """% (this.date_start,
                                      this.date_end,
                                      this.id,
                                      w_ids
                                      )
            self.env.cr.execute(SQL)
            res = self.env.cr.fetchall()
            if res:
                dt = self.browse(res[0][0])
                raise ValidationError(
                    (u"%s %s хугацааны хооронд Агуулах давхцаж байна") % (this.date_start, this.date_end))
            
    def get_stock_move_is_lock(self, stock_move_id):
        lock_obj = self.env['stock.move.lock']
        check_wh_ids = []
        if stock_move_id.location_id.usage=='internal' and stock_move_id.location_dest_id.usage=='internal':
            check_wh_ids.append(stock_move_id.location_id.set_warehouse_id.id)
            check_wh_ids.append(stock_move_id.location_dest_id.set_warehouse_id.id)
        elif stock_move_id.location_id.usage=='internal':
            check_wh_ids.append(stock_move_id.location_id.set_warehouse_id.id)
        elif stock_move_id.location_dest_id.usage=='internal':
            check_wh_ids.append(stock_move_id.location_dest_id.set_warehouse_id.id)
            
        check_datetime = stock_move_id.date + timedelta(hours=8)
        check_date = check_datetime.strftime( "%Y-%m-%d")
        lock_id = lock_obj.sudo().search([('date_start','<=',check_date), ('date_end','>=',check_date),('warehouse_ids','in',check_wh_ids)])
        # print blblb
        if lock_id:
            return True,check_wh_ids
        return False,False

class StockMove(models.Model):
    _inherit = 'stock.move'

    
    def unlink(self):
        self._update_check_move_lock()
        return super(StockMove, self).unlink()

    
    def write(self, vals):
        if any(key in vals for key in ('location_id', 'date', 'date_expected', 'location_dest_id', 'product_uom_qty', 'price_unit', 'state')):
            self._update_check_move_lock()
        return super(StockMove, self).write(vals)

    
    def _update_check_move_lock(self):
        """ Raise Warning to cause rollback if the move is posted, some entries are reconciled or the move is older than the lock date"""
        lock_obj = self.env['stock.move.lock']
        # print blblb
        for line in self:
            err_msg = u'Агуулахын хөдөлгөөн (id): %s (%s)' % (line.name, str(line.id))
            if line.state == 'done':
                lock_id = lock_obj.sudo().get_stock_move_is_lock(line)
                check_datetime = line.date + timedelta(hours=8)
                if lock_id[0]:
                    wh_names = ', '.join(self.env['stock.warehouse'].browse(lock_id[1]).mapped('name'))
                    raise UserError((u'%s Агуулах\n%sОгноонд Хөдөлгөөн цоожтой байна.\n%s.')% (wh_names,line.date,err_msg))
        return True



