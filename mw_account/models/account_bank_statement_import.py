# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64
import xlrd
from tempfile import NamedTemporaryFile
from datetime import datetime

class AccountBankStatementImportFile(models.TransientModel):
    _name = 'account.bank.statement.import.file'
    _description = "Import File"

    type = fields.Selection([('default','Энгийн'),
                             ('golomt','Голомт'),
                             ('tdb','ХХБ'),
                             ('xac','ХАС'),
                             ('khaan','ХААН'),
                             ('tur','ТӨР'),
                             ('capitron','Капитрон'),
                             ('arig','Ариг'),
                             ('uhob','ҮХОБ'),
                             ('teever','Тээвэр'),
                             ('credit','Кредит'),
                             ],'TYPE',default='default')
    data_file = fields.Binary(string='Bank Statement File', required=True, help='Get you bank statements in electronic format from your bank and select them here.')


    desc = fields.Text('Template', default="""# A Огноо 2020-02-10 загвартай байна
# B Гүйлгээний утга
# C харилцагчийн ERP нэр
# D Дүн Орлого + Зарлага бол -
# E Дансны код 
# F Мөнгөн гүйлгээний төрлийн нэр
# G Салбарын нэр ERP дээрх
# H Банкны данс
# I Шинжилгээний данс нэр""", readonly=True)
    
    
    def import_file(self):
        context = self._context
        statement=None
        if context.get('active_model') == 'account.bank.statement' and context.get('active_ids'):
            statement = self.env['account.bank.statement'].browse(context['active_ids'])[0]
        if not statement:
            raise UserError(_("No active statement!"))
            
            
        try:
            fileobj = NamedTemporaryFile('w+b')
            fileobj.write(base64.decodestring(self.data_file))
            fileobj.seek(0)
            book = xlrd.open_workbook(fileobj.name)
        except ValueError:
            raise UserError(
                _('Error loading data file. \ Please try again!'))
        
        start_sequence = 1
        last_statment_line = self.env['account.bank.statement.line'].search([('statement_id', '=', statement.id)], order='sequence desc', limit=1)
        if last_statment_line:
            start_sequence = last_statment_line.sequence+1

        sheet = book.sheet_by_index(0)
        nrows = sheet.nrows
        rowi = 1
        while rowi < nrows:
            partner_id = False
            cashflow_id = False
            account_id=False
            branch_id=False
            amount = 0.0
            row = sheet.row(rowi)
            print ('row[0].value ',row[0].value)
            dd=row[0].value
            try:
                if type(dd)==float:
                    serial = dd
                    seconds = (serial - 25569) * 86400.0
                    date=datetime.utcfromtimestamp(seconds)
                    print ('date ',date)
                else:
                    date = datetime.strptime(dd, '%Y-%m-%d')
            except ValueError:
                raise ValidationError(_('Date error %s row! \n \
                format must \'YYYY-mm-dd\'' % rowi))
                
            name = row[1].value
            try:
                partner_name = row[2].value
            except Exception:
                partner_name=''
            db_amount = row[3].value
            try:
                str_account_code =   row[4].value
            except Exception:
                str_account_code=''
            try:
                cashflow_type_name = row[5].value
            except Exception:
                cashflow_type_name=''

            try:
                branch_name = row[6].value
            except Exception:
                branch_name=''
                
            try:
                str_account_bank =   row[7].value
            except Exception:
                str_account_bank=''
                
#             if db_amount and cr_amount:
#                 raise ValidationError(_('Data error %s row! \n \
#                     Only one of Income and Expense columns \
#                     must have a value' % rowi))

            if type(str_account_code) in [float]:
                account_code = str(str_account_code).strip().split('.')[0]
            elif type(str_account_code) in [int]:
                account_code = str(str_account_code).strip()
            else:
                account_code = str_account_code.strip()
                
                
            if type(str_account_bank) in [float]:
                account_bank = str(str_account_bank).strip().split('.')[0]
            elif type(str_account_bank) in [int]:
                account_bank = str(str_account_bank).strip()
            else:
                account_bank = str_account_bank.strip()                
            try:
                analytic_name = row[8].value
            except Exception:
                analytic_name=''
            
#             if db_amount:
            amount = db_amount
#             if cr_amount:
#                 amount = -cr_amount
            print ('account_code ',account_code)
            partner = self.env['res.partner'].search([('name', '=', partner_name)], limit=1)
            if partner:
                partner_id = partner.id

            branch = self.env['res.branch'].search([('name', '=', branch_name)], limit=1)
            if branch:
                branch_id = branch.id

            account = self.env['account.account'].search([('code', '=', account_code)], limit=1)
            if account:
                account_id = account.id

            bank_account_id = False
            bank_account = self.env['res.partner.bank'].search([('acc_number', '=', account_bank)], limit=1)
            if bank_account:
                bank_account_id = bank_account.id


            if cashflow_type_name:
                cashflow = self.env['account.cash.move.type'].search([('name', '=', cashflow_type_name)], limit=1)
                if not cashflow:
                    raise UserError(_("No cashflow found matching '%s'.") % cashflow_type_name)
                cashflow_id = cashflow.id
            if not bank_account_id:
                partner_bank = self.env['res.partner.bank'].search([('partner_id', '=', partner_id)], limit=1)
                if partner_bank:
                    bank_account_id = partner_bank.id
            if name:
                if isinstance(name, float) or isinstance(name, int):
                    name=str(int(name))
            analytic_id=False
            if analytic_name:
                analytic = self.env['account.analytic.account'].search([('name', '=', analytic_name)], limit=1)
                if not analytic:
                    raise UserError(_("No analytic account matching '%s'.") % analytic_name)
                analytic_id = analytic.id
            
            self.env['account.bank.statement.line'].create({
                    'name': name or '/',
                    'amount': amount,
                    'partner_id': partner_id,
                    'statement_id': statement.id,
                    'date': date,
#                     'currency_id': statement.currency_id.id if statement.currency_id else False,
                    'cash_type_id': cashflow_id,
                    'sequence':start_sequence,
                    'bank_account_id':bank_account_id,
                    'account_id':account_id,
                    'branch_res_id':branch_id,
                    'analytic_account_id':analytic_id
                })
            rowi += 1
            start_sequence += 1
#         statement.onchange_balance_end()
        return True

class account_statement_import_invoice(models.TransientModel):
    """ Generate Entries by Account Bank Statement from Invoices """
    _name = "account.bank.statement.import.invoice"
    _description = "Import Invoice"

    account_invoices = fields.Many2many(
        'account.move', 'account_invoice_relation', 'invoice_id', 'invoice_line', 'Invoices')

    def populate_invoice(self):
        context = dict(self._context or {})
        statement_id = context.get('statement_id', False)
        if not statement_id:
            return {'type': 'ir.actions.act_window_close'}
        account_invoices = self.account_invoices
        if not account_invoices:
            return {'type': 'ir.actions.act_window_close'}

        statement_line_obj = self.env['account.bank.statement.line']
        move_line_obj = self.env['account.move.line']

        statement = self.env['account.bank.statement'].browse(statement_id)
        # for each selected move lines
        for line in self.account_invoices:
            bank_account_id = False
            ctx = context.copy()
            ctx['date'] = statement.date
            amount = 0.0
            count = 0
            reconcile = self.env['account.move.line.reconcile.writeoff'].search(
                [('writeoff_acc_id', '=', line.account_id.id)])
            move_line_id = move_line_obj.search(
                [('account_id', '=', line.account_id.id), ('invoice_id', '=', line.id)])  # , ('reconcile','=',False)
            if move_line_id:
                move_line = move_line_obj.browse(move_line_id.id)
                if line.type == 'out_refund' or line.type == 'in_invoice':
                    amount = -line.residual
                elif line.type == 'in_refund' or line.type == 'out_invoice':
                    amount = line.residual
                
                partner_bank = self.env['res.partner.bank'].search([('partner_id', '=', move_line.partner_id.id)], limit=1)
                if partner_bank:
                    bank_account_id = partner_bank.id
                    
                statement_line_obj.create({
                    'name': move_line.name or ' ?',
                    'amount': amount,
                    'partner_id': move_line.partner_id.id,
                    'bank_account_id': bank_account_id,
                    'statement_id': statement_id,
                    'ref': move_line.ref,
                    'date': statement.date,
                    'amount_currency': move_line.amount_currency,
                    'currency_id': move_line.currency_id.id,
                    'import_line_id': move_line.id,
                    'account_id': line.account_id.id,
                    'cashflow_id': False
                })
#         statement.onchange_balance_end()
        return {'type': 'ir.actions.act_window_close'}
