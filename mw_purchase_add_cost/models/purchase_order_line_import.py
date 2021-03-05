# -*- coding: utf-8 -*-
from odoo import api, fields, models
from io import BytesIO
import base64
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError

class PurchaseOrderLineImport(models.TransientModel):
    _name = 'purchase.order.line.import'
    _description = 'Purchase order line import'

    purchase_id = fields.Many2one('purchase.order', 'Purchase order')
    import_data = fields.Binary('Import excel file', copy=False, required=True)

    def action_import_line(self):
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodestring(self.import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
        book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise UserError(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
        nrows = sheet.nrows
        
        rowi = 2
        data = []
        r=0
        line_obj = self.env['purchase.order.line']
        for item in range(0,nrows):
            row = sheet.row(item)
            barcode = str(row[0].value)
            product_qty = row[1].value
            price_unit = row[2].value
            # barcode = str(int(barcode))
            product_id = self.env['product.product'].search([('barcode','=',barcode)], limit=1)
            if product_id:
                line_obj.create({
                    'order_id': self.purchase_id.id,
                    'name': product_id.name_get()[0][1],
                    'product_id': product_id.id,
                    'product_uom': product_id.uom_po_id.id,
                    'product_qty': product_qty,
                    'price_unit': price_unit,
                    'date_planned': self.purchase_id.date_order
                })
            elif barcode:
            	raise UserError(barcode+' Barcode product not found')
            	# print barcode, product_qty
            