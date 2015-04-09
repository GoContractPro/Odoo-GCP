# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp.report import report_sxw
from amount_to_words import amount_to_words
from openerp.tools.amount_to_text_en import amount_to_text

class report_print_check1(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(report_print_check1, self).__init__(cr, uid, name, context)
        self.number_lines = 0
        self.number_add = 0
        self.localcontext.update({
            'time': time,
            'get_lines': self.get_lines,
            'fill_stars' : self.fill_stars,
            'total_amt' : self.total_amt,
            'amt_word' : self.amt_word,
            'total_credit':self.total_credit,
        })
    
    def fill_stars(self, amount):
#        amount = amount.replace('Dollars',' ')
        if len(amount) < 90:
            stars = 90 - len(amount)
            return ' '.join([amount,'*'*stars])

        else: return amount

    def total_amt(self, voucher):
        voucher_obj = self.pool.get('account.voucher')
        total = 0.0
        for voucher in voucher_obj.browse(self.cr, self.uid, [voucher.id]):
            if voucher.line_dr_ids:
                for cr in voucher.line_dr_ids:
#                     if cr.move_line_id.invoice.print_check:
                    total += cr.amount
                    if cr.move_line_id.invoice.credit_available:
                        total = total - cr.move_line_id.invoice.credit_available
        return total

    def total_credit(self, voucher_line):
        inv_obj = self.pool.get('account.invoice')
        credit = 0.0
        if voucher_line['name']:
            inv_id = inv_obj.search(self.cr, self.uid, [('number','=',voucher_line['name'])])
            if not inv_id:
                inv_id = inv_obj.search(self.cr, self.uid, [('supplier_invoice_number','=',voucher_line['name'])])
            credit = inv_obj.browse(self.cr, self.uid, inv_id[0]).credit_available
        return credit

    def amt_word(self, amt,crny):
#        if crny and crny.upper() == 'USD':
#            crny = 'Dollars'
        amount = amount_to_text(amt,currency=crny)
        amount = amount.replace('USD','Dollars')
        return amount

    def get_lines(self, voucher_lines):
        result = []
        res = {}
        self.number_lines = len(voucher_lines)
        cnt = 10
        for voucher in voucher_lines:
            cnt -= 1
            if voucher.move_line_id.invoice and voucher.reconcile:  #voucher.move_line_id.invoice.print_check
                res = {
                    'date_due' : voucher.date_due,
                    'name' : voucher.name or voucher.move_line_id and voucher.move_line_id.invoice and voucher.move_line_id.invoice.supplier_invoice_number,
                    'amount_original' : voucher.amount_original and voucher.amount_original or False,
                    'amount_unreconciled' : voucher.amount_unreconciled and voucher.amount_unreconciled or False,
                    'amount' : voucher.amount and voucher.amount or False,
                    'supplier_invoice_number': voucher.move_line_id and voucher.move_line_id.invoice and voucher.move_line_id.invoice.supplier_invoice_number,
                    'date_invoice': voucher.move_line_id.invoice and  voucher.move_line_id.invoice.date_invoice or False,
                    'residual':voucher and voucher.move_line_id and voucher.move_line_id.invoice and voucher.move_line_id.invoice.residual or 0.0 
                }
#                 
#             else :
#                 res = {
#                     'date_due' : False,
#                     'name' : False,
#                     'amount_original' : False,
#                     'amount_due' : False,
#                     'amount' : False,
#                     'date_invoice' : False,
#                     'residual':0.0
#                 }
                result.append(res)
            if cnt == 0:
                break
#         for i in range(0, min(10,self.number_lines)):
#             if i < self.number_lines:
                
        return result

report_sxw.report_sxw(
    'report.account.print.check.top.multi',
    'account.voucher',
    'addons/batch_payment_invoices/report/check_print_top.rml',
    parser=report_print_check1,header=False
)

report_sxw.report_sxw(
    'report.account.print.check.middle.multi',
    'account.voucher',
    'addons/batch_payment_invoices/report/check_print_middle.rml',
    parser=report_print_check1,header=False
)

report_sxw.report_sxw(
    'report.account.print.check.bottom.multi',
    'account.voucher',
    'addons/batch_payment_invoices/report/check_print_bottom.rml',
    parser=report_print_check1,header=False
)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
