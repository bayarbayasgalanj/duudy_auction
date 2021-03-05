# -*- coding: utf-8 -*-
##############################################################################
#
#    ManageWall, Enterprise Management Solution    
#    Copyright (C) 2007-2014 ManageWall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#
#    Email : daramaa26@gmail.com
#    Phone : 976 + 99081691
#
##############################################################################


# from openerp.osv import fields, osv

import time
# _logger = logging.getLogger('usi.generic.report')
from odoo import api, fields, models, _
from xlwt import easyxf

class ReportEsxelOutput(models.TransientModel):
    _name = 'report.excel.output'
    _description = "Excel Report Output"
    
    name = fields.Char('Filename', readonly=True)
    data = fields.Binary('File', readonly=True, required=True)
    date = fields.Datetime(default=fields.Datetime.now)


class Abstract_Report_Excel(models.TransientModel):
    _name = 'abstract.report.excel'
    _description = 'Abstract Report Excel'
    
    save=fields.Boolean('Save to document storage')
    
    def get_easyxf_styles(self):
        styledict = {
            'title_xf': easyxf('font: name Times New Roman, bold on, height 250; align: wrap off, vert centre, horiz left;'),
            'small_title_xf': easyxf('font: name Times New Roman, bold on, height 190; align: wrap off, vert centre, horiz left;'),
            'too': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center,rota 90; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue'),
            'heading_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue', num_format_str='#,##0.00'),
            'heading_xf_right': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue', num_format_str='#,##0.00'),
            'heading_xf-1': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin , top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour light_turquoise', num_format_str='#,##0.00'),
            'heading_xf-1_right': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin , top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour light_turquoise', num_format_str='#,##0.00'),
            'heading_white_xf': easyxf('font: name Times New Roman, bold on, height 180; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50'),
            'heading_grey_text_center_bold_xf': easyxf('font: name Times New Roman, bold on, height 180; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gray25'),
            'text_xf': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'text_xf_wrap_off': easyxf('font: name Times New Roman, bold on, height 160; align: wrap off, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'text_xf_grey': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;pattern: pattern solid, fore_color gray25'),
            'text_right_xf': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'text_bold_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'text_bold_xf_no_wrap': easyxf('font: name Times New Roman, bold on, height 160; align: wrap off, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'text_bold_right_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; '),
            'text_center_bold_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50 ;'),
            'text_center_xf': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'text_center_xf_gray': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'number_xf': easyxf('font: name Times New Roman, height 160; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00'),
            'number_xf_grey': easyxf('font: name Times New Roman, height 160; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color gray25', num_format_str='#,##0.00'),
            'number_bold_xf': easyxf('font: name Times New Roman, height 160, bold on; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00'),
            'grey_text_bold_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gray25'),
            'grey_text_bold_right_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin , top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour light_turquoise'),
            'grey_text_center_bold_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gray25'),
            'grey_number_bold_xf': easyxf('font: name Times New Roman, height 160, bold on; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin , top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour light_turquoise', num_format_str='#,##0.00'),
            'gold_text_bold_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gold'),
            'gold_text_bold_right_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gold'),
            'gold_text_center_bold_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gold'),
            'gold_number_bold_xf': easyxf('font: name Times New Roman, height 160, bold on; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_color pale_blue', num_format_str='#,##0.00'),
            'number_boldtotal_xf': easyxf('font: name Times New Roman, height 160, bold on; align: wrap on, vert centre, horiz right; borders: top thin, left thin, bottom thin, right thin , top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50 ;pattern: pattern solid, fore_colour pale_blue ', num_format_str='#,##0.00'),
            'number_xf_no_precision': easyxf('font: name Times New Roman, height 160; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;;', num_format_str='#,##0'),
            'number_bold_xf_no_precision': easyxf('font: name Times New Roman, height 160, bold on; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0'),
            'grey_number_text_bold_xf': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz left; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gray25', num_format_str='#,##0.00'),

            'grey_number_bold_xf1': easyxf('font: name Times New Roman, height 160, bold on; align: vert centre, horz right; borders: top thin, left thin, bottom thin, right thin , top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gray25', num_format_str='#,##0.00'),
            'heading_xf-grey': easyxf('font: name Times New Roman, bold on, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin , top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50; pattern: pattern solid, fore_colour gray25', num_format_str='#,##0.00'),

            'asset_name_bold_xf': easyxf('font: name Times New Roman, height 160, bold on; align: wrap on, vert centre, horz left; borders: top thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00'),
            'asset_code_bold_xf': easyxf('font: name Times New Roman, height 160, bold on; align: wrap on, vert centre, horz left; borders: bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='#,##0.00'),
            'asset_name_center_xf': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'asset_code_center_xf': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz center; borders: left thin, bottom thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;'),
            'date_center_xf': easyxf('font: name Times New Roman, bold off, height 160; align: wrap on, vert centre, horiz center; borders: top thin, left thin, bottom thin, right thin, top_colour gray50,bottom_colour gray50,left_colour gray50,right_colour gray50;', num_format_str='YYYY-MM-DD'),
        
        }
        return styledict
    
    def get_log_message(self, cr, uid, ids, context=None):
        return u"Unimplemented log"
    
    def force_make_attachment(self, cr, uid, datas, directory_name, 
            attache_name, context=None):
        ''' Excel тайланг шууд баримтын серверт хадгална.
        '''
        if context is None:
            context = {}
        if attache_name:
            aname = "%s_%s.xls" % (attache_name, time.strftime('%Y%m%d_%H%M'))
        else :
            aname = '%s_%s.xls' % (self._name.replace('.','_'), time.strftime('%Y%m%d%H%M%S'))
        directory = False
        if directory_name:
            directory_ids = self.pool.get('document.directory').search(cr, 1, 
                        [('name','=',directory_name)], context=context)
            if directory_ids :
                directory = directory_ids[0]
        try:
            model_name = self._name
            res_id = False
            if 'generator_id' in context:
                model_name = 'report.schedule.generator'
                res_id = context['generator_id']
            document_name = context.get('force_document_name', context.get('attache_name', aname))
            self.pool.get('ir.attachment').create(cr, uid, {
                'name': document_name+' [%s]' % time.strftime('%Y%m%d%H%M%S'),
                'datas': datas,
                'datas_fname': aname,
                'res_model': model_name,
                'res_id': res_id,
                'parent_id': directory
                }, context=context)
            if context.get('other_users',[]):
                for uid2 in context['other_users']:
                    self.pool.get('ir.attachment').create(cr, uid2, {
                        'name': document_name+' [%s]' % time.strftime('%Y%m%d%H%M%S'),
                        'datas': datas,
                        'datas_fname': aname,
                        'res_model': model_name,
                        'res_id': res_id,
                        'parent_id': directory
                    }, context=context)
        except Exception:
            #TODO: should probably raise a proper osv_except instead, shouldn't we? see LP bug #325632
            logging.getLogger('report').error('Could not create saved report attachment', exc_info=True)
        return aname
    
    def print_report(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        data = self.prepare_data(cr, uid, ids, context=context)
        
        body = self.get_log_message(cr, uid, ids, context=context)
        message = u"[Тайлан][PDF][PROCESSING] %s" % body
        context.update({'report_log':True})
        log_id = self.log(cr, uid, ids[0], message, context=context)
        data['log_body'] = body
        data['log_id'] = log_id
        data['log_start'] = time.strftime('%Y-%m-%d %H:%M:%S')
        _logger.debug(message)
        
        return {
            'type': 'ir.actions.report.xml',
            'report_name': data['report_name'],
            'datas': data,
            'context': context
        }
    
    def export_report(self):
        if context is None:
            context = {}
        body = self.get_log_message()
        if 'generator_id' in context:
            message = u"[Автомат тайлан][XLS][PROCESSING] %s" % body
            prefix = u"[Автомат тайлан][XLS][PROCESSING]"
        else :
            message = u"[Тайлан][XLS][PROCESSING] %s" % body
            prefix = u"[Тайлан][XLS][PROCESSING]"
        # _logger.debug(message)
        context.update({'report_log':True})
        # log_id = self.log(cr, uid, ids[0], message, context=context)
        
        d1 = datetime.datetime.now()
        res = self.get_export_data()
        
        book = res['data'] # Workbook object instance.
        buffer = StringIO()
        book.save(buffer)
        buffer.seek(0)
        
        out = base64.encodestring(buffer.getvalue())
        buffer.close()
        
        # Force save if needed.
        if res.get('force_save', False) == True and res.get('directory_name', False):
            context.update({'force_document_name': body[:128]})
            filename = self.force_make_attachment(cr, uid, out, res['directory_name'], 
                        res.get('attache_name',False), context=context)
        else :
            filename = self._name.replace('.', '_')
            filename = "%s_%s.xls" % (filename, time.strftime('%Y%m%d_%H%M'),)
            if 'xlsx' in res:
                filename += 'x' # Office 2007
        
        excel_id = self.env['report.excel.output'].create({
                                'data':out,
                                'name':filename
        })
        
        mod_obj = self.env['ir.model.data']
        form_res = mod_obj.get_object_reference('mw_base', 'action_excel_output_view')
        form_id = form_res and form_res[1] or False
        
        dta = datetime.datetime.now() - d1
        if dta.seconds > 60 :
            tm = '%sm %ss' %(dta.seconds / 60, dta.seconds % 60)
        else :
            tm = '%ss' % dta.seconds
        if 'generator_id' in context:
            prefix = u"[Автомат тайлан][XLS][COMPLETE (%s)]" % (tm,)
        else :
            prefix = u"[Тайлан][XLS][COMPLETE (%s)]" % (tm,)
        message = u"%s %s" % (prefix, body)
        #self.pool.get('res.log').write(cr, uid, [log_id], {'name': message,'create_date':time.strftime('%Y-%m-%d %H:%M:%S')})
        _logger.debug(message)
        
        
        return {
            'name': _('Export Result'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'res_id': excel_id,
            'view_id': False,
            'views': [(form_id, 'form')],
            'context': context,
            'type': 'ir.actions.act_window',
            'target':'new',
            'nodestroy': True,
        }
    
    def get_export_data():
        raise osv.except_osv(_('Programming Error!'), _('Unimplemented method.'))
