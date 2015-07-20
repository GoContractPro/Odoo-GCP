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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.addons.product import _common
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.tools import float_compare
from openerp.tools.translate import _
from openerp import tools, SUPERUSER_ID


class mrp_production_product_line(osv.osv):
    _inherit = 'mrp.production.product.line'
    _columns = {
        'bom_seq':fields.integer("BoM line Sequence"),
    }

class StockMove(osv.osv):
    _inherit = 'stock.move'

    _columns = {
        'bom_seq':fields.integer("BoM line Sequence"),
    }
    
    def _prepare_procurement_from_move(self, cr, uid, move, context=None):
        res = super(StockMove, self)._prepare_procurement_from_move(cr, uid, move, context=context)
        res.update({'bom_seq': move.bom_seq})
        return res


class mrp_bom(osv.osv):
    _inherit ='mrp.bom'
    
    def _bom_explode(self, cr, uid, bom, product, factor, properties=None, level=0, routing_id=False, previous_products=None, master_bom=None):
        """ Finds Products and Work Centers for related BoM for manufacturing order.
        @param bom: BoM of particular product template.
        @param product: Select a particular variant of the BoM. If False use BoM without variants.
        @param factor: Factor of product UoM.
        @param properties: A List of properties Ids.
        @param level: Depth level to find BoM lines starts from 10.
        @param previous_products: List of product previously use by bom explore to avoid recursion
        @param master_bom: When recursion, used to display the name of the master bom
        @return: result: List of dictionaries containing product details.
                 result2: List of dictionaries containing Work Center details.
        """
        routing_obj = self.pool.get('mrp.routing')
        all_prod = [] + (previous_products or [])
        master_bom = master_bom or bom

        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            if factor < product_rounding:
                factor = product_rounding
            return factor

        factor = _factor(factor, bom.product_efficiency, bom.product_rounding)

        result = []
        result2 = []

        routing = (routing_id and routing_obj.browse(cr, uid, routing_id)) or bom.routing_id or False
        if routing:
            for wc_use in routing.workcenter_lines:
                wc = wc_use.workcenter_id
                d, m = divmod(factor, wc_use.workcenter_id.capacity_per_cycle)
                mult = (d + (m and 1.0 or 0.0))
                cycle = mult * wc_use.cycle_nbr
                result2.append({
                    'name': tools.ustr(wc_use.name) + ' - ' + tools.ustr(bom.product_tmpl_id.name_get()[0][1]),
                    'workcenter_id': wc.id,
                    'sequence': level + (wc_use.sequence or 0),
                    'cycle': cycle,
                    'hour': float(wc_use.hour_nbr * mult + ((wc.time_start or 0.0) + (wc.time_stop or 0.0) + cycle * (wc.time_cycle or 0.0)) * (wc.time_efficiency or 1.0)),
                })

        for bom_line_id in bom.bom_line_ids:
            if bom_line_id.date_start and bom_line_id.date_start > time.strftime(DEFAULT_SERVER_DATETIME_FORMAT) or \
                bom_line_id.date_stop and bom_line_id.date_stop > time.strftime(DEFAULT_SERVER_DATETIME_FORMAT):
                    continue
            # check properties
            if set(map(int,bom_line_id.property_ids or [])) - set(properties or []):
                continue
            # all bom_line_id variant values must be in the product
            if bom_line_id.attribute_value_ids:
                if not product or (set(map(int,bom_line_id.attribute_value_ids or [])) - set(map(int,product.attribute_value_ids))):
                    continue

            if bom_line_id.product_id.id in all_prod:
                raise osv.except_osv(_('Invalid Action!'), _('BoM "%s" contains a BoM line with a product recursion: "%s".') % (master_bom.name,bom_line_id.product_id.name_get()[0][1]))
            all_prod.append(bom_line_id.product_id.id)
            
            if bom_line_id.type != "phantom":
                result.append({
                    'name': bom_line_id.product_id.name,
                    'product_id': bom_line_id.product_id.id,
                    'product_qty': _factor(bom_line_id.product_qty * factor, bom_line_id.product_efficiency, bom_line_id.product_rounding),
                    'product_uom': bom_line_id.product_uom.id,
                    'product_uos_qty': bom_line_id.product_uos and bom_line_id.product_uos_qty * factor or False,
                    'product_uos': bom_line_id.product_uos and bom_line_id.product_uos.id or False,
                    #Verts Added sequence field
                    'bom_seq' : bom_line_id.sequence,
                })
            else:
                bom_id = self._bom_find(cr, uid, bom_line_id.product_uom.id, product_id=bom_line_id.product_id.id, properties=properties)
                if bom_id:
                    bom2 = self.browse(cr, uid, bom_id)  
                    res = self._bom_explode(cr, uid, bom2, bom_line_id.product_id, factor,
                        properties=properties, level=level + 10, previous_products=all_prod, master_bom=master_bom)
                    result = result + res[0]
                    result2 = result2 + res[1]
                else:
                    raise osv.except_osv(_('Invalid Action!'), _('BoM "%s" contains a phantom BoM line but the product "%s" don\'t have any BoM defined.') % (master_bom.name,bom_line_id.product_id.name_get()[0][1]))

        return result, result2
    

class mrp_production(osv.osv):
    _inherit ='mrp.production'
    _order = 'name'
    _columns = {
        'production_id' : fields.many2one('mrp.production','Parent MO'),
#         'bom_seq' : fields.char('Reference',size=64),
    }
    
#     _defaults = {
#         'name': '/',
#     }

    def default_get(self, cr, uid, fields, context=None):
        res = super(mrp_production, self).default_get(cr, uid, fields, context)
        res ['name'] = '/'
        return res
    
    def create(self, cr, uid, default, context={}):
        seq = ''
        if not default.get('name') or default.get('name') == '/':
            default.update({'name': self.pool.get('ir.sequence').get(cr, uid, 'mrp.production.bom.seq') or '/'})
        return super(mrp_production, self).create(cr, uid, default, context=context)
    
    def _make_consume_line_from_data(self, cr, uid, production, product, uom_id, qty, uos_id, uos_qty, bom_seq, context=None):
        stock_move = self.pool.get('stock.move')
        # Internal shipment is created for Stockable and Consumer Products
        if product.type not in ('product', 'consu'):
            return False
        # Take routing location as a Source Location.
        source_location_id = production.location_src_id.id
        prod_location_id = source_location_id
        prev_move= False
        if production.bom_id.routing_id and production.bom_id.routing_id.location_id and production.bom_id.routing_id.location_id.id != source_location_id:
            source_location_id = production.bom_id.routing_id.location_id.id
            prev_move = True
            
        destination_location_id = production.product_id.property_stock_production.id
        move_id = stock_move.create(cr, uid, {
            'name': production.name,
            'date': production.date_planned,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': uom_id,
            'product_uos_qty': uos_id and uos_qty or False,
            'product_uos': uos_id or False,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'company_id': production.company_id.id,
            'procure_method': prev_move and 'make_to_stock' or self._get_raw_material_procure_method(cr, uid, product, context=context), #Make_to_stock avoids creating procurement
            'raw_material_production_id': production.id,
            #this saves us a browse in create()
            'price_unit': product.standard_price,
            'origin': production.name,
            'bom_seq':bom_seq,
        }, context=context)
        
        if prev_move:
            prev_move = self._create_previous_move(cr, uid, move_id, product, prod_location_id, source_location_id, context=context)
        return move_id    

    def _make_production_consume_line(self, cr, uid, line, context=None):
        return self._make_consume_line_from_data(cr, uid, line.production_id, line.product_id, line.product_uom.id, line.product_qty, line.product_uos.id, line.product_uos_qty, line.bom_seq, context=context)

    
class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    
    _columns = {
                'bom_seq':fields.integer("BoM line Sequence"),
                }
     
    def make_mo(self, cr, uid, ids, context={}):
        """ Make Manufacturing(production) order from procurement
        @return: New created Production Orders procurement wise
        """
        res = {}
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        production_obj = self.pool.get('mrp.production')
        bom_obj = self.pool.get('mrp.bom')
        procurement_obj = self.pool.get('procurement.order')
        for procurement in procurement_obj.browse(cr, uid, ids, context=context):
            if self.check_bom_exists(cr, uid, [procurement.id], context=context):
                if procurement.bom_id:
                    bom_id = procurement.bom_id.id
                    routing_id = procurement.bom_id.routing_id.id
                else:
                    properties = [x.id for x in procurement.property_ids]
                    bom_id = bom_obj._bom_find(cr, uid, procurement.product_uom.id,
                        product_id=procurement.product_id.id, properties=properties)
                    bom = bom_obj.browse(cr, uid, bom_id, context=context)
                    routing_id = bom.routing_id.id

                res_id = procurement.move_dest_id and procurement.move_dest_id.id or False
                newdate = datetime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - relativedelta(days=procurement.product_id.produce_delay or 0.0)
                newdate = newdate - relativedelta(days=company.manufacturing_lead)
                #create the MO as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
                sequence_number =  procurement.move_dest_id and procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.name or ''
                #if procurement.move_dest_id and procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.id :
                produce_id = production_obj.create(cr, SUPERUSER_ID, {
                    'origin': procurement.origin,
                    'product_id': procurement.product_id.id,
                    'product_qty': procurement.product_qty,
                    'product_uom': procurement.product_uom.id,
                    'product_uos_qty': procurement.product_uos and procurement.product_uos_qty or False,
                    'product_uos': procurement.product_uos and procurement.product_uos.id or False,
                    'location_src_id': procurement.location_id.id,
                    'location_dest_id': procurement.location_id.id,
                    'bom_id': bom_id,
                    'routing_id': routing_id,
                    'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                    'move_prod_id': res_id,
                    'company_id': procurement.company_id.id,
                    'production_id':procurement.move_dest_id and procurement.move_dest_id.raw_material_production_id and procurement.move_dest_id.raw_material_production_id.id or False,
                    'name':sequence_number + (procurement.bom_seq and ('-' + str(procurement.bom_seq)) or '')
                })
                
                res[procurement.id] = produce_id
                self.write(cr, uid, [procurement.id], {'production_id': produce_id})
                procurement.refresh()
                self.production_order_create_note(cr, uid, procurement, context=context)
                production_obj.action_compute(cr, uid, [produce_id], properties=[x.id for x in procurement.property_ids])
                production_obj.signal_workflow(cr, uid, [produce_id], 'button_confirm')
            else:
                res[procurement.id] = False
                self.message_post(cr, uid, [procurement.id], body=_("No BoM exists for this product!"), context=context)
        return res

    