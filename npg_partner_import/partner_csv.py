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
from openerp import tools
from openerp.tools.translate import _
import csv
import cStringIO
import base64
from datetime import datetime
import time

import logging
import sys

_logger = logging.getLogger(__name__)

HEADER_MAP = {
#                'sequence'  : 'Reference',    this field is only used for AGS Partner Sequence      
                'name'      : 'Name',
                'street'    : 'Street',
                'street2'   : 'Street2',
                'city'      : 'City',
                'country_code': 'Country/Country Code',
                'state_code': 'State/State Code',
                'zip'       : 'Zip',
                'type'      : 'Address Type',
                'phone'     : 'Phone',
                'fax'       : 'Fax',
                'mobile'    : 'Mobile',
                'email'     : 'Email',
                'website'   : 'Website',
                'is_company': 'Is a Company',
                'supplier'  : 'Supplier',
                'customer'  : 'Customer',
                'employee'  : 'Employee',
                'related_company'   : 'Related Company/Name',
                'property_payment_term' : 'Customer Payment Term/Payment Term',
                'credit_limit': 'Credit Limit',
                'debit_limit'   : 'Payable Limit',
                'ref'       : 'Reference',
                'comment'   : 'Notes',
            }


def index_get(L, i, v=None):
    try: return L.index(i)
    except: return v

class partner_csv(osv.osv):
    _name = 'import.partner.csv'
    _columns = {
        'name':fields.char('Started',size=10, readonly=True),
        'end_time': fields.datetime('End',  readonly=True),
        'browse_path': fields.binary('Csv File Path', required=True),
        'error_log': fields.text('Error Log'),
        'test_sample_size': fields.integer('Test Sample Size'),
        'do_update': fields.boolean('Allow Update', 
                help='If Set when  matching unique fields on records will update values for record, Otherwise will just log duplicate and skip this record '),
        'field_map' : fields.text ('Field Map', readonly = True),
        }
    
    
     
    _defaults = {
        'test_sample_size':20,
        'field_map' : HEADER_MAP
        
        }
    
    
    def check_expected_headers(self, cr, uid, ids, context=None):
         
        # Mapp Odoo Fields to  CSVColumns
        
        if context is None:
            context = {}
        for wiz_rec in self.browse(cr, uid, ids, context=context):
            
            str_data = base64.decodestring(wiz_rec.browse_path)
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                partner_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            headers_list = []
            headers_dict ={}
            
            for header in partner_data[0]:
                headers_list.append(header.strip())
             
            msg = 'Csv Column position in not listed then column not found on CSV file \n\n Odoo field \t CSV Column  \t Position \n'   
            for field, column in HEADER_MAP.iteritems():
                
                headers_dict[field] = index_get(headers_list,column)
                msg += field + '\t' + column + '\t' + headers_dict[field] or ''
                
        popup_obj = self.pool.get( 'warning.warning')
        return popup_obj.info(cr, uid, title='CSV Map ', message = msg)
        
    
    
    def import_csv(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        start = time.strftime('%Y-%m-%d %H:%M:%S')       
        if context is None:
            context = {}
        for wiz_rec in self.browse(cr, uid, ids, context=context):
            
            str_data = base64.decodestring(wiz_rec.browse_path)
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                partner_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            

            headers_list = []
            for header in partner_data[0]:
                headers_list.append(header.strip())
            headers_dict = {
                'sequence' : index_get(headers_list,'Reference'),         
                'name'      : index_get(headers_list,'Name'),
                'street'    : index_get(headers_list,'Street'),
                'street2'   : index_get(headers_list,'Street2'),
                'city'      : index_get(headers_list,'City'),
                'country_code': index_get(headers_list,'Country/Country Code'),
                'state_code': index_get(headers_list,'State/State Code'),
                'zip'       : index_get(headers_list,'Zip'),
                'type'      : index_get(headers_list,'Address Type'),
                'phone'     : index_get(headers_list,'Phone'),
                'fax'       : index_get(headers_list,'Fax'),
                'mobile'    : index_get(headers_list,'Mobile'),
                'email'     : index_get(headers_list,'Email'),
                'website'   : index_get(headers_list,'Website'),
                'is_company': index_get(headers_list,'Is a Company'),
                'supplier'  : index_get(headers_list,'Supplier'),
                'customer'  : index_get(headers_list,'Customer'),
                'employee'  : index_get(headers_list,'Employee'),
                'related_company'   : index_get(headers_list,'Related Company/Name'),
                'property_payment_term' :index_get(headers_list,'Customer Payment Term/Payment Term'),
                'credit_limit': index_get(headers_list,'Credit Limit'),
                'debit_limit'   : index_get(headers_list,'Payable Limit'),
                'ref'       : index_get(headers_list,'Contact Reference'),
                'comment'   : index_get(headers_list,'Notes'),
   
            }
            
            error_log = ''
            n = 1 # Start Counter at One for to Account for Column Headers
            
            time_start = datetime.now()
            for data in partner_data[1:]:
                
                    n += 1
                
                    name = data[headers_dict['name']]                    
                    email = headers_dict['email'] and data[headers_dict['email']] or None    
                    search = [ ('name','=', name )]
                    partner_ids = partner_obj.search(cr,uid,search) or None
                    
                    if partner_ids and not wiz_rec.do_update:
                        _logger.info(_('Duplicate Found at Record %s -- %s, %s \n' % (n,name or '',email or'' )))
                        error_log += _('Duplicate Found at Record %s -- %s, %s \n' % (n,name or '',email or'' ))
                        
                        continue 
                    
                    if headers_dict['related_company'] and data[headers_dict['related_company']]:
                        
                        try:
                            related_search = [('name','=',data[headers_dict['related_company']])]
                            parent_id = state_obj.search(cr, uid , related_search)[0] or None
                        except:
                            _logger.info(_('Error Related Company Not Found -- %s, %s \n ' % (name or '',email or'' )))
                            error_log += _('Error Related Company Found at Record %s -- %s, %s \n' % (n,name or '',email or'' ))
                            parent_id = None
                    else:
                        parent_id = None 
                          
                    
                    if headers_dict['country_code'] and data[headers_dict['country_code']]:
                        try: 
                            country_search_val = [('code','=',data[headers_dict['country_code']])]
                            country_id = country_obj.search(cr, uid , country_search_val)[0] or None
                        except:
                            _logger.info(_('Error Country Not Found -- %s \n' % ( data[headers_dict['country_code']]  or '##' )))
                            error_log += _('Error Country Not Found at Record %s -- %s, %s \n' % (n,name or '',email or'' ))
                            country_id = None
                    else:
                        country_id = None
                        
                    
                    if headers_dict['state_code'] and data[headers_dict['state_code']]:
                        try: 
                            state_search_val = [('code','=',data[headers_dict['state_code']]),('country_id.code','=',data[headers_dict['country_code']])]
#                            state_search_val = [('code','=',data[headers_dict['state_code']]),('country_id','=',country_id)]
                            state_id = state_obj.search(cr, uid , state_search_val)[0] or None
                        except:
                            _logger.info(_('Error State Not Found -- %s' % (data[headers_dict['state_code']] or '##' )))
                            error_log += _('Error State Not Found at Record %s -- %s, %s \n' % (n,name or '',email or'' ))
                            state_id = None
                    else:
                        state_id =  None
                            
                        
                    if headers_dict['property_payment_term'] and data[headers_dict['property_payment_term']]:
                        try:    
                            term_obj = self.pool.get('account.payment.term')
                            term_search = [('name','=',data[headers_dict['property_payment_term']])]
                            property_payment_term = term_obj.search(cr, uid , term_search)
                            property_payment_term = property_payment_term[0] or None
                        except:
                            _logger.info(_('Error Payemtn Term Not Found -- %s, %s' % (name or '',email or'' )))
                            error_log += _('Error Payment Term Not Found at Record %s -- %s, %s \n' % (n,name or '',email or'' ))
                            property_payment_term = None
                    else:
                        property_payment_term = None
                            
                        
                    try:
                        part_vals = {
                                'name'          :name,
                                'email'         :email,
                                'sequence'     :headers_dict['sequence'] and data[headers_dict['sequence']] or None,
                                'street'        :headers_dict['street'] and data[headers_dict['street']] or None,
                                'street2'       :headers_dict['street2'] and data[headers_dict['street2']] or None,
                                'city'          :headers_dict['city'] and data[headers_dict['city']] or None,
                                'country_id'    :country_id,
                                'state_id'      :state_id,
                                
                                'zip'           :headers_dict['zip'] and data[headers_dict['zip']] or None,
                                'property_payment_term': property_payment_term,
                                'is_company'    :headers_dict['is_company'] and data[headers_dict['is_company']] or False,
                                'employee'      :headers_dict['employee'] and data[headers_dict['employee']] or False,
                                'customer'      :headers_dict['customer'] and data[headers_dict['customer']] or False ,
                                'supplier'      :headers_dict['supplier'] and data[headers_dict['supplier']] or False, 
                                'credit_limit'  :headers_dict['credit_limit'] and data[headers_dict['credit_limit']] or None,
                                'debit_limit'   :headers_dict['debit_limit'] and data[headers_dict['debit_limit']] or None,
                                'parent_id'     :parent_id,
                                'phone'         :headers_dict['phone'] and data[headers_dict['phone']] or None,
                                'fax'           :headers_dict['fax'] and data[headers_dict['fax']] or None,
                                'mobile'        :headers_dict['mobile'] and data[headers_dict['mobile']] or None,
                                'website'       :headers_dict['website'] and data[headers_dict['website']] or None, 
                                'ref'           :headers_dict['ref'] and data[headers_dict['ref']] or None,
                                'comment'       :headers_dict['comment'] and data[headers_dict['comment']] or None,                    
                                }
                        
                                                
                        if partner_ids and wiz_rec.do_update:
                            partner_obj.write(cr, uid,partner_ids, part_vals)
                            _logger.info('update record %s for %s, %s ',n,name,email)
                        
                        else:
                            partner_obj.create(cr, uid,part_vals , context=context)
                            _logger.info('Loaded record %s for %s, %s ',n,name,email)
                        
                        try:
                            if n == wiz_rec.test_sample_size  and context.get('test',False):
                                t2 = datetime.now()
                                time_delta = (t2 - time_start)
                                time_each = time_delta // wiz_rec.test_sample_size
                                list_size = len(partner_data)
                                 
                                estimate_time = (time_each * list_size)
                                
                                
                                msg = _('Time for %s records  is %s (hrs:min:sec) \n %s' % (list_size, estimate_time ,error_log))
                                
                                msg += _('/n -- Field Map --') 
                                
                                for field , i in headers_dict:
                                    msg +=  'Odoo Field' + field + ' >> Maps to >> ' + headers_list(i) + '/n'
                                    

                                cr.rollback()
                                vals = {'name':start,
                                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'error_log':error_log}
                                self.write(cr,uid,ids[0],vals)
                                return self.show_warning(cr, uid, msg , context = context)
                        except:
                            e = sys.exc_info()
                            _logger.error(_('Error %s' % (e,)))
                            vals = {'error_log': e}
                            self.write(cr,uid,ids[0],vals)
                            return vals
                        
                    except:
                        e = sys.exc_info()
                        _logger.info(_('Error  # partner not created for %s, %s' % (name or '',email or'' )))
                        error_log += _('Error  %s at Record %s -- %s, %s \n' % (e,n,name or '',email or'' ))
                    
        vals = {'name':start,
                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'error_log':error_log}
        if context.get('test',False):
            cr.rollback()
        self.write(cr,uid,ids[0],vals)
        result = {} 
        result['value'] = vals   
        return result
    
    def show_message(self, cr, uid, ids, context=None):
        
        return self.show_warning(cr,uid, "this is test")
        
    def show_warning(self,cr,uid,msg="None",context=None):
        
        warn_obj = self.pool.get( 'warning.warning')
        return warn_obj.info(cr, uid, title='Import Information',message = msg)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
