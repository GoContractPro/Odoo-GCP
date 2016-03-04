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

from openerp.osv import fields,osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

# Overloaded stock_picking to manage carriers :
class stock_picking(osv.osv):
    _inherit = 'stock.picking'

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        inv_vals = super(stock_picking, self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
        sale = move.picking_id.sale_id
        if sale:
            inv_vals.update({
                'sale_order': sale.id,
                'stock_picking': key
                })
        if move.picking_id:
            inv_vals.update({
                'picking_id': move.picking_id.id,
                })
        return inv_vals

    def _get_company_code(self, cr, user, context=None):
        return [('grid', 'Price Grid')]

    def _get_picking_line(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            result[line.picking_id.id] = True
        return result.keys()
    
    def _get_sale_order(self, cr, uid, ids, context=None):
        return self.pool.get('stock.picking').search(cr, uid, [('sale_id', 'in', ids)])

    _columns = {
        'carrier_id':fields.many2one("delivery.carrier","Delivery Service"),
        'carrier_contact':fields.many2one("res.partner", "Carrier Contact", help="Contact Info for Carrier  responsible for Shipping"),
        'ship_income_account_id': fields.many2one('account.account', 'Ship Income GL Account',
                                           help='This account represents the g/l account for booking shipping income.'),
        'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
        'volume': fields.float('Volume'),
        'carrier_tracking_ref': fields.char('Carrier Tracking Ref', size=32),
        'number_of_packages': fields.integer('Number of Packages'),
        'weight_uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True,readonly="1",help="Unit of measurement for Weight",),
        'ship_service': fields.char('Ship Service', size=128, readonly=True),
        'shipcharge': fields.float('Shipping Charge', readonly=True),
        'shipcost': fields.float('Shipping Cost', readonly=True),
        }

    def _prepare_shipping_invoice_line(self, cr, uid, picking, invoice, context=None):
        """Prepare the invoice line to add to the shipping costs to the shipping's
           invoice.

            :param browse_record picking: the stock picking being invoiced
            :param browse_record invoice: the stock picking's invoice
            :return: dict containing the values to create the invoice line,
                     or None to create nothing
        """
        carrier_obj = self.pool.get('delivery.carrier')
        grid_obj = self.pool.get('delivery.grid')
        if not picking.carrier_id or \
            any(inv_line.product_id.id == picking.carrier_id.product_id.id
                for inv_line in invoice.invoice_line):
            return None
        grid_id = carrier_obj.grid_get(cr, uid, [picking.carrier_id.id],
                picking.partner_id.id, context=context)
        if not grid_id:
            raise osv.except_osv(_('Warning!'),
                    _('The carrier %s (id: %d) has no delivery grid!') \
                            % (picking.carrier_id.name,
                                picking.carrier_id.id))
        price = grid_obj.get_price_from_picking(cr, uid, grid_id,
                invoice.amount_untaxed, picking.weight, picking.volume,
                context=context)
        account_id = picking.carrier_id.product_id.property_account_income.id
        if not account_id:
            account_id = picking.carrier_id.product_id.categ_id\
                    .property_account_income_categ.id

        taxes = picking.carrier_id.product_id.taxes_id
        partner = picking.partner_id or False
        if partner:
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, partner.property_account_position, account_id)
            taxes_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, partner.property_account_position, taxes)
        else:
            taxes_ids = [x.id for x in taxes]

        return {
            'name': picking.carrier_id.name,
            'invoice_id': invoice.id,
            'uos_id': picking.carrier_id.product_id.uos_id.id,
            'product_id': picking.carrier_id.product_id.id,
            'account_id': account_id,
            'price_unit': price,
            'quantity': 1,
            'invoice_line_tax_id': [(6, 0, taxes_ids)],
        }
        
    
    def onchange_carrier_id(self, cr, uid, ids, carrier, context=None):
        res = {}
        if carrier:
            carrier_obj = self.pool.get('delivery.carrier').browse(cr, uid, carrier, context=context)
            res = {'value': {'carrier_contact' : carrier_obj.partner_id.id,
                            'ship_service' : carrier_obj.name,
                            'ship_income_account_id':carrier_obj.ship_income_account_id and carrier_obj.ship_income_account_id.id or False}}
        return res

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        res = self._get_journal_id(cr, uid, ids, context=context)
        result_partial = super(stock_picking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        if res and res[0]:
            journal_id = res[0][0]
            result = result_partial
            for picking_obj in self.browse(cr, uid, ids, context=context):
                sale = picking_obj.sale_id
                if sale and sale.order_policy == 'picking':
                    pick_id = result_partial[picking_obj.id]['delivered_picking']
                    result = self.action_invoice_create(cr, uid, [pick_id], journal_id, type=None, context=context)
                    inv_obj = self.pool.get('account.invoice')
                    if result:
                        inv_obj.write(cr, uid, result.values, {
                           'ship_service': sale.ship_service,
                           'shipcharge': sale.shipcharge,
                           'ship_income_account_id': sale.ship_method_id and sale.ship_method_id.account_id and \
                                              sale.ship_method_id.account_id.id or False,
#                           'ship_method_id': sale.ship_method_id and sale.ship_method_id.id
                           })
                        inv_obj.button_reset_taxes(cr, uid, result.values(), context=context)
        return result_partial

    def action_invoice_create(self, cr, uid, ids, journal_id=False,
             group=False, type='out_invoice', context=None):
        

        result = super(stock_picking, self).action_invoice_create(cr, uid,
                ids, journal_id=journal_id, group=group, type=type,
                context=context)
        
        picking_obj = self.pool.get('stock.picking').browse(cr,uid,ids[0],context)
        invoice_obj = self.pool.get('account.invoice')
        
        if picking_obj.carrier_id and picking_obj.carrier_id.invoice_ship_act_cost:
            shipcharge = picking_obj.shipcost
        else:
            shipcharge = picking_obj.shipcharge
            
        
        vals = {
            'ship_service':picking_obj.ship_service,
            'carrier_contact': picking_obj.carrier_contact.id,
            'shipcost':picking_obj.shipcost,
            'shipcharge': shipcharge,
            'sale_id':picking_obj.sale_id.id,
            'total_weight_net':picking_obj.weight,
            }
           
        invoice_obj.write(cr, uid, result , vals, context)  
        return result
  
    def _invoice_create_line(self, cr, uid, moves, journal_id, inv_type='out_invoice', context=None):
        invoice_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('stock.move')
        invoices = {}
        for move in moves:
            company = move.company_id
            origin = move.picking_id.name
            partner, user_id, currency_id = move_obj._get_master_data(cr, uid, move, company, context=context)

            key = (partner, currency_id, company.id, user_id)

            if key not in invoices:
                # Get account and payment terms
                invoice_vals = self._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
                invoice_id = self._create_invoice_from_picking(cr, uid, move.picking_id, invoice_vals, context=context)
                invoices[key] = invoice_id
                invoice = invoice_obj.browse(cr,uid,invoice_id,context=context)
                #Call to create invoice line for shipping
                invoice_line = self._prepare_shipping_invoice_line(cr, uid, move.picking_id, invoice, context=context)
                if invoice_line:
                    move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line, context=context)

            invoice_line_vals = move_obj._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
            invoice_line_vals['invoice_id'] = invoices[key]
            invoice_line_vals['origin'] = origin

            move_obj._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context=context)
            move_obj.write(cr, uid, move.id, {'invoice_state': 'invoiced'}, context=context)

        invoice_obj.button_compute(cr, uid, invoices.values(), context=context, set_total=(inv_type in ('in_invoice', 'in_refund')))
        return invoices.values()
    
    
    def _get_default_uom(self,cr,uid,c):
        uom_categ, uom_categ_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'product', 'product_uom_categ_kgm')
        return self.pool.get('product.uom').search(cr, uid, [('category_id', '=', uom_categ_id),('factor','=',1)])[0]
    _defaults = {
        'weight_uom_id': lambda self,cr,uid,c: self._get_default_uom(cr,uid,c)
    }

    def copy(self, cr, uid, id, default=None, context=None):
        default = dict(default or {},
            number_of_packages=0,
            carrier_tracking_ref=False,
            volume=0.0)
        return super(stock_picking, self).copy(cr, uid, id, default=default, context=context)



class stock_move(osv.osv):
    _inherit = 'stock.move'

    def _get_sale_order(self, cr, uid, ids, context=None):
        picking_ids = self.pool.get('stock.picking').search(cr, uid, [('sale_id', 'in', ids)])
        move_ids = self.pool.get('stock.move').search(cr, uid, [('picking_id', 'in', picking_ids)])
        return move_ids

    _columns = {
        'weight_uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True,readonly="1",help="Unit of Measure (Unit of Measure) is the unit of measurement for Weight",),
        'ship_service': fields.related('picking_id', 'sale_id', 'ship_service', string='Ship Service', type='char', size=128,
            store = {'sale.order': (_get_sale_order, ['ship_service'], -10)})
        }
    
stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: