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
from openerp import netsvc

class invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'prepaid': fields.boolean('Prepaid Invoice', readonly=True)
    }
    
class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    
    def _invoiced_rate(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cursor, user, ids, context=context):
            tot = 0.0
            amount_untaxed=0.0
            for invoice in purchase.invoice_ids:
                if invoice.state not in ('draft','cancel'):
                    tot += invoice.amount_untaxed
            for line in purchase.order_line: 
                if not line.adavance_product:
                    amount_untaxed+=line.price_subtotal       
            if amount_untaxed:
                res[purchase.id] = tot * 100.0 / amount_untaxed
            else:
                res[purchase.id] = 0.0
        return res
    
    def _invoiced(self, cursor, user, ids, name, arg, context=None):
        res = {}
        for purchase in self.browse(cursor, user, ids, context=context):
            invoiced = False
            if purchase.invoiced_rate >= 100.00:
                invoiced = True
            res[purchase.id] = invoiced
        return res
    
    _columns = {
        'invoiced': fields.function(_invoiced, string='Invoice Received', type='boolean', help="It indicates that an invoice has been paid"),
        'invoiced_rate': fields.function(_invoiced_rate, string='Invoiced', type='float'),
    }
    
class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _columns = {
        'adavance_product': fields.boolean('Advance Product', readonly=True)
    }    