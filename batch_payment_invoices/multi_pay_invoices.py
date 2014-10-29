from openerp.osv import osv,fields
import time
from openerp import netsvc
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

class account_invoice(osv.Model):
    _inherit = 'account.invoice'

    _columns = {
                'amount_paid': fields.float('Amount paid'),
                'check_log_ref': fields.char("Check-log Reference",size=128),
                'payment_method': fields.selection([('on_due_date', 'On Due Date'), ('before_due_date', 'Before Due Date')],'Payment Method'),
                'end_balance':fields.float('Payment Account Ending Balance', readonly=1),
                'apply_credit':fields.boolean('Apply Credits'),
                'term_discount':fields.boolean('Apply Terms Discounts'),
                'payment_date':fields.datetime('Payment Date'),
                'pay': fields.boolean('Pay'),
                'print_check': fields.boolean('Print'),
                'credit_available':fields.float(string='Credit Available'),
                'use_credit_available':fields.float(string='Use Credit Available'),
                'use_credit_available_dummy':fields.float(string='Dummy Credit Available'),
                'voucher_id':fields.many2one('account.voucher', 'Voucher'),
                'dummy_id':fields.many2one('account.multi.pay.invoice', 'Dummy'),
#                'multi_pay_id':fields.many2many('account.multi.pay.invoice', 'multi_pay_invoice_rel', 'invoice_id','multi_invoice_id', 'Multi-pay ID'),
                'state_for_readonly' : fields.related("dummy_id", "state", type="char", string="Dummy State"),
    }

    _defaults = {
        'amount_paid': 0.0,
        'payment_date': lambda *args: time.strftime('%Y-%m-%d %H:%M:%S'),
        'pay':False,
        'print_check':False,
    }

    def onchange_credit(self, cr, uid, ids, total_balance, credit , context=None):
        result = {'amount_paid' : self.cal_amount_paid(total_balance,credit)}
        return {}

    def cal_amount_paid(self, total_balance, credit ):
        if credit:
            total = total_balance - credit
        else:
            total = total_balance
        return total

    def pay_print_button(self, cr, uid, ids, context=None):
        vals = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.type == 'in_invoice':
                if not inv.pay and not inv.print_check:
                    vals = {'pay': True, 'print_check':True, 'amount_paid':inv.residual or 0.0}
                elif inv.pay and not inv.print_check:
                    vals = {'pay': True, 'print_check':True , 'amount_paid':inv.residual or 0.0}
                elif inv.pay and inv.print_check:
                    vals = {'pay': False, 'print_check':False, 'amount_paid':0.0}
                elif not inv.pay and  inv.print_check:
                    vals = {'pay': False, 'print_check':True,'amount_paid':0.0}
            else:
                if not inv.pay:
                    vals = {'pay': True, 'amount_paid':inv.residual or 0.0 ,'use_credit_available': inv.use_credit_available_dummy}
                elif inv.pay:
                    vals = {'pay': False, 'amount_paid':0.0, 'use_credit_available': 0.0,'use_credit_available_dummy' :inv.use_credit_available}
        return self.write(cr, uid, ids, vals)

#    def cal_end_balance(self, cr, uid, ids, context=None):
#        multi_pay = self.pool.get('account.multi.pay.invoice')
#        total = 0.0
#        for invoice in self.read(cr, uid, ids, context=context):
#            multi = invoice.multi_pay_id
#            if multi:   
#                invoice_ids = multi_pay.read(cr,uid,multi,['invoice_ids'], context=context)
#                for invoice in invoice_ids:
#                    if invoice.pay:
#                        total = total + invoice.amount_paid or 0.0
#            if multi.multi_pay_id.payment_journal.default_debit_account_id or multi.multi_pay_id.payment_journal.default_debit_account_id.balance == 0.0:
#                total = (multi.payment_journal.multi_pay_id.default_debit_account_id.balance) - total 
#        return self.write(cr, uid, ids, {'end_balance':total}, context=context)

class account_multi_pay_invoice(osv.Model):
    _name = 'account.multi.pay.invoice'

    def _state_get(self, cr, uid, ids, field_name, arg=None, context=None):
        result = {}
        counter = 0
        inv_obj = self.pool.get('account.invoice')
        for r in self.read(cr, uid, ids,['invoice_ids']):
            no_of_invoice = len(r.get('invoice_ids', []))
            for inv_state in inv_obj.browse(cr, uid,r.get('invoice_ids',[]), context=context ):
                if inv_state.state == 'paid':
                    counter = counter +1
            if counter < no_of_invoice:
                result[r['id']] = 'Open'
            elif no_of_invoice == 0:
                result[r['id']] = 'Open'
            else: 
                result[r['id']] = 'Paid'
        return result

    _columns = {
                'amount_due_by': fields.date('Amount Due By', required=1),
                'payment_method': fields.selection([('on_due_date', 'On Due Date'), ('before_due_date', 'Before Due Date')],'Payment Due'),
                'end_balance':fields.float('Ending Balance', readonly=1),
                'apply_credit':fields.boolean('Apply Credits'),
                'term_discount':fields.boolean('Apply Terms Discounts'),
                'payment_date':fields.date('Payment Date'),
                'invoice_ids': fields.many2many('account.invoice', 'multi_pay_invoice_rel', 'multi_invoice_id', 'invoice_id', 'Created Invoices'),
                'pay':fields.boolean('Pay'),
                'inv_type': fields.selection([('in', 'In Invoice'),('out', 'Out Invoice')], 'Invoice Type'),
                'print': fields.boolean('Print'),
                'payment_journal': fields.many2one('account.journal', string='Payment Method', domain=[('type', 'in', ['bank', 'cash'])],required=True),
                'state': fields.selection([
                                           ('new', 'Create Batch'),
                                           ('draft', 'Draft'),
                                           ('posted','Payments Created'),
                                           ('printed','Checks Printed'),
                                           ('cancel', 'Cancelled'),
                                           ]
                                          , 'Status', readonly=True, track_visibility='onchange',)
                }

    _defaults = {
        'payment_date': lambda *args: time.strftime('%Y-%m-%d %H:%M:%S'),
        'state':'new',
        'payment_method': 'on_due_date',
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
                                        context=None, count=False):
        return super(account_multi_pay_invoice, self).search(cr, uid, args, offset=0, limit=limit, order='payment_date desc',
                                        context=context, count=count)

    def cal_end_balance(self, cr, uid, ids, context=None):
        account_invoice = self.pool.get('account.invoice')
        total = 0.0
        for multi in self.browse(cr, uid, ids, context=context):
            if multi.invoice_ids:
                for invoice in multi.invoice_ids:
                    if invoice.pay:
                        total = (total + invoice.amount_paid) or 0.0
            if multi.payment_journal.default_debit_account_id or multi.payment_journal.default_debit_account_id.balance == 0.0:
                if context.get('default_inv_type',False) == 'in':
                    total = (multi.payment_journal.default_debit_account_id.balance) - total
                else: 
                    total = (multi.payment_journal.default_debit_account_id.balance) + total
        return self.write(cr, uid, ids, {'end_balance':total}, context=context)

    def do_post_or_nothing(self, cr, uid, voucher_id, inv_type='out'):
        self.pool.get('account.voucher').button_proforma_voucher(cr, uid, [voucher_id], context= None)
        return True
    
    def pay_bills(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')
        vouchers = []
        voucher_not_print = []
        account_invoice = self.pool.get('account.invoice')
        temp_invoices_ids = []
        for multi in self.browse(cr, uid, ids, context=context):
            vouchers = []
            temp_invoices_ids = [invoice.id for invoice in multi.invoice_ids]
            if not multi.payment_method:
                raise osv.except_osv(_('Error!'),_("You need Payment Method."))
            if not multi.invoice_ids:
                raise osv.except_osv(_('Error!'),_("Please Get Invoices first."))
            inv_ids = []
            MOVE_LINES = {}
            if multi.invoice_ids:
                for invoice in multi.invoice_ids:
                    inv_ids.append(invoice.id)
                    # Check partner is contact or company
                    if invoice.partner_id.is_company:
                       partner = invoice.partner_id.id
                    else:
                       if not invoice.partner_id.parent_id:
                          partner = invoice.partner_id.id
                       else:
                          partner = invoice.partner_id.parent_id.id
                    # Linked move_lines with partner so only partner movelines consider in voucher lines
                    if partner not in MOVE_LINES.keys():
                        MOVE_LINES[partner] = []
                    MOVE_LINES[partner] += [invoice.id]
            cr.execute("SELECT partner_id,id FROM account_invoice s  \
                                WHERE s.id in %s AND s.pay=True\
                                order by partner_id\
                                    ",(tuple(inv_ids),))
            inv_ids = cr.fetchall()
            inv_ids_dict = dict(inv_ids)
            inv_ids_list = inv_ids_dict.values()
            if multi.invoice_ids:
                MOVE_CONN = {}
                for invoice in account_invoice.browse(cr, uid,inv_ids_list, context=context):
                    inv_part = account_invoice.search(cr, uid, [('id', 'in', temp_invoices_ids),('pay','=',True),('partner_id','=',invoice.partner_id.id),('state','=','open')])
                    amt = 0.0
                    CREDIT = 0.0
                    inv_ids = []
                    for inv in account_invoice.browse(cr, uid,inv_part, context=context):
                        # calculate total credit and total payable amount for customer/supplier
                        amt +=inv.amount_paid
                        # connection with move line and paid amount for amount correction in voucher line
                        MOVE_CONN[inv.move_id.id] = inv.amount_paid 
                        CREDIT += inv.credit_available
                        inv_ids.append(inv.id)
                    total_paid_amt = 0.0
                    if invoice.pay:
                        if invoice.state in ('open',):
                            ctx = dict(context)
                            ctx.update({'payment_expected_currency':invoice.currency_id.id})
                            partner = ''
                            if invoice.partner_id.is_company:
                                partner = invoice.partner_id.id
                            else:
                                if not invoice.partner_id.parent_id:
                                    partner = invoice.partner_id.id
                                else:
                                    partner = invoice.partner_id.parent_id.id
                            dist =  {
                                 'partner_id'   : partner,
                                 'amount'       : abs(amt-CREDIT),
                                 'journal_id'   : multi.payment_journal.id,
                                 'log_ref'      : invoice.check_log_ref or '',
                                 'origin'       : invoice.origin or '',
                            }
                            if amt < 0:
                                raise osv.except_osv(_('Error!'),_("Pay Amount should not be negative!"))
                            ttype = invoice.type in ['in_invoice', 'out_refund'] and 'payment' or 'receipt'
                            ctx.update({'inv_ids' : MOVE_LINES[partner],'batch_pay_credit':CREDIT ,'MOVE_CONN': MOVE_CONN})
                            lines = []
                            lines_cr = []
                            lines_dr = []
                            dist.update(self.pool.get('account.voucher').onchange_partner_id(cr, uid, [], partner,  multi.payment_journal.id , amt- CREDIT, invoice.currency_id.id, ttype, invoice.date_invoice, context= ctx)['value'])
#                            remain_credit_amount = 0.0
#                            if context.get('default_inv_type') == 'in':
#                                if dist['line_cr_ids'] != []:
#                                    lines_cr = dist['line_cr_ids']
#                                if lines_cr != []:
#                                    for ml in lines_cr:
#                                        remain_credit_amount += ml['amount_unreconciled']
#                                dist.update(self.pool.get('account.voucher').onchange_journal_voucher(cr, uid, [], False, False, amt- CREDIT, partner, multi.payment_journal.id , ttype, invoice.company_id.id, context= ctx)['value'])
#                            else:
#                                if dist['line_dr_ids'] != []:
#                                    lines_cr = dist['line_dr_ids']
#                                if lines_cr != []:
#                                    for ml in lines_cr:
#                                        remain_credit_amount += ml['amount_unreconciled']
                            dist.update(self.pool.get('account.voucher').onchange_journal_voucher(cr, uid, [], False, False, amt- CREDIT, partner, multi.payment_journal.id , ttype, invoice.company_id.id, context= ctx)['value'])
#                            if not multi.apply_credit and remain_credit_amount > 0:
##                                dist.update(self.pool.get('account.voucher').onchange_amount(cr, uid, [], abs(remain_credit_amount - amt), 1, partner,  multi.payment_journal.id , invoice.currency_id.id, ttype, invoice.date_invoice, invoice.currency_id.id, invoice.company_id.id, context= ctx)['value'])
#                    
#                            else:
                            dist.update(self.pool.get('account.voucher').onchange_amount(cr, uid, [], amt- CREDIT, 1, partner,  multi.payment_journal.id , invoice.currency_id.id, ttype, invoice.date_invoice, invoice.currency_id.id, invoice.company_id.id, context= ctx)['value'])
#                            lines = []
#                            lines_cr = []
#                            lines_dr = []
                            if dist['line_cr_ids'] != []:
                                lines_cr = dist['line_cr_ids']
                            if dist['line_dr_ids'] != []:
                                lines_dr = dist['line_dr_ids']
                            if 'line_ids' in dist.keys():
                                dist.pop('line_ids')
                            dist.pop('line_cr_ids')
                            dist.pop('line_dr_ids')
                            voucher_id = voucher_obj.create(cr, uid, dist,context=context)
                            account_invoice.write(cr, uid, inv_ids, {'voucher_id': voucher_id},context=context)
                            if invoice.print_check:
                                vouchers.append(voucher_id)
                            else:
                                voucher_not_print.append(voucher_id)
                            # FIx me 
                            if context.get('default_inv_type') == 'in':
                                # Credit manage for supplier
                                if lines_cr != []:
                                    for ml in lines_cr:
                                        if multi.apply_credit:
                                            if CREDIT >= ml['amount']:
                                                if CREDIT == 0 or CREDIT == ml['amount']:
                                                    ml.update({'voucher_id': voucher_id, 'reconcile':False,'amount': CREDIT})
                                                    CREDIT = CREDIT - ml['amount']
                                                else:
                                                    ml.update({'voucher_id': voucher_id,'reconcile':True,'amount': ml['amount']})
                                                    CREDIT = CREDIT - ml['amount']
                                            else:
                                                if not CREDIT < 0: 
                                                    ml.update({'voucher_id': voucher_id, 'reconcile':False,'amount': CREDIT})
                                                else:
                                                    ml.update({'voucher_id': voucher_id, 'reconcile':False,'amount': 0})
                                                CREDIT = 0 
                                        else:
                                            ml.update({'voucher_id': voucher_id, 'reconcile':False, 'amount': 0.0})
                                        self.pool.get('account.voucher.line').create(cr, uid, ml)
                                # Debit manage for supplier
                                if lines_dr != []:
                                    for ml in lines_dr:
                                        move_line_is = self.pool.get('account.move.line').browse(cr, uid, ml['move_line_id'], context=context).move_id.id
                                        for inv in account_invoice.browse(cr, uid, inv_ids, context=context):
                                            if move_line_is == inv.move_id.id:
                                                ml.update({'voucher_id': voucher_id, 'amount': ml['amount']})
                                                self.pool.get('account.voucher.line').create(cr, uid, ml)
                            # Credit manage for customer
                            elif context.get('default_inv_type') == 'out':
                                if lines_cr != []:
                                    for ml in lines_cr:
                                        move_line_is = self.pool.get('account.move.line').browse(cr, uid, ml['move_line_id'], context=context).move_id.id
                                        for inv in account_invoice.browse(cr, uid, inv_ids, context=context):
                                            if move_line_is == inv.move_id.id:
                                                ml.update({'voucher_id': voucher_id, 'amount': ml['amount']})
                                                self.pool.get('account.voucher.line').create(cr, uid, ml)
                                #Debit manage for customer
                                if lines_dr != []:
                                    for ml in lines_dr:
                                        if multi.apply_credit:
                                            if CREDIT >= ml['amount']:
                                                if CREDIT == 0 or CREDIT == ml['amount']:
                                                    ml.update({'voucher_id': voucher_id, 'reconcile':False,'amount': CREDIT})
                                                    CREDIT = CREDIT - ml['amount']
                                                else:
                                                    ml.update({'voucher_id': voucher_id,'reconcile':True,'amount': ml['amount']})
                                                    CREDIT = CREDIT - ml['amount']
                                            else:
                                                if not CREDIT < 0:
                                                    ml.update({'voucher_id': voucher_id, 'reconcile':False,'amount': CREDIT})
                                                else:
                                                    ml.update({'voucher_id': voucher_id, 'reconcile':False,'amount': 0})
                                                CREDIT = 0 
                                        else:
                                            ml.update({'voucher_id': voucher_id, 'reconcile':False, 'amount': 0.0})
                                        self.pool.get('account.voucher.line').create(cr, uid, ml)
                            ctx.update({'invoice_id': invoice.id})
                            #method slice for only supplier voucher post
                            self.do_post_or_nothing(cr, uid, voucher_id, context.get('default_inv_type','out'))
                            self.write(cr, uid, ids, {'state':'posted'}, context=context)
        return True
    
    def cancel(self,cr, uid, ids, context=None):
        res = {}
        voucher_obj = self.pool.get('account.voucher')
        for multi in self.browse(cr, uid, ids, context=context):
            for invoice in multi.invoice_ids:
                if invoice.voucher_id:
                    res = voucher_obj.cancel_voucher(cr, uid, [invoice.voucher_id.id], context=context)
        self.write(cr, uid, ids, {'state':'cancel'}, context=context)
        return res

    def set_to_open(self,cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'new'}, context=context)

    def print_checks(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')
        vouchers = []
        voucher_not_print = []
        account_invoice = self.pool.get('account.invoice')
        vouchers = []
        for multi in self.browse(cr, uid, ids, context=context):
            if not multi.invoice_ids:
                raise osv.except_osv(_('Error!'),_("Please Get Invoices first."))
            if multi.invoice_ids:
                for invoice in multi.invoice_ids:
                    total_paid_amt = 0.0
                    if invoice.print_check and multi.payment_journal.allow_check_writing:
                        vouchers.append(invoice.voucher_id.id)
            view_ref = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_check_writing', 'view_account_check_write')
            voucher_list = list(set(vouchers))
            view_id = view_ref and view_ref[1] or False,
            context.update({'active_ids':voucher_list})
            self.write(cr, uid, ids, {'state':'printed'}, context=context)
            if not vouchers:
                raise osv.except_osv(_('Error!'),_("Minimum one invoice should be checked as 'Print'."))
            return {
                   'type': 'ir.actions.act_window',
                   'name': 'Print Checks',
                   'view_mode': 'form',
                   'view_type': 'form',
                   'view_id': view_id,
                   'res_model': 'account.check.write',
                   'nodestroy': True,
                   'target':'new',
                   'context': context,
                   }
        return True

    def get_invoice(self, cr, uid, ids, context=None):
        # Method use for open invoices to be paid
        if context is None:
            context = {}
        invoice_obj = self.pool.get('account.invoice')
        voucher_obj = self.pool.get('account.voucher')
        multipay = self.browse(cr, uid, ids, context=context)[0]
        invoice_type = ''
        if context.get('default_inv_type') == 'in':
            invoice_type = 'in_invoice'
        else: 
            invoice_type = 'out_invoice'
        invoice_ids =[]
        vals = {}
        if multipay:
            domain = ''
            if multipay.amount_due_by:
                if multipay.payment_method == 'on_due_date':
                    cr.execute("SELECT id FROM account_invoice s  \
                            WHERE s.date_due = %s \
                            AND (s.state = 'open') AND (s.type=%s) order by partner_id, id desc \
                                ",(multipay.amount_due_by,invoice_type))
                else:
                    cr.execute("SELECT id FROM account_invoice s  \
                                WHERE s.date_due <= %s \
                                AND (s.state = 'open') AND (s.type=%s) order by partner_id,id desc\
                                    ",(multipay.amount_due_by,invoice_type))
                invoice_ids =  map(lambda x: x[0], cr.fetchall())
        partners = {}
        if SUPERUSER_ID != uid:
            invoice_ids = invoice_obj.search(cr, uid, [('id', 'in', invoice_ids)], order='partner_id,id desc', context=context)
        ctx = context.copy()
#        ctx.update({'date_from':multipay.amount_due_by,'date_to':multipay.amount_due_by})
        dist = {}
        use_credit = 0.0
        for inv in invoice_obj.browse(cr, uid, invoice_ids, context=ctx):
            invoice_obj.write(cr, uid, inv.id,{'dummy_id' :ids[0]}, context=context)
            if inv.partner_id.is_company:
                partner = inv.partner_id.id
            else:
                if not inv.partner_id.parent_id:
                    partner = inv.partner_id.id
                else:
                    partner = inv.partner_id.parent_id.id
            
            if inv.partner_id.id in partners:
                vals ={'use_credit_available' : 0,
                       'credit_available': 0.0,
                       'amount_paid': inv.residual or 0.0,
#                        'pay':True,
                       'pay':False,
                       'print_check':False}
                vals['use_credit_available'] = partners[partner]
                # Only credit show in first invoices 
                
#                    use_credit = abs((use_credit - inv.residual))
#                else:
#                    vals ={'use_credit_available' : abs(use_credit),
#                           'credit_available': 0.0,
#                           'amount_paid': inv.residual  or 0.0,
#                           'pay':True,
#                           'print_check':True}
#                    use_credit = (use_credit - inv.residual)
            else:
                if context.get('default_inv_type') == 'in':
                   lines_cr = []
                   if multipay.apply_credit:
                        ttype = inv.type in ['in_invoice', 'out_refund'] and 'payment' or 'receipt'
                        dist.update(self.pool.get('account.voucher').onchange_partner_id(cr, uid, [], inv.partner_id.parent_id.id or inv.partner_id.id,  multipay.payment_journal.id , 0, inv.currency_id.id, ttype, inv.date_invoice, context= context)['value'])
                        remain_credit_amount = 0.0
                        if dist['line_cr_ids'] != []:
                                lines_cr = dist['line_cr_ids']
                        if lines_cr != []:
                            for ml in lines_cr:
                                remain_credit_amount += ml['amount_unreconciled']
#                        use_credit = (remain_credit_amount - inv.residual)
                        if lines_cr:
                            partners[partner] = remain_credit_amount
                            vals ={'credit_available':  0.0,
                                   'use_credit_available':remain_credit_amount or 0.0,
                               'amount_paid': inv.residual or 0.0,
#                                'pay':True,
                               'pay':False,
#                                'print_check':True
                               'print_check':False}
#                                else:
#                                    vals ={'credit_available': 0.0,
#                                           'use_credit_available':remain_credit_amount or 0.0,
#                                       'amount_paid':inv.residual  or 0.0,
#                                       'pay':True,
#                                       'print_check':True}
#                            else:
#                                vals ={'credit_available': 0.0,
#                                   'use_credit_available':remain_credit_amount or 0.0,
#                               'amount_paid': inv.residual  or 0.0,
#                               'pay':True,
#                               'print_check':True}
                        else:
                            vals ={'credit_available': 0.0,
                                   'use_credit_available':0.0,
                                   'amount_paid': inv.residual or 0.0,
#                                    'pay':True,
                                   'pay':False,
#                                    'print_check':True
                                   'print_check':False}
#                   elif not multipay.apply_credit and inv.partner_id.credit:
#                        vals ={'credit_available': 0.0,
#                               'use_credit_available':0.0,
#                               'amount_paid': inv.residual  or 0.0,
#                               'pay':True,
#                               'print_check':True}
                   else:
                            vals ={'credit_available': 0.0,
                                   'use_credit_available': 0.0,
                                   'amount_paid': inv.residual  or 0.0,
#                                    'pay':True,
                                   'pay':False,
#                                    'print_check':True
                                   'print_check':False}
                elif context.get('default_inv_type') == 'out':
                    lines_cr = []
                    if multipay.apply_credit:
                        ttype = inv.type in ['in_invoice', 'out_refund'] and 'payment' or 'receipt'
                        dist.update(self.pool.get('account.voucher').onchange_partner_id(cr, uid, [], inv.partner_id.parent_id.id or inv.partner_id.id,  multipay.payment_journal.id , 0, inv.currency_id.id, ttype, inv.date_invoice, context= context)['value'])
                        remain_credit_amount = 0.0
                        if dist['line_dr_ids'] != []:
                                lines_cr = dist['line_dr_ids']
                        if lines_cr != []:
                            for ml in lines_cr:
                                remain_credit_amount += ml['amount_unreconciled']
                        use_credit = (remain_credit_amount - inv.residual)
                        if lines_cr:
#                            if use_credit <= inv.residual:
#                                if inv.residual - (remain_credit_amount) < 0 :
                                partners[partner] = remain_credit_amount
                                vals ={'credit_available':  0.0,
                                       'use_credit_available':remain_credit_amount or 0.0,
                                   'amount_paid': inv.residual or 0.0,
#                                    'pay':True,
                                   'pay':False,
                                   'print_check':False}
#                                else:
#                                    vals ={'credit_available': 0.0,
#                                           'use_credit_available':remain_credit_amount or 0.0,
#                                       'amount_paid':inv.residual or 0.0 ,
#                                       'pay':True,
#                                       'print_check':True}
#                            else:
#                                vals ={'credit_available': 0.0,
#                                   'use_credit_available':remain_credit_amount or 0.0,
#                               'amount_paid': inv.residual or 0.0,
#                               'pay':True,
#                               'print_check':True}
                        else:
                            vals ={'credit_available':  0.0,
                                   'use_credit_available': 0.0,
                                   'amount_paid': inv.residual or 0.0,
#                                    'pay':True,
                                   'pay':False,
                                   'print_check':False}
#                    elif not multipay.apply_credit and inv.partner_id.credit:
#                        vals ={'credit_available': 0.0,
#                               'use_credit_available':0.0,
#                               'amount_paid': inv.residual  or 0.0,
#                               'pay':True,
#                               'print_check':True}
                    else:
                            vals ={'credit_available': 0.0,
                                   'use_credit_available': 0.0,
                                   'amount_paid': inv.residual  or 0.0,
#                                    'pay':True,
                                   'pay':False,
                                   'print_check':False}

            invoice_obj.write(cr, uid, [inv.id], vals, context=context)
        if not invoice_ids:
            raise osv.except_osv(_('Error!'),_("There is no any invoices in this criteria "))
        self.write(cr, uid, ids, {'invoice_ids':[( 6,0, invoice_ids),],'state':'draft'}, context=context)
        self.cal_end_balance( cr, uid, ids, context=context)
        return True

    def on_change_invoice(self, cr, uid, ids, context=None):
        self.cal_end_balance( cr, uid, ids, context=context)
        return

class check_log(osv.Model):
    _name = 'check.log'
    _description=""" This model use for check record"""
    
    _columns = {
                'name': fields.char('Check Number'),
                'voucher_id': fields.many2one('account.voucher', 'Voucher'),
                'state': fields.selection([('void','Voided'),('print','Printed'),('re_print','Re-printed')])
            }
