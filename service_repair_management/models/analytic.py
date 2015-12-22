###############################################################################################
#Make sure the copyright information is correct (Copyright (C) 2011 NovaPoint Group LLC 
#(<http://www.novapointgroup.com>) and placed on top of OpenERP certification line and reflects
# Novapoint Group, Inc as the author 
#
#################################################################################################
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
from openerp.osv import osv,fields

class account_analytic_account(osv.osv):
    _inherit='account.analytic.account'
    
    def _get_pricelist_id(self, cr, uid, context=None):
        pricelist_id =False
        partner_obj = self.pool.get('res.partner')
        if context.get('default_is_service_repair',False)== True and context.get('partner_id',False):
            pricelist = partner_obj.browse(cr, uid, context.get('partner_id',False))
            pricelist_id = pricelist.property_product_pricelist and pricelist.property_product_pricelist.id or False
        return pricelist_id
    
    _defaults={
               'pricelist_id':_get_pricelist_id,
               }
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(account_analytic_account, self).default_get(cr, uid, fields, context=context)
        to_invoice = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_timesheet_invoice', 'timesheet_invoice_factor1')
        res.update({'to_invoice':to_invoice[1]})
        return res

account_analytic_account()
    
class account_analytic_line(osv.osv):
    _inherit = 'account.analytic.line'
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(account_analytic_line, self).default_get(cr, uid, fields, context=context)
        to_invoice = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'hr_timesheet_invoice', 'timesheet_invoice_factor1')
        res.update({'to_invoice':to_invoice[1]})
        return res
    
account_analytic_line()