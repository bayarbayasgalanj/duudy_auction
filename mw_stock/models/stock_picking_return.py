from odoo import api, fields, models, _

class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    
    def _create_returns(self):
        new_picking_id, pick_type_id = super(ReturnPicking,self)._create_returns()
        for item in self.picking_id.move_lines:
            if item.product_id.tracking!='none':
                for new_move in self.env['stock.picking'].browse(new_picking_id).move_lines:
                    new_move_line_id = new_move.move_line_ids.filtered(lambda r: not r.lot_id and r.product_id.id==item.product_id.id)
                    if new_move_line_id:
                        new_move_line_id = new_move_line_id[0]
                        lot_ids = new_move.move_line_ids.mapped('lot_id').ids
                        old_move_line_id = item.move_line_ids.filtered(lambda r: r.lot_id not in lot_ids and r.product_id.id==item.product_id.id)
                        if old_move_line_id:
                            old_move_line_id = old_move_line_id[0]
                        new_move_line_id.lot_id = old_move_line_id.lot_id.id
                        break;
                    # qty_save = 
        return new_picking_id, pick_type_id 
