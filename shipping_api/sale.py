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

class sale_order(osv.osv):
    _inherit = 'sale.order'
    
    _columns= {
        
        'partner_order_id': fields.many2one('res.partner', 'Ordering Contact', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="The name and address of the contact who requested the order or quotation."),
    }

    _defaults = {
        'partner_order_id': lambda self, cr, uid, context: context.get('partner_id', False) and self.pool.get('res.partner').address_get(cr, uid, [context['partner_id']], ['order_contact'])['order_contact'],
    }

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        addr = {}
        if part:
            addr = super(sale_order, self).onchange_partner_id(cr, uid, ids, part, context)
            addr['value'].update({'partner_order_id': part})
        return addr

sale_order()


