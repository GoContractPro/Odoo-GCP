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
from tools.translate import _

class mrp_product_disassemble(osv.osv_memory):
    _name = "mrp.product.disassemble"
    _rec_name = 'product_id'
    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),
        'location_id': fields.many2one('stock.location', 'Location'),
        'qty_available': fields.float('Real Stock', readonly=True),
        'product_qty': fields.float('Quantity'),
        }
    _defaults = {
        'product_qty': lambda *a : 1.00,
        }

    def default_get(self, cr, uid, fields, context=None):
        res = super(mrp_product_disassemble, self).default_get(cr, uid, fields, context=context)
        if context.get('active_model', False) == 'product.product':
            res['product_id'] = context.get('active_id')
        return res

    def do_disassemble(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids, context=context)[0]
        if data.product_qty > data.qty_available:
            raise osv.except_osv(_("Not enough Product"), _("Not enough product to do disassamble."))
        mrp_data = {
            'disassemble' : True,
            'product_qty' : data.product_qty,
            'product_id' : data.product_id.id,
            'location_src_id' : data.location_id.id,
            'location_dest_id' : data.location_id.id,
            }
        disassemble_obj = self.pool.get('mrp.disassemble.location')
        production_obj = self.pool.get('mrp.production')
        finish_location_ids = disassemble_obj.search(cr, uid, [('type', '=', 'product')], context=context)
        if finish_location_ids:
            mrp_data['location_dest_id'] = disassemble_obj.browse(cr, uid, finish_location_ids, context=context)[0].location_id.id
        product_change_vals = production_obj.product_id_change(cr, uid, [], data.product_id.id, context=context)
        mrp_data.update(product_change_vals['value'])
        if not product_change_vals['value']['bom_id']:
            raise osv.except_osv(_("No BoM found"), _("Please configure a BoM for this product."))
        production_id = production_obj.create(cr, uid, mrp_data, context=context)
        wf_service = netsvc.LocalService('workflow')
        wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_confirm', cr)
        production_obj.force_production(cr, uid, [production_id])
        wf_service.trg_validate(uid, 'mrp.production', production_id, 'button_produce', cr)
        production = production_obj.browse(cr, uid, production_id, context=context)
        for move in production.move_lines:
            self.pool.get('stock.move').action_consume(cr, uid, [move.id], move.product_qty, move.location_id.id, context=context)

        production_obj.action_produce(cr, uid, production_id,data.product_qty, 'consume_produce', context=context)
        return {'type': 'ir.actions.act_window_close' }

    def onchange_product_id(self, cr, uid, ids, product_id, location_id, context=None):
        res = {}
        if context is None:
            context = {}
        if location_id and product_id:
            context['location'] = [location_id]
            product_obj = self.pool.get('product.product').browse(cr, uid, [product_id], context=context)[0]
            res['qty_available'] = product_obj.qty_available
        return {'value': res}

mrp_product_disassemble()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
