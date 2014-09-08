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

import netsvc
from osv import fields, osv

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'disassemble': fields.boolean('Disassemble'),                
        }
    _defaults = {
        'disassemble': False,
        }
    
    def action_produce(self, cr, uid, production_id, production_qty, production_mode, context=None):
        """ To produce final product based on production mode (consume/consume&produce).
        If Production mode is consume, all stock move lines of raw materials will be done/consumed.
        If Production mode is consume & produce, all stock move lines of raw materials will be done/consumed
        and stock move lines of final product will be also done/produced.
        @param production_id: the ID of mrp.production object
        @param production_qty: specify qty to produce
        @param production_mode: specify production mode (consume/consume&produce).
        @return: True
        """
        stock_mov_obj = self.pool.get('stock.move')
        production = self.browse(cr, uid, production_id, context=context)
        final_product_todo = []
        produced_qty = 0
        if production_mode == 'consume_produce':
            produced_qty = production_qty

        for produced_product in production.move_created_ids2:
            if (produced_product.scrapped) or (produced_product.product_id.id <> production.product_id.id):
                continue
            produced_qty += produced_product.product_qty
         
        if production_mode in ['consume', 'consume_produce']:
            consumed_products = {}
            check = {}
            scrapped = map(lambda x:x.scrapped, production.move_lines2).count(True)

            for consumed_product in production.move_lines2:
                consumed = consumed_product.product_qty
                if consumed_product.scrapped:
                    continue
                if not consumed_products.get(consumed_product.product_id.id, False):
                    consumed_products[consumed_product.product_id.id] = consumed_product.product_qty
                    check[consumed_product.product_id.id] = 0
                for f in production.product_lines:
                    if f.product_id.id == consumed_product.product_id.id:
                        if (len(production.move_lines2) - scrapped) > len(production.product_lines):
                            check[consumed_product.product_id.id] += consumed_product.product_qty
                            consumed = check[consumed_product.product_id.id]
                        rest_consumed = produced_qty * f.product_qty / production.product_qty - consumed
                        consumed_products[consumed_product.product_id.id] = rest_consumed

            for raw_product in production.move_lines:
                for f in production.product_lines:
                    if f.product_id.id == raw_product.product_id.id:
                        consumed_qty = consumed_products.get(raw_product.product_id.id, 0)
                        if consumed_qty == 0:
                            consumed_qty = production_qty * f.product_qty / production.product_qty
                        if consumed_qty > 0:
                            stock_mov_obj.action_consume(cr, uid, [raw_product.id], consumed_qty, production.location_src_id.id, context=context)

        if production_mode == 'consume_produce':
            # To produce remaining qty of final product
            vals = {'state': 'confirmed'}
            produced_products = {}
            for produced_product in production.move_created_ids2:
                if produced_product.scrapped:
                    continue
                if not produced_products.get(produced_product.product_id.id, False):
                    produced_products[produced_product.product_id.id] = 0
                produced_products[produced_product.product_id.id] += produced_product.product_qty

            for produce_product in production.move_created_ids:
                produced_qty = produced_products.get(produce_product.product_id.id, 0)
                rest_qty = production.product_qty - produced_qty
                if rest_qty <= production_qty:
                   production_qty = rest_qty
                if rest_qty > 0 :
                    if production.disassemble:                        
                        stock_mov_obj.action_consume(cr, uid, [produce_product.id], produce_product.product_qty - produced_qty, context=context)
                    else:
                        stock_mov_obj.action_consume(cr, uid, [produce_product.id], production_qty, context=context)

        for raw_product in production.move_lines2:
            new_parent_ids = []
            parent_move_ids = [x.id for x in raw_product.move_history_ids]
            for final_product in production.move_created_ids2:
                if final_product.id not in parent_move_ids:
                    new_parent_ids.append(final_product.id)
            for new_parent_id in new_parent_ids:
                stock_mov_obj.write(cr, uid, [raw_product.id], {'move_history_ids': [(4, new_parent_id)]})

        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce_done', cr)
        return True
    
    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms production order and calculates quantity based on subproduct_type.
        @return: Newly generated picking Id.
        """
        move_obj = self.pool.get('stock.move')
        picking_id = super(mrp_production, self).action_confirm(cr, uid, ids)
        for production in self.read(cr, uid, ids, ['move_created_ids', 'move_lines', 'disassemble'], context=context):
            if production['disassemble']:
                self.write(cr, uid, production['id'], {
                    'move_created_ids': [(6, 0, production['move_lines'])],
                    'move_lines': [(6, 0, production['move_created_ids'])]
                    }, context=context)
                
                move_lines_data = move_obj.read(cr, uid, production['move_lines'], ['location_id', 'location_dest_id'], context=context)
                move_created_ids_data = move_obj.read(cr, uid, production['move_created_ids'], ['location_id', 'location_dest_id'], context=context)
                if move_lines_data and move_created_ids_data:
                    move_obj.write(cr, uid, production['move_lines'], {
                        'location_id': move_created_ids_data[0]['location_id'][0],
                        'location_dest_id': move_created_ids_data[0]['location_dest_id'][0]
                        }, context=context)
                    move_obj.write(cr, uid, production['move_created_ids'], {
                        'location_id': move_lines_data[0]['location_id'][0],
                        'location_dest_id': move_lines_data[0]['location_dest_id'][0]
                        }, context=context)
        return picking_id
    
mrp_production()

class mrp_production2(osv.osv):
    _description = 'Production'
    _inherit= 'mrp.production'

    def action_confirm(self, cr, uid, ids, context=None):
        """ Confirms production order and calculates quantity based on subproduct_type.
        @return: Newly generated picking Id.
        """
        picking_id = super(mrp_production2, self).action_confirm(cr, uid, ids)
        for production in self.browse(cr, uid, ids, context=context):
            if production['disassemble']:
                for move in production.move_lines:
                    self.pool.get('stock.move').write(cr, uid, [move.id], {'location_id': production.location_src_id.id}, context=context)
        return picking_id

mrp_production2()

class mrp_disassemble_location(osv.osv):
    _name = 'mrp.disassemble.location'
    _description = "Locations for Finished products"    
    _rec_name = 'location_id'
    _columns = {
         'location_id': fields.many2one('stock.location', 'Finished Products Location', required=True),
         'type': fields.selection([('incoming_shipment', 'Incoming Shipments'), ('product', 'Delivered Products')],'Type', required=True)
          }
    
mrp_disassemble_location()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: