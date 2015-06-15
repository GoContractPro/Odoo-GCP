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
                'country'    : 'Country',
                'state'     : 'State',
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
                'related_company'       : 'Related Company/Name',
                'property_payment_term' : 'Customer Payment Term/Payment Term',
                'credit_limit'  : 'Credit Limit',
                'debit_limit'   : 'Payable Limit',
                'ref'       : 'Contact Reference',
                'comment'   : 'Notes',
                'external_id' : 'External ID',
                'sequence': 'Sequence',
            }


def index_get(L, i, v=None):
    try: return L.index(i) 
    except: return v

class partner_csv(osv.osv):
    _name = 'import.partner.csv'
    _columns = {
        'name':fields.char('Started',size=10, readonly=True),
        'end_time': fields.datetime('End',  readonly=True),
#        'browse_path': fields.binary('Csv File Path', required=True),
        'error_log': fields.text('Error Log'),
        'test_sample_size': fields.integer('Test Sample Size'),
        'do_update': fields.boolean('Allow Update', 
                help='If Set when  matching unique fields on records will update values for record, Otherwise will just log duplicate and skip this record '),
        'field_map' : fields.text ('Available Import Fields ', readonly = True, help='Display the CSV to Odoo Field map relations'),
        'csv_attachment': fields.many2many('ir.attachment',
            'import_markeeting_csv_ir_attachments_rel',
            'import_csv_id', 'attachment_id', 'CSV Import File'),
        'col_missing_in_csv' : fields.text ('Missing Import Fields ', readonly = True, help='Fields for Import not found in CSV sheet'),
        }
    
    
    def _get_header_map(self, cr, uid, context=None):
        field_map = 'CSV Column -->> Odoo Field \n\n'
        for field, column in HEADER_MAP.iteritems():
            field_map += column + ' -->> ' + field + '\n'
        return field_map
    
    _defaults = {
        'test_sample_size':20,
        'field_map' : _get_header_map
        
        }


    
    def check_expected_headers(self, cr, uid, ids, context=None):
         
        # Mapp Odoo Fields to  CSVColumns
        
        if context is None:
            context = {}
        for wiz_rec in self.browse(cr, uid, ids, context=context):
            
            str_data = ''
            for csv_attach in wiz_rec.csv_attachment:
                str_data = base64.decodestring(csv_attach.datas)
                continue
            
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                partner_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            headers_list = []
            
            for header in partner_data[0]:
                headers_list.append(header.strip())
             
            msg = 'Fields found on CSV file \n\n'
            msg += 'Position  -- CSV Column -> Odoo field  \n\n'
            fields_matched = {}
            fields_missing = []  
            headers_list = [x.lower() for x in headers_list ]
             
            for field, column in HEADER_MAP.iteritems():
                
                col_num = index_get(headers_list,column.lower())
                if col_num is None:
                    fields_missing.append(column + ' -> ' + field)
                else:
                    fields_matched[col_num + 1] = (column + ' -> ' + field)

            fields_match_sort = sorted(fields_matched.keys()) 
             
            for position in fields_match_sort:  
                msg += str(position)  + ' -- ' + fields_matched[position]
                msg += '\n'
                
            
            missing = ' Fields not found in Sheet --  \n\n'
            missing += 'CSV Column -> Odoo field  \n\n'
            for fields in fields_missing:
                missing +=  fields
                missing += '\n'
                
                
        popup_obj = self.pool.get( 'warning.warning')
        return popup_obj.info(cr, uid, title='CSV Map ', message = msg + '\n' + missing)
        
    
    
    def import_csv(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        state_obj = self.pool.get('res.country.state')
        country_obj = self.pool.get('res.country')
        model_data_obj = self.pool.get('ir.model.data')
        start = time.strftime('%Y-%m-%d %H:%M:%S')       
        if context is None:
            context = {}
        for wiz_rec in self.browse(cr, uid, ids, context=context):
            
            str_data = ''
            for csv_attach in wiz_rec.csv_attachment:
                str_data = base64.decodestring(csv_attach.datas)
                continue
                   
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                partner_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            

            headers_list = []
            for header in partner_data[0]:
                headers_list.append(header.strip())
            headers_list = [x.lower() for x in headers_list ]
             
            headers_dict = {}
            fields_missing = []
            for field, column in HEADER_MAP.iteritems():  
                
                headers_dict[field] = index_get(headers_list,column.lower())
                
                if headers_dict[field] is None:
                    fields_missing.append(column + ' -> ' + field)
                    
            missing = 'CSV Column -> Odoo field  \n\n'
            for fields in fields_missing:
                missing +=  fields
                missing += '\n'        
                    
            error_log = ''
            n = 1 # Start Counter at One for to Account for Column Headers
            
            time_start = datetime.now()
            list_size = len(partner_data)- 1
            for data in partner_data[1:]:
                
                    n += 1
                    
                    external_id = ((headers_dict.get('external_id') > -1) and data[headers_dict['external_id']]) or None   
                    name = ((headers_dict.get('name') > -1) and data[headers_dict['name']]) or None                   
                    email = ((headers_dict.get('email') > -1) and data[headers_dict['email']]) or None 
                    
                    if external_id:
                        search = [('name','=', data[headers_dict['external_id']]),('model','=','res.partner')]                     
                        model_data_ids =  model_data_obj.search(cr,uid,search) or None
                        if model_data_ids:
                            partner_ids = model_data_obj.browse(cr,uid,model_data_ids).res_id
                        else:
                            partner_ids = None
                    else:  
                        search = [ ('name','=', name ),
                                  ('street','=',((headers_dict.get('street')> -1) and data[headers_dict['street']]) or None),
                                  ('zip','=',((headers_dict.get('zip') > -1) and data[headers_dict['zip']]) or None)]
                        partner_ids = partner_obj.search(cr,uid,search) or None
                    
                    if partner_ids and not wiz_rec.do_update and not external_id:
                        _logger.info(_('Duplicate Found at row %s -- %s, %s \n' % (n,name or '',email or'' )))
                        error_log += _('Duplicate Found at row %s -- %s, %s \n' % (n,name or '',email or'' ))
                        continue 
                    
                    if (headers_dict.get('related_company') > -1) and data[headers_dict['related_company']]:
                        
                        try:
                            related_search = [('name','=',data[headers_dict['related_company']])]
                            parent_id = partner_obj.search(cr, uid , related_search)[0] or None
                        except:
                            msg = _('Error Related Company - %s - Not Found at row %s -- %s, %s \n' % (data[headers_dict['related_company']],n,name or '',email or'' ))
                            _logger.info(msg)
                            error_log += msg
                            parent_id = None
                    else:
                        parent_id = None 
                          
                    
                    if (headers_dict.get('country') > -1) and data[headers_dict['country']]:
                        
                        # TODO: Setting Default Country to  no country Specified in CSV-
                        try: 
                            if data[headers_dict['country']]== '':
                                country = 'US'
                            else:
                                country = data[headers_dict['country']]
                            
                            country_id = country_obj.name_search(cr, uid , name=country,context=context)[0][0] or None
                        except:
                            msg = _('Error Country %s Not Found at row %s -- %s, %s \n' % (data[headers_dict['country']],n,name or '',email or'' ))
                            _logger.info(msg)
                            error_log += msg
                            country_id = None
                    else:
                        country_id = country_obj.search(cr, uid , [('code','=','US')])[0] or None
                        
                    
                    if (headers_dict.get('state') > -1) and data[headers_dict['state']]:
                        try: 
#                            state_search_val = [('code','=',data[headers_dict['state_code']]),('country_id.code','=',data[headers_dict['country_code']])]
                            country_search = [('country_id','=',country_id)]
                            state = data[headers_dict['state']]
                            state_id = state_obj.name_search(cr, uid , name=state, args = country_search, context=context)[0][0] or None
                        except:
                            msg = _('Error State - %s - Not Found at row %s -- %s, %s \n' % (data[headers_dict['state']],n,name or '',email or'' ))
                            _logger.info(msg)
                            error_log += msg
                            state_id = None
                    else:
                        state_id =  None
                            
                        
                    if (headers_dict.get('property_payment_term') > -1) and data[headers_dict['property_payment_term']]:
                        try:    
                            term_obj = self.pool.get('account.payment.term')
                            term_search = [('name','=',data[headers_dict['property_payment_term']])]
                            property_payment_term = term_obj.search(cr, uid , term_search)
                            property_payment_term = property_payment_term[0] or None
                        except:
                            msg = _('Error Payment Term - %s - Not Found at row %s -- %s, %s \n' % (data[headers_dict['property_payment_term']],n,name or '',email or'' ))
                            _logger.info(msg)
                            error_log += msg
                            property_payment_term = None
                    else:
                        property_payment_term = None
                            
                        
                    try:
                        part_vals = { 
                                'name'          :name,
                                'email'         :email,
                                'street'        :((headers_dict.get('street')> -1) and data[headers_dict['street']]) or None,
                                'street2'       :((headers_dict.get('street2') > -1) and data[headers_dict['street2']]) or None,
                                'city'          :((headers_dict.get('city') > -1) and data[headers_dict['city']]) or None,
                                'country_id'    :country_id,
                                'state_id'      :state_id,
                                
                                'zip'           :((headers_dict.get('zip') > -1) and data[headers_dict['zip']]) or None,
                                'property_payment_term': property_payment_term,
                                'is_company'    :((headers_dict.get('is_company') >-1 ) and data[headers_dict['is_company']]) or False,
                                'employee'      :((headers_dict.get('employee') >-1 ) and data[headers_dict['employee']])or False,
                                'customer'      :((headers_dict.get('customer') > -1 ) and data[headers_dict['customer']]) or False ,
                                'supplier'      :((headers_dict.get('supplier') > -1) and data[headers_dict['supplier']]) or False, 
                                'credit_limit'  :((headers_dict.get('credit_limit') > -1) and data[headers_dict['credit_limit']]) or None,
                                'debit_limit'   :((headers_dict.get('debit_limit') > -1) and data[headers_dict['debit_limit']]) or None,
                                'parent_id'     :parent_id,
                                'phone'         :((headers_dict.get('phone') > -1) and data[headers_dict['phone']]) or None,
                                'fax'           :((headers_dict.get('fax') > -1) and data[headers_dict['fax']]) or None,
                                'mobile'        :((headers_dict.get('mobile') > -1) and data[headers_dict['mobile']]) or None,
                                'website'       :(( headers_dict.get('website') > -1) and data[headers_dict['website']]) or None, 
                                'ref'           :((headers_dict.get('ref') > -1) and data[headers_dict['ref']]) or None,
                                'comment'       :((headers_dict.get('comment') > -1) and data[headers_dict['comment']] ) or None,
                                'sequence'      :((headers_dict.get('sequence') > -1) and data[headers_dict['sequence']] ) or None,              
                                }
                        
                                                
                        if partner_ids and (wiz_rec.do_update or model_data_ids) :
                            partner_obj.write(cr, uid,partner_ids, part_vals)
                            _logger.info('update row %s for %s, %s ',n,name,email)
                        
                        else:
                            id = partner_obj.create(cr, uid,part_vals , context=context)
                            if external_id and id:
                                data = {'res_id':id,
                                        'name':external_id,
                                        'model':'res.partner',
                                        'noupdate': False}
                                model_data_obj.create(cr,uid,data,context=context)
                            
                            _logger.info('Loaded row %s for %s, %s ',n,name,email)
                        
                        #exit loop and Roll back updates if is a test
                        try:
                            
                            if  context.get('test',True) and (((n - 1) >= list_size) or (n > wiz_rec.test_sample_size)) :
                                t2 = datetime.now()
                                time_delta = (t2 - time_start)
                                time_each = time_delta // wiz_rec.test_sample_size
                                
                                 
                                estimate_time = (time_each * list_size)
                                
                                
                                msg = _('%s Total Records in Import, Estimated Import Time is %s (hrs:min:sec) \n\n %s' % (list_size, estimate_time ,error_log))
                                
                                cr.rollback()
                                vals = {'name':start,
                                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'error_log':error_log,
                                'col_missing_in_csv':missing,
                                }
                                self.write(cr,uid,ids[0],vals)
                                return self.show_warning(cr, uid, msg , context = context)
                        except:
                            e = sys.exc_info()
                            _logger.error(_('Error %s' % (e,)))
                            vals = {'error_log': e,
                                    'col_missing_in_csv': missing}
                            self.write(cr,uid,ids[0],vals)
                            return vals
                        
                    except:
                        e = sys.exc_info()
                        msg = _('Error  %s at row %s -- %s, %s \n' % (e,n,name or '',email or'' ))
                        _logger.info(msg)
                        error_log += _(msg)
                        if n == wiz_rec.test_sample_size  and context.get('test',True):
                            vals = {'error_log': error_log}
                            cr.rollback()
                            self.write(cr,uid,ids[0],vals)
                            return vals
                    

        if not error_log:
            error_log = "All Records Imported Successfully"
        vals = {'name':start,
                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'error_log':error_log,
                'col_missing_in_csv': missing}
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
    
    def onchange_csv_attachment(self, cr, uid ,ids, attachments=None, context=None):

        if context is None:
            context = {}
        n = 0    
        attach = attachments[0]
        if attach[2]:
            n= len(attach[2] or 0)
            
        if n > 1:
# TODO: make so additional files attached are automatically deleted
#                extra_attachments = attach[2][1:]
#                self.pool.get('ir.attachment').unlink(cr,uid,extra_attachments, context=context)
                raise osv.except_osv('Warning', 'Only attach one file!, other files will be ignored')
                
        return

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
