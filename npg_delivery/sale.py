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
# from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp import api, fields, models, _

# Overloaded sale_order to manage carriers :
class sale_order(models.Model):
    _inherit = 'sale.order'
    
    def _get_company_code(self):
        return [('grid', 'Price Grid')]
    
    def _make_invoice(self, order, lines):
        inv_id = super(sale_order, self)._make_invoice(order,lines)
        if inv_id:
            if self.ship_income_account_id:
                inv_obj = self.env['account.invoice']
                inv_obj.write(inv_id, {
                    'shipcharge': order.shipcharge,
                    'ship_service': order.ship_service,
                    'ship_income_account_id': order.ship_income_account_id.id,
                    'sale_order': order.id ,
                    })
        return inv_id

    @api.multi
    def _amount_shipment_tax(self, shipment_taxes, shipment_charge):
        val = 0.0
        for c in self.env['account.tax'].compute_all(shipment_taxes, shipment_charge, 1)['taxes']:
            val += c.get('amount', 0.0)
        return val

#TODO Taxes currently not calculated for Shipping, Tax ids have not been defined and would need to be added to the Delivery Carrier shipping methods    
#     def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
#         cur_obj = self.pool.get('res.currency')
#         res = super(sale_order, self)._amount_all(cr, uid, ids, field_name, arg, context=context)
#         for order in self.browse(cr, uid, ids, context=context):
#             cur = order.pricelist_id.currency_id
#             tax_ids =[]# order.ship_method_id and order.ship_method_id.shipment_tax_ids
#             if tax_ids:
#                 val = self._amount_shipment_tax(tax_ids, order.shipcharge)
#                 res[order.id]['amount_tax'] += cur_obj.round(cr, uid, cur, val)
#                 res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + order.shipcharge
#             elif order.shipcharge:
#                 res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + order.shipcharge
#         return res
    
    

    
    def _get_address_validation_method(self):
        user = self.env.user
        return user and user.company_id and user.company_id.address_validation_method
    
    @api.multi
    def _validated(self):
        for sale_order in self:
            if sale_order.partner_invoice_id.last_address_validation and sale_order.partner_order_id.last_address_validation and sale_order.partner_shipping_id.last_address_validation:
                sale_order.update({'hide_validate': True})
            else:
                sale_order.update({'hide_validate': False})
    
    def _method_get(self):
        return [("none", "None")]

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", help="The Delivery service Choices defined for Transport or Logistics Company")
    carrier_contact = fields.Many2one("res.partner", string="Carrier Contact", help="Contact Info for Carrier  responsible for Shipping")
    transport_id = fields.Many2one("res.partner", string="Transport N/A", help="Contact Info for Carrier  responsible for Shipping")
    shipcharge = fields.Float('Shipping Charges')
    shipcost = fields.Float('Shipping Charges')
    ship_service = fields.Char('Ship Service', size=128, readonly=True)
    ship_company_code = fields.Selection(_get_company_code, string ='Ship Company')
    sale_account_id = fields.Many2one('account.account', string='Ship Income Account',
                                           help='This account represents the g/l account for booking shipping income.')
        
    ship_income_account_id = fields.Many2one('account.account', string='Ship Income Account',
                                           help='This account represents the g/l account for booking shipping income.')
        
#     amount_untaxed = fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Untaxed Amount',
#             store = {
#                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'shipcharge'], 10),
#                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
#                },
#                multi='sums', help="The amount without tax."),
#         'amount_tax': fields.function(_amount_all, method=True, digits_compute=dp.get_precision('Sale Price'), string='Taxes',
#             store = {
#                 'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line',  'shipcharge'], 10),
#                 'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
#                 },
#                 multi='sums', help="The tax amount."),
#         'amount_total': fields.function(_amount_all, method=True, digits_compute= dp.get_precision('Sale Price'), string='Total',
#             store = {
#                 'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'shipcharge'], 10),
#                 'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
#                 },
#                  multi='sums', help="The total amount."),
#                  
        # From partner address validation module.
      
    hide_validate = fields.Boolean(string='Hide Validate',compute='_validated')
    address_validation_method = fields.Selection(_method_get, string='Address Validation Method',default=_get_address_validation_method)
    
    
#     def create(self, cr, uid, vals, context=None):
#         if vals.get('name','/')=='/':
#             vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'sale.order') or '/'
#         if vals.has_key('carrier_id') and vals['carrier_id']:
#             carrier_id =vals['carrier_id']
#             carrier_obj = self.pool.get('delivery.carrier').browse(cr, uid, carrier_id, context=context)
#             vals['carrier_contact']=carrier_obj.partner_id.id
#             vals['ship_service']=carrier_obj.name
# #         if vals.has_key('ups_shipper_id') and vals['ups_shipper_id']:
# #             ups_shipper_id =vals['ups_shipper_id']
# #             ups_shipper_id_obj = self.pool.get('ups.account.shipping').browse(cr, uid, ups_shipper_id, context=context)
# #             vals['carrier_contact']=ups_shipper_id_obj.partner_id.id
#         return super(sale_order, self).create(cr, uid, vals, context=context)
#     
#     def write(self, cr, uid,ids, vals, context=None):
#         if vals.has_key('carrier_id') and vals['carrier_id']:
#             carrier_id =vals['carrier_id']
#             carrier_obj = self.pool.get('delivery.carrier').browse(cr, uid, carrier_id, context=context)
#             vals['carrier_contact']=carrier_obj.partner_id.id
#             vals['ship_service']=carrier_obj.name
# #         if vals.has_key('ups_shipper_id') and vals['ups_shipper_id']:
# #             ups_shipper_id =vals['ups_shipper_id']
# #             ups_shipper_id_obj = self.pool.get('ups.account.shipping').browse(cr, uid, ups_shipper_id, context=context)
# #             vals['carrier_contact']=ups_shipper_id_obj.partner_id.id
#         return super(sale_order, self).write(cr, uid,ids, vals, context=context)

    @api.onchange('carrier_id')
    def onchange_carrier_id(self):
        if not self.carrier_id:
            self.update({
                'carrier_contact': False,
                'ship_service': False,
                'ship_income_account_id': False,
                'ship_company_code':False
            })
            return
        self.update({'carrier_contact' : self.carrier_id.partner_id.id,
                     'ship_company_code':self.carrier_id.ship_company_code,
                        'ship_service' : self.carrier_id.name,
                        'ship_income_account_id':self.carrier_id.ship_income_account_id and self.carrier_id.ship_income_account_id.id or False})
    
#     def action_ship_create(self, cr, uid, ids, context=None):
#         pick_obj = self.pool.get("stock.picking")
#         ret = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
#         for sale_obj in self.browse(cr, uid, ids, context=context):
#             pick_obj.write(cr, uid, [x.id for x in sale_obj.picking_ids], {'carrier_id': sale_obj.carrier_id and sale_obj.carrier_id.id or False,
#                                                                             'ship_income_account_id':sale_obj.ship_income_account_id and sale_obj.ship_income_account_id.id or False,
#                                                                             'carrier_contact':sale_obj.carrier_contact and sale_obj.carrier_contact.id or False,
#                                                                             'shipcharge':sale_obj.shipcharge or False,
#                                                                             'ship_service':sale_obj.ship_service or False,
#                                                                             },
#                                                                              context=context)
#                     
#         return ret
#     
#     def delivery_set(self, cr, uid, ids, context=None):
#         order_obj = self.pool.get('sale.order')
#         grid_obj = self.pool.get('delivery.grid')
#         carrier_obj = self.pool.get('delivery.carrier')
#         for order in self.browse(cr, uid, ids, context=context):
#             grid_id = carrier_obj.grid_get(cr, uid, [order.carrier_id.id], order.partner_shipping_id.id)
#             if not grid_id:
#                 raise osv.except_osv(_('No Grid Available!'), _('No grid matching for this carrier!'))
# 
#             if not order.state in ('draft', 'sent'):
#                 raise osv.except_osv(_('Order not in Draft State!'), _('The order state have to be draft to add delivery lines.'))
# 
#             grid = grid_obj.browse(cr, uid, grid_id, context=context)
#             price_unit= grid_obj.get_price_sale(cr, uid, grid.id, order, time.strftime('%Y-%m-%d'), context)
#             order_obj.write(cr,uid,ids,{'ship_service':order.carrier_id.name,'shipcharge':price_unit})
#         return True
    
    def action_invoice_create(self, grouped=False, final=False):
        inv_id = super(sale_order, self).action_invoice_create(grouped, final)
        for so in self:
            vals = {'carrier_contact':so.carrier_contact.id or False,
                  'carrier_id':so.carrier_id.id or False,
                  'ship_service': so.ship_service or False,
                  }
                
            self.env['account.invoice'].write(inv_id,vals)
        return inv_id

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: