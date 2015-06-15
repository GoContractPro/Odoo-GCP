# -*- coding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Verts Services India Pvt. Ltd. (<http://www.verts.co.in>)
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

from openerp.osv import fields
from openerp.osv import osv
from openerp import netsvc
import time
from datetime import datetime, timedelta
from openerp.tools.translate import _


class sale_order(osv.osv):
    _inherit = 'sale.order'
    _columns = {
                'ship_via':fields.many2one('account.ship.via','Ship Via'),
                'tracking_numb':fields.char('Tracking Number',size=32),
                }
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals['partner_invoice_id'] = order.partner_invoice_id.id
        invoice_vals['partner_shipping_id'] = order.partner_shipping_id.id
        invoice_vals['ship_via'] = order.ship_via and order.ship_via.id or False
        invoice_vals['tracking_numb'] = order.tracking_numb
        return invoice_vals
sale_order()

class account_ship_via(osv.osv):
    _name = 'account.ship.via'
    _columns = {
                'name':fields.char('Ship Via', size=64,required=True),
                'desc':fields.text('Description'),
                }
account_ship_via()

class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
                'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True, states={'draft':[('readonly',False)]}, help="Invoice address for current Invoice."),
                'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', readonly=True, states={'draft':[('readonly',False)]}, help="Delivery address for current Invoice."),
                'ship_via':fields.many2one('account.ship.via','Ship Via',readonly=True, states={'draft':[('readonly',False)]}),
    #           'partner_numn':fields.char('Customer Number',size=32),
                'partner_numb':fields.related('partner_id','ref', readonly=True, type='char', string="Customer Number"),
                'tracking_numb':fields.char('Tracking Number',size=32,readonly=True, states={'draft':[('readonly',False)]}),
                }
    
    _defaults = {
        'partner_invoice_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['invoice'])['invoice'],
        'partner_shipping_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['delivery'])['delivery'],
    }
    
    def invoice_print(self, cr, uid, ids, context=None):
        '''
        This function prints the invoice and mark it as sent, so that we can see more easily the next step of the workflow
        '''
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self.write(cr, uid, ids, {'sent': True}, context=context)
        datas = {
             'ids': ids,
             'model': 'account.invoice',
             'form': self.read(cr, uid, ids[0], context=context)
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'npg.custom.account.invoice',
            'datas': datas,
            'nodestroy' : True
        }
    
    
    def onchange_partner_id(self, cr, uid, ids, type, partner_id,\
            date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        """
         Overridden On Change Partner method to add shipping address of the partner.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: Current Logged in User's Identifier.
         @param ids: List of ids.
         @param type : Type of invoice
         @param partner_id : Identifier for Customer/Supplier
         @param date_invoice : Invoice date
         @param payment_term : Payment Term selected on Invoice
         @param partner_bank_id : Bank Account selected on Invoice
         @param company_id : Company
         @return: True
        """
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice=date_invoice,payment_term=payment_term, partner_bank_id=partner_bank_id, company_id=company_id)
        if type == 'out_invoice' or type == 'in_invoice':
            shipping_address = False
            salesman_id = False
            if partner_id:
                addr = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['delivery', 'invoice', 'contact'])
            else:
               return res 
            res['value'].update({'partner_invoice_id': addr['invoice'],
                                    'partner_shipping_id': addr['delivery'],})
        return res

    
account_invoice()

class purchase_order(osv.osv):
    _inherit = 'purchase.order'
    _columns = {
                'ship_via':fields.many2one('account.ship.via','Ship Via'),
                'tracking_numb':fields.char('Tracking Number',size=32),
                'partner_invoice_id': fields.many2one('res.partner', 'Invoice Address', readonly=True, states={'draft':[('readonly',False)]}, help="Invoice address for current Purchase Order."),
                'partner_shipping_id': fields.many2one('res.partner', 'Delivery Address', readonly=True, states={'draft':[('readonly',False)]}, help="Delivery address for current Purchase Order."),
                }
    
    _defaults = {
        'partner_invoice_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['invoice'])['invoice'],
        'partner_shipping_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['delivery'])['delivery'],
    }
    
    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        invoice_vals = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context=context)
        invoice_vals['partner_invoice_id'] = order.partner_invoice_id.id
        invoice_vals['partner_shipping_id'] = order.partner_shipping_id.id
        invoice_vals['ship_via'] = order.ship_via and order.ship_via.id or False
        invoice_vals['tracking_numb'] = order.tracking_numb
        return invoice_vals
    
    def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        if context is None:
            context = {}
        journal_obj = self.pool.get('account.journal')
        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')

        res = False
        uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        for order in self.browse(cr, uid, ids, context=context):
            context.pop('force_company', None)
            if order.company_id.id != uid_company_id:
                #if the company of the document is different than the current user company, force the company in the context
                #then re-do a browse to read the property fields for the good company.
                context['force_company'] = order.company_id.id
                order = self.browse(cr, uid, order.id, context=context)
            pay_acc_id = order.partner_id.property_account_payable.id
            journal_ids = journal_obj.search(cr, uid, [('type', '=', 'purchase'), ('company_id', '=', order.company_id.id)], limit=1)
            if not journal_ids:
                raise osv.except_osv(_('Error!'),
                    _('Define purchase journal for this company: "%s" (id:%d).') % (order.company_id.name, order.company_id.id))

            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)

                po_line.write({'invoice_lines': [(4, inv_line_id)]}, context=context)

            # get invoice data and create invoice
            inv_data = {
                'name': order.partner_ref or order.name,
                'reference': order.partner_ref or order.name,
                'account_id': pay_acc_id,
                'type': 'in_invoice',
                'partner_id': order.partner_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'journal_id': len(journal_ids) and journal_ids[0] or False,
                'invoice_line': [(6, 0, inv_lines)],
                'origin': order.name,
                'fiscal_position': order.fiscal_position.id or False,
                'payment_term': order.payment_term_id.id or False,
                'company_id': order.company_id.id,
                'partner_invoice_id':order.partner_invoice_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'ship_via' : order.ship_via and order.ship_via.id or False,
                'tracking_numb': order.tracking_numb
            }
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]}, context=context)
            res = inv_id
        return res

    
purchase_order()