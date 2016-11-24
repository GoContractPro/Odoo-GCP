# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.verts.co.in>)
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
from xml.dom.minidom import Document
import xml2dic
from openerp.tools.translate import _
import httplib

class delete_payment_profile(osv.TransientModel):
    _name = 'delete.payment.profile'
    _description = 'Delete Payment Profile'
    
    def del_pay_profile(self, cr, uid, ids, context=None):
        parent_model = context.get('active_model')
        parent_id = context.get('active_id')
        if parent_model == 'res.partner':
            partner = self.pool.get(parent_model).browse(parent_id)
        else:
            parent_model_obj = self.pool.get(parent_model).browse(cr, uid, parent_id, context=context)
            partner = parent_model_obj.partner_id

        data = self.pool.get('delete.payment.profile').browse(cr, uid, ids[0])
        partner.delete_customer_payment_profile(data.payment_profile_id)
    
        return True

    def _get_profile_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('active_model') == 'cust.payment.profile':
            return context.get('active_id')
        return None

    _columns = {
        'payment_profile_id':fields.many2one('cust.payment.profile', 'Payment Profile'),
        }
    _defaults = {
        'payment_profile_id':_get_profile_id
    }
