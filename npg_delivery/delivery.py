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
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp



class delivery_method(osv.osv):
    _name = "delivery.method"
    _description = "Delivery Type"
    
    def _get_company_code(self, cr, user, context=None):
        return [('grid', 'Price Grid')]
    
    _columns = {
        'name': fields.char('Delivery Type', size=24, required=True),
        'description': fields.char('Description', size=64),
        'ship_company_code': fields.selection(_get_company_code, 'Method Type', method=True,size=64),
        'active': fields.boolean('Active', 
                 help="If the active field is set to False, it will allow you to hide the delivery method without removing it."),
        'delivery_carriers': fields.many2many('delivery.carrier', 'delivery_method_delivery_carrier', 'del_id', 'carier_id', 'Delivery Carrier'),
        'ship_income_account_id': fields.property(type='many2one',relation='account.account', string="Shipping Income GL Account",view_load=True,
                                required=True, help='This account represents the g/l account for booking shipping income.'),
        'invoice_ship_act_cost': fields.boolean('Invoice on Actual Costs', help = 'Invoice using actual shipping costs from packages not using quoted ship charges as quoted on Sales Order')
     }
       
    _defaults = {
        'active':  1,}
    
    def onchange_delivery_method(self,cr,uid,ids, delivery_method, context = None):
        
        if delivery_method:
            delivery_obj = self.pool('delivery.method').browse(cr,uid,delivery_method,context = context)
            
            carrier_ids = (delivery_obj.delivery_carriers and delivery_obj.delivery_carriers.ids) or []
            account = delivery_obj.ship_income_account_id and delivery_obj.ship_income_account_id.id
            res = {'value': {'carrier_id':False,
                         'carrier_contact':False,
                         'ship_service':False,
                         'ship_income_account_id':account},
                   'domain':{'carrier_id':[('id','in',carrier_ids)]}
                   }
               
        else: 
            res = {'value':{'ship_income_account_id':False,
                             'carrier_id':False,
                             'carrier_contact':False,
                             'ship_service':False,},
                   'domain':{'carrier_id':[('id','in',[])]}
                   }
        return res
 


class delivery_carrier(osv.osv):
    _inherit = "delivery.carrier"


    _columns = {
        'name': fields.char('Delivery Carrier', size=64, required=True),
        'partner_id': fields.many2one('res.partner', 'Delivery Company', required=True, help="The partner who is doing the delivery service."),
        'grids_id': fields.one2many('delivery.grid', 'carrier_id', 'Delivery Service Grids'),

    }

    _defaults = {
        'active': 1,
        'free_if_more_than': False,
    }

    
    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context is None:
            context = {}
        results =[]
        
        if context.get('delivery_method', False):
            id = context.get('delivery_method')
            method_obj = self.pool.get('delivery.method').browse(cr,uid,[id], context = context)
            
            for rec in method_obj:
               
                ids = [x.id for x in rec.delivery_carriers]
                args += [('id', 'in', ids)]
    

        return super(delivery_carrier, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)
        
    def name_search(self, cr, uid, name='', args=None, operator='ilike', context=None, limit=100):
        
        if not args:
            args = []
            
        if context.get('delivery_method', False):
            id = context.get('delivery_method')
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            
            method_obj = self.pool.get('delivery.method').browse(cr,uid,[id], context = context)
            
            for rec in method_obj:
                
                ids = [x.id for x in rec.delivery_carriers]
                args += [('id', 'in', ids)]
    
            ids = []
            if operator in positive_operators:
                ids = self.search(cr, uid, [('name',operator,name)]+ args, limit=limit, context=context)
            ids = self.search(cr, uid, args, limit=limit, context=context)
            result = self.name_get(cr, uid, ids, context=context) 
            return result  
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
            return self.name_get(cr, uid, ids, context=context)



