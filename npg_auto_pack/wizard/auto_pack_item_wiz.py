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

from openerp.osv import orm, fields, osv

class auto_pack_items_edi(orm.TransientModel):
    
    _name = 'auto.pack.items.edi'
    _description = 'EDI Auto-Pack Items'

    _columns = {
    }

    def split(self, cr, uid, data, context=None):
        if context is None:
            context = {}
            
#         inventory_id = context.get('inventory_id', False)
        rec_id = context and context.get('active_id', False)
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        track_obj = self.pool.get('stock.tracking')
        inventory_obj = self.pool.get('stock.inventory')
#         quantity = self.browse(cr, uid, data[0], context=context).quantity or 0.0
        for move in picking_obj.browse(cr, uid, rec_id, context=context).move_lines:
            case_pack_qty = move.product_id.case_pack or 0.0
            if not case_pack_qty:
                continue
            
            if move.product_qty < case_pack_qty:
                continue
            tracking_id = False
            #Editing the current move with qty
#             move_obj.setlast_tracking(cr, uid, [move.id], context=context)
            write_vals = {
                  'product_qty': case_pack_qty,
                  'product_uos_qty': case_pack_qty,
                  'product_uos': move.product_uom.id,
            }

            if not move.tracking_id.id:
                tracking_id = track_obj.create(cr, uid, {}, context=context)
                write_vals.update({'tracking_id': tracking_id})
            move_obj.write(cr, uid, [move.id], write_vals)
            
            #Deducting first and time and processing.
            quantity_rest =  move.product_qty - case_pack_qty

            while quantity_rest:
                quantity_process = quantity_rest - min(case_pack_qty,quantity_rest)
                tracking_id = track_obj.create(cr, uid, {}, context=context)

                default_val = {
                        'product_qty': quantity_rest,
                        'product_uos_qty': quantity_rest,
                        'tracking_id': tracking_id,
                        'state': move.state,
                        'product_uos': move.product_uom.id
                }

                #process case_pack_qty
                if quantity_process:
                    default_val.update({
                        'product_qty': case_pack_qty,
                        'product_uos_qty': case_pack_qty,
                    })
                current_move = move_obj.copy(cr, uid, move.id, default_val, context=context)
#                 move_obj.write(cr, uid, [current_move], {'tracking_id': tracking_id}, context=context)
                quantity_rest = quantity_process

        return {'type': 'ir.actions.act_window_close'}
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: