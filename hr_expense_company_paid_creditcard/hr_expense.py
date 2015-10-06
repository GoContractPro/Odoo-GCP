# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 NovaPoint Group INC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################


from openerp.osv import fields, osv
from openerp import tools
from openerp.tools.translate import _
from openerp import netsvc
from datetime import datetime, timedelta

class hr_expense_expense(osv.osv):
    
    _inherit="hr.expense.expense"
    _columns={
              'company_paid':fields.boolean("Company Paid Expenses?"),
              }
    
    def action_move_create(self, cr, uid, ids, context=None):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_obj = self.pool.get('account.move')
        for exp in self.browse(cr, uid, ids, context=context):
            if not exp.company_paid and not exp.employee_id.address_home_id:
                raise osv.except_osv(_('Error!'), _('The employee must have a home address.'))
            if not exp.company_paid and not exp.employee_id.address_home_id.property_account_payable.id:
                raise osv.except_osv(_('Error!'), _('The employee must have a payable account set on his home address.'))
            
#             Verts Changes for creditcard company
            if exp.company_paid and not exp.journal_id.credit_card_company_id:
                raise osv.except_osv(_('Error!'), _('Credit card company must be selected in expense journal.'))
            if exp.company_paid and not exp.journal_id.credit_card_company_id.property_account_payable.id:
                raise osv.except_osv(_('Error!'), _('The Credit card company must have a payable account set.'))

            company_currency = exp.company_id.currency_id.id
            diff_currency_p = exp.currency_id.id <> company_currency
            
            #create the move that will contain the accounting entries
            move_id = move_obj.create(cr, uid, self.account_move_get(cr, uid, exp.id, context=context), context=context)
        
            #one account.move.line per expense line (+taxes..)
            eml = self.move_line_get(cr, uid, exp.id, context=context)
            
            #create one more move line, a counterline for the total on payable account
            total, total_currency, eml = self.compute_expense_totals(cr, uid, exp, company_currency, exp.name, eml, context=context)
            
            partner = exp.company_paid and exp.journal_id.credit_card_company_id or exp.employee_id.address_home_id
            acc = partner.property_account_payable.id
            eml.append({
                    'type': 'dest',
                    'name': '/',
                    'price': total, 
                    'account_id': acc, 
                    'date_maturity': exp.date_confirm, 
                    'amount_currency': diff_currency_p and total_currency or False, 
                    'currency_id': diff_currency_p and exp.currency_id.id or False, 
                    'ref': exp.name
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, partner, exp.date_confirm, context=context)), eml)
            journal_id = move_obj.browse(cr, uid, move_id, context).journal_id
            # post the journal entry if 'Skip 'Draft' State for Manual Entries' is checked
            if journal_id.entry_posted:
                move_obj.button_validate(cr, uid, [move_id], context)
            move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=context)
            self.write(cr, uid, ids, {'account_move_id': move_id, 'state': 'done'}, context=context)
        return True
hr_expense_expense()


class account_journal(osv.osv):
    
    _inherit="account.journal"
    _columns={
              'credit_card_company_id':fields.many2one("res.partner",string="Credit Card Company"),
              }

account_journal()