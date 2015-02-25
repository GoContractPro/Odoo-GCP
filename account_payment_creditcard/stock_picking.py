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

class stock_picking(osv.Model):

    _inherit = "stock.picking"
    '''
    Adding credit card preauthorised and payed check box on delivery order
    '''
    def _get_sale_order(self, cr, uid, ids, context={}):
        result = []
        move_ids = []
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        for id in ids:
            stock_pick_ids = picking_obj.search(cr, uid, [('sale_id', '=', id)])
            if stock_pick_ids:
                move_ids += move_obj.search(cr, uid, [('picking_id', 'in', stock_pick_ids)])
        move_ids = list(set(move_ids))
        return move_ids
    
    def __get_invoice_state(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for pick in self.browse(cr, uid, ids, context=context):
            result[pick.id] = 'none'
            for move in pick.move_lines:
                if move.invoice_state == 'invoiced':
                    result[pick.id] = 'invoiced'
                elif move.invoice_state == 'credit_card': 
                     result[pick.id] = 'credit_card'  
                elif move.invoice_state == '2binvoiced':
                    result[pick.id] = '2binvoiced'
                    break
        return result

    def __get_picking_move(self, cr, uid, ids, context={}):
        res = []
        for move in self.pool.get('stock.move').browse(cr, uid, ids, context=context):
            if move.picking_id:
                res.append(move.picking_id.id)
        return res
    
    def _set_inv_state(self, cr, uid, picking_id, name, value, arg, context=None):
        pick = self.browse(cr, uid, picking_id, context=context)
        moves = [x.id for x in pick.move_lines]
        move_obj= self.pool.get("stock.move")
        move_obj.write(cr, uid, moves, {'invoice_state': value}, context=context)
    
    _columns = {
        'cc_pre_auth':  fields.related('sale_id', 'cc_pre_auth', string='CC Pre-authorised', type='boolean'),
        'invoiced':  fields.related('sale_id', 'invoiced', string='Paid', type='boolean'),
        'invoice_state': fields.function(__get_invoice_state, type='selection', selection=[
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable"),
            ("credit_card", "Credit Card"),
            ("cc_refund", "Credit Card Refund")
          ], string="Invoice Control", required=True,
        fnct_inv = _set_inv_state,
        store={
            'stock.picking': (lambda self, cr, uid, ids, c={}: ids, ['state'], 10),
            'stock.move': (__get_picking_move, ['picking_id', 'invoice_state'], 10),
        },
        ),
        'ship_state': fields.selection([
            ('draft', 'Draft'),
            ('in_process', 'In Process'),
            ('ready_pick', 'Ready for Pickup'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('void', 'Void'),
            ('hold', 'Hold'),
            ('cancelled', 'Cancelled')
            ], 'Shipping Status', readonly=True, help='The current status of the shipment'),
        'ship_message': fields.text('Message'),
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
class stock_move(osv.Model):
    _inherit = "stock.move"
    _columns = {
        'invoice_state': fields.selection([
            ("invoiced", "Invoiced"),
            ("2binvoiced", "To Be Invoiced"),
            ("none", "Not Applicable"),
            ("credit_card", "Credit Card"),
            ("cc_refund", "Credit Card Refund")
            ], "Invoice Control", select=True, required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }

    