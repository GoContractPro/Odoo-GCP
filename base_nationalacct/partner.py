# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
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

class res_partner(osv.Model):
    _inherit = "res.partner"
    
    #===========================================================================
    # Overriding a function defined on account module.
    # This is to include the payable and receivable from child partners if the 
    # account is a national account.
    #===========================================================================
    def _credit_debit_get(self, cr, uid, ids, field_names, arg, context=None):
        """
        calculating payable and receivable from account moves for the mentioned partners
        """
        query = self.pool.get('account.move.line')._query_get(cr, uid, context=context)
        cr.execute("""
                   SELECT l.partner_id, a.type, SUM(l.debit-l.credit)
                   FROM account_move_line l
                   LEFT JOIN account_account a ON (l.account_id=a.id)
                   WHERE a.type IN ('receivable','payable')
                   AND l.partner_id IN %s
                   AND l.reconcile_id IS NULL
                   AND """ + query + """
                   GROUP BY l.partner_id, a.type
                   """,(tuple(ids), ))
        maps = {'receivable': 'credit', 'payable': 'debit'}
        res = {}
        for id in ids:
            res[id] = dict.fromkeys(field_names, 0)
        for pid, type, val in cr.fetchall():
            if val is None: val = 0
            partner = self.browse(cr, uid, pid, context=context)
            #Include the payable and receivable form child partner if the Partner is national account
            if partner.nat_acc_parent:
                res[pid][maps[type]] = (type == 'receivable') and val or -val
                child_partner_ids = self.search(cr, uid, [('parent_id', 'child_of', [partner.id])], context=context)
                if child_partner_ids: 
                    child_partner_ids.remove(partner.id)
                    for val in self.read(cr, uid, child_partner_ids, ['credit', 'debit'], context=context):
                        res[pid][maps[type]] += val.get(maps[type], 0)
            else:
                res[pid][maps[type]] = (type == 'receivable') and val or -val
            
        return res

    def _credit_search(self, cr, uid, obj, name, args, context=None):
        """
        search function for the credit field
        """
        return self._asset_difference_search(cr, uid, obj, name, 'receivable', args, context=context)
    
    def _debit_search(self, cr, uid, obj, name, args, context=None):
        """ 
        search function for the debit field 
        """
        return self._asset_difference_search(cr, uid, obj, name, 'payable', args, context=context)
    
    _columns = {
        'credit': fields.function(_credit_debit_get, fnct_search=_credit_search, method=True, string='Total Receivable', multi='dc', 
                                  help="Total amount this customer owes you."),
        'debit': fields.function(_credit_debit_get, fnct_search=_debit_search, method=True, string='Total Payable', multi='dc', 
                                 help="Total amount you have to pay to this supplier."),
        'nat_acc_parent': fields.boolean('National Acct Parent', help='Designates this partner as the top level parent of a "National Account".'),
        }
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
