import time
from openerp.osv import osv
from openerp.osv import fields
from openerp import netsvc
from openerp.tools.translate import _

class invoice_payment_wizard(osv.TransientModel):
    """
        A wizard to manage the invoice payment
    """
    _name = 'invoice.payment.wizard'
    _description = "Invoice Payment Wizard"
    _columns = {
        'invoice_ids': fields.one2many('account.invoice.payment', 'wizard_id', string='Invoices'),
    }
    
    def default_get(self, cr, uid, fields, context=None):
        if context == None:
            context = {}
        invoice_ids = context.get('active_ids', [])
        wiz_id = context.get('active_id', None)
        res = []
        invoices = self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context)
        for invoice in invoices:
            if invoice.state =='open':
                res.append((0, 0, {
                     'wizard_id': wiz_id,
                     'invoice_id': invoice.id,
                     'partner_id': invoice.partner_id.id,
                     'amount_paid': invoice.amount_paid,
                     'ref': invoice.reference,
                     'journal_id': invoice.journal_id.id,
                     'different_amount': invoice.residual - invoice.amount_paid,
                     'date': time.strftime('%Y-%m-%d'),
                     'period_id': invoice.period_id.id,
                     'memo': "Pay for %s " % (invoice.reference or None) ,
                     'state': invoice.state,
                     }))
        return {'invoice_ids': res}
    
    def invoice_payment(self, cr, uid, id, context=None):
        wizard = self.browse(cr, uid, id, context=context)[0]
        invoice_ids = [invoice.id for invoice in wizard.invoice_ids]
        self.pool.get('account.invoice.payment').invoice_payment(cr, uid, invoice_ids, context=context)
        return {
            'type': 'ir.actions.act_window_close',
        }
        
class account_invoice_payment(osv.TransientModel):
    """
        A wizard to show the invoices payment
    """
    _name = 'account.invoice.payment'
    _description = "Invoice Payment"
    _columns = {
        'wizard_id': fields.many2one('invoice.payment.wizard', string='Wizard', required=True),
        'invoice_id': fields.many2one('account.invoice', string='Invoice'),
        'partner_id': fields.many2one('res.partner', string='Partner'),
        'amount_paid': fields.float('Amount paid'),
        'ref': fields.char('Reference'),
        'journal_id': fields.many2one('account.journal', string='Journal'),
        'different_amount': fields.float('Different Amount'),
        'date': fields.date('Date'),
        'period_id': fields.many2one('account.period', string='Period'),
        'memo': fields.char('Memo'),
        'state': fields.char('State'),
        'payment_method': fields.many2one('account.journal', string='Payment Method', domain=[('type', 'in', ['bank', 'cash'])],)
    }
    
    def invoice_payment(self, cr, uid, ids, context=None):
        voucher_obj = self.pool.get('account.voucher')
        account_invoice = self.pool.get('account.invoice')
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state in ('open',):
                invoice_id = account_invoice.browse(cr, uid, invoice.invoice_id.id, context=None)
                ctx = dict(context)
                ctx.update({'payment_expected_currency':invoice_id.currency_id.id, 'invoice_id': invoice.invoice_id.id})
                if not invoice.payment_method:
                    raise osv.except_osv(_('Error!'),_("You need Payment Method."))
#                 if invoice.residual < invoice.amount_paid:
#                     raise osv.except_osv(_('Error!'),_("Amount paid is greater than Balance."))
                dist =  {
                     'partner_id'   : invoice.partner_id.id,
                     'amount'       : invoice.amount_paid,
                     'journal_id'   : invoice.payment_method.id                    
                }
                dist.update(self.pool.get('account.voucher').onchange_partner_id(cr, uid, [], invoice.partner_id.id,  invoice.payment_method.id , 0, invoice_id.currency_id.id, False, invoice.date, context= ctx)['value'])
                dist.update(self.pool.get('account.voucher').onchange_amount(cr, uid, [], invoice.amount_paid, 1, invoice_id.partner_id.id,  invoice.payment_method.id , invoice_id.currency_id.id, False, invoice.date, invoice_id.currency_id.id, invoice_id.company_id.id, context= ctx)['value'])
                dist.update(self.pool.get('account.voucher').onchange_journal_voucher(cr, uid, [], False, False, invoice.amount_paid, invoice.partner_id.id, invoice.payment_method.id , invoice_id.type == 'in_invoice' and 'payment' or False, invoice_id.company_id.id, context= ctx)['value'])
                lines = []
                if dist['line_cr_ids'] != []:
                    lines = dist['line_cr_ids']                
                if dist['line_dr_ids'] != []:
                    lines = dist['line_dr_ids']
                dist.pop('line_cr_ids')
                dist.pop('line_dr_ids')
                voucher_id = voucher_obj.create(cr, uid, dist)
                for ml in lines:
                    ml.update({'voucher_id': voucher_id})
                    self.pool.get('account.voucher.line').create(cr, uid, ml)
                voucher_obj.button_proforma_voucher(cr, uid, [voucher_id], context= None)
                
            account_invoice.write(cr,uid,[invoice_id.id], {'amount_paid':0})