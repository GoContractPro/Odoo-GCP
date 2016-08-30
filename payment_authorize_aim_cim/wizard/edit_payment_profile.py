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
import httplib
from xml.dom.minidom import Document
import xml2dic
from openerp.tools.translate import _

class edit_payment_profile(osv.TransientModel):
    _name = 'edit.payment.profile'
    _description = 'Edit Payment Profile'

    def _get_partner(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('active_id', False)

    def _get_state(self, cr, uid, context=None):
        if context.get('active_model', False) == 'cust.payment.profile':
            if context.get('active_id',False):
                edit_profile_id = self.search(cr,uid,[('payment_profile_id','=',context.get('active_id',False))])
                if edit_profile_id:
                    state = self.browse(cr,uid,edit_profile_id[0]).state
                    return state
                return 'preprocessing'
        return 'draft'
    
    
    def _get_cc_number(self, cr, uid, context=None):
        if context.get('active_model', False) == 'cust.payment.profile':
            if context.get('active_id',False):
                edit_profile_id = self.search(cr,uid,[('payment_profile_id','=',context.get('active_id',False))])
                if edit_profile_id:
                    cc_number = self.browse(cr,uid,edit_profile_id[0]).cc_number
                    return cc_number
                return ''
        return ''
    
    def _get_cc_ed_month(self, cr, uid, context=None):
        if context.get('active_model', False) == 'cust.payment.profile':
            if context.get('active_id',False):
                edit_profile_id = self.search(cr,uid,[('payment_profile_id','=',context.get('active_id',False))])
                if edit_profile_id:
                    cc_ed_month = self.browse(cr,uid,edit_profile_id[0]).cc_ed_month
                    return cc_ed_month
                return ''
        return ''


    def _get_cc_ed_year(self, cr, uid, context=None):
        if context.get('active_model', False) == 'cust.payment.profile':
            if context.get('active_id',False):
                edit_profile_id = self.search(cr,uid,[('payment_profile_id','=',context.get('active_id',False))])
                if edit_profile_id:
                    cc_ed_year = self.browse(cr,uid,edit_profile_id[0]).cc_ed_year
                    return cc_ed_year
                return ''
        return ''


    def _get_cc_code(self, cr, uid, context=None):
        if context.get('active_model', False) == 'cust.payment.profile':
            if context.get('active_id',False):
                edit_profile_id = self.search(cr,uid,[('payment_profile_id','=',context.get('active_id',False))])
                if edit_profile_id:
                    cc_code = self.browse(cr,uid,edit_profile_id[0]).cc_code
                    return cc_code
                return ''
        return ''

    def _get_profile_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context['active_model'] == 'cust.payment.profile':
            return context.get('active_id')
        return None

    _columns = {
        'payment_profile_id':fields.many2one('cust.payment.profile', 'Payment Profile', required=True),
        'partner_id':fields.many2one('res.partner', 'Customer', required=True),
        'cc_number':fields.char('Credit Card Number', size=32),
        'cc_ed_month':fields.char('Expiration Date MM', size=32),
        'cc_ed_year':fields.char('Expiration Date YYYY', size=32),
        'cc_code':fields.char('Card Code', size=32),
        'state':fields.selection(
            [('draft', 'Draft'),
             ('done', 'Done'),
             ('processing', 'Processing'),
             ('preprocessing', 'PreProcessing'),
            ], 'State', readonly=True, size=32)
    }

    _defaults = {
        'partner_id': _get_partner,
        'state':'draft',
#         'cc_number':_get_cc_number,
#         'cc_ed_month':_get_cc_ed_month,
#         'cc_ed_year':_get_cc_ed_year,
#         'cc_cc_code':_get_cc_code,
        'payment_profile_id':_get_profile_id
        }



    def search_dic(self, dic, key):
        ''' Returns the parent dictionary containing key None on Faliure'''
        if key in dic.keys():
            return dic
        for k in dic.keys():
            if type(dic[k]) == type([]):
                for i in dic[k]:
                    if type(i) == type({}):
                        ret = self.search_dic(i, key)
                        if ret and key in ret.keys():
                            return ret
        return None

    def _clean_string(self, text):
        lis = ['\t', '\n']
        if type(text) != type(''):
            text = str(text)
        for t in lis:
            text = text.replace(t, '')
        return text

    def _setparameter(self, dic, key, value):
        ''' Used to input parameters to corresponding dictionary'''
        if key == None or value == None :
            return
        if type(value) == type(''):
            dic[key] = value.strip()
        else:
            dic[key] = value
            
    def get_payment_profile_info(self, cr, uid, ids, context=None):
        parent_model = context.get('active_model')
        parent_id = context.get('active_id')
        data = self.browse(cr, uid, ids[0])
        if parent_model == 'res.partner':
            partner = self.pool.get(parent_model).browse(cr, uid, parent_id)
        else:
            parent_model_obj = self.pool.get(parent_model).browse(cr, uid, parent_id)
            partner = parent_model_obj.partner_id
            
        customerPaymentProfileId = data.payment_profile_id
        
        existing_profile = partner.read_customer_payment_profile(customerPaymentProfileId)
        
        vals = {
                'state': 'processing',
                'cc_number' : existing_profile.get('cardNumber'),
                'cc_ed_year' : existing_profile.get('expirationDate'),
                'cc_code' : existing_profile.get('cardCode'),
                }
        print vals
        self.write(cr, uid, [data.id], vals)
        return {
                'name': _('Edit Payment Profile'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'edit.payment.profile',
#                 'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox').id,
                'type': 'ir.actions.act_window',
                'res_id': data.id,
                'context': context,
                'target': 'new'
            }
        
        



    def update_payment_profile_info(self, cr, uid, ids, context=None):
        Param_Dic = {}
        parent_model = context.get('active_model')
        parent_id = context.get('active_id')
        data = self.browse(cr, uid, ids[0])
        if parent_model == 'res.partner':
            partner = self.pool.get(parent_model).browse(cr, uid, parent_id)
        else:
            parent_model_obj = self.pool.get(parent_model).browse(cr, uid, parent_id)
            partner = parent_model_obj.partner_id

        cardNumber = data.cc_number or ''
        expirationDate = ''
        if data.cc_ed_year and data.cc_ed_month:
            expirationDate = data.cc_ed_year + '-' + data.cc_ed_month
        cardCode = data.cc_code or ''

        customerPaymentProfileId = data.payment_profile_id

        self._setparameter(Param_Dic, 'cardNumber', cardNumber)
        self._setparameter(Param_Dic, 'expirationDate', expirationDate)
        if cardCode:
            self._setparameter(Param_Dic, 'cardCode', cardCode)
        if partner:
            self._setparameter(Param_Dic, 'firstName', partner.name or '')
            self._setparameter(Param_Dic, 'zip', partner.zip or '')
            self._setparameter(Param_Dic, 'country', partner.country_id.name or '')
            self._setparameter(Param_Dic, 'phoneNumber', partner.phone or '')
            self._setparameter(Param_Dic, 'faxNumber', partner.fax or '')
            self._setparameter(Param_Dic, 'email', partner.email or '')
            self._setparameter(Param_Dic, 'customerType', 'individual' or '')

        profile = partner.update_customer_payment_profile(customerPaymentProfileId,Param_Dic)

        return{}
