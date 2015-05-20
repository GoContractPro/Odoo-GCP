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

def index_get(L, i, v=None):
    try: return L.index(i)
    except: return v
    
class import_header_csv(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = 'import.header.csv'
    _description = "Map Odoo Data to CSV  Import Sheet Columns"
    _columns = { 'name':fields.char('CSV Header Field', size=64, required = True),
                'csv_id':fields.many2one('import.csv','Import CSV'),
                'is_unique':fields.boolean('Is Unique', help ='Value for Field  Should be unique name or reference identifier and not Duplicated '),
                'model':fields.many2one('ir.model','Model'),
                'model_field':fields.many2one('ir.model.fields','Model Field'),
                'relation_model': fields.many2one('ir.model', 'Relation Model',
                    help="The   model this field is related to"),
                'search':fields.char('Domian Search  ', size=256,
                     help="Define search domains for related records subsitute Values from CSV columns in search using ${'Column Name'} example: [('odoo_field_name', '=', ${'Column Name'}] "),
                
                'create':fields.boolean('Create Related', help = "Will create the related records using system default values if missing" ),
                }
    
    def onchange_name(self, cr, uid, ids, name, context=None):
        # TODO set model_field value to Search  if Name matches the models Field Name,
        # TODo set relation_model if the model_field is found and is a Relation Feild
        return

class import_csv(osv.osv):
    _name = 'import.csv'
    _columns = {
        'name':fields.char('Name',size=32, ),
        'model_id': fields.many2one('ir.model', 'Model', ondelete='cascade', required= True,
            help="The model to import"),
        'start_time': fields.datetime('Start',  readonly=True),
        'end_time': fields.datetime('End',  readonly=True),
        'browse_path': fields.binary('Csv File Path', required=True),
        'error_log': fields.text('Error Log'),
        'test_sample_size': fields.integer('Test Sample Size'),
        'do_update': fields.boolean('Allow Update', 
                help='If Set when  matching unique fields on records will update values for record, Otherwise will just log duplicate and skip this record '),
        'header_csv_ids': fields.one2many('import.header.csv','csv_id','CSV Columns Map'),
        }
    
    _defaults = {
        'test_sample_size':10
        }
    
    
    
    def action_get_headers_csv(self, cr, uid, ids, context=None):
        
        for import_csv in self.browse(cr,uid,ids,context):
        
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
                
                header_csv_obj = self.pool.get('import.header.csv')
                header_csv_ids=header_csv_obj.search(cr, uid,[('csv_id','=',ids[0])])
                if header_csv_ids:
                    header_csv_obj.unlink(cr,uid,header_csv_ids,context=None)
                
                headers_list = []
                for header in partner_data[0]:
                    headers_list.append(header.strip())
                n=0
                for header in headers_list:
                    n += 1
                    rid = self.pool.get('import.header.csv').create(cr,uid,{'name':header,'index': n , 'csv_id':import_csv.id, 'model_id':import_csv.model_id.id})
        return True
    
    def search_record_exists(self, cr, uid, data, header_dict, context = None): 
        
        #Todo Add Code here to  search on fields in header_dict which are flaged as Unique Record
        # for example a Name or Ref Field
        # if Found Return record ID (most also Consider is possible could be multiple records if search field not Truely unique Will update all these)
        # if not Found Return false
        
        return False  
    
    def make_domain_search(self,cr,uid,data,header_dict,field):
        
        search_string = ''
        
        #TODO Add code here to Create Domain Search 
        # Parse field.search and replace column Identifier with Values from CSV Data
        # For Example
        # 
        # If Header_dict Search  for field is  '[('name','=',${'Name'})]
        # Where 'Name' is The Column Header on CSV and 'name' is field named in Odoo
        # Substitute in the value from CSV data for ${'Name'} for this data row and return modified String, 
        # Similar in how Email Template will do Substitution
    
        return search_string
    
    def action_import_csv(self, cr, uid, ids, context=None):

        start = time.strftime('%Y-%m-%d %H:%M:%S')       
        if context is None:
            context = {}
        for wiz_rec in self.browse(cr, uid, ids, context=context):
            
            str_data = base64.decodestring(wiz_rec.browse_path)
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                csv_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            error_log = ''
            n = 1
            
            time_start = datetime.now()
            
            # get Header Dict
            
            header_dict_ids = self.pool.get('import.header.csv').search(cr,uid,[('id','=',ids[0])])
            header_dict = self.pool.get('import.header.csv').browse(cr,uid,header_dict_ids)
            
            for data in csv_data[1:]:
                
#               Check if Uniques already exist in Data if so then if Do update is True then write Records else Skip
                # TODO add Code here to Search on Uniques
                n += 1
                
                record_ids = self.search_record_exists(cr,uid,data, header_dict)
                    
                if record_ids and not wiz_rec.do_update: 
                    
                    #TODO  need to add the Unique Record Field and Value Found to this Log
                    
                    _logger.info(_('Error Duplicate Name Found at line %s record skipped' % (n)) )
                    error_log += _('Error Duplicate Name Found at line %s record skipped\n' %(n) )
                    
                    continue
                    
                # Create Vals Dict    
                vals ={}
                for field in header_dict:
                    
                    if field.related:
                        
                        # Search on Related Model using Search Domain and Get ID
                        # TODO: update code Search must be created from search defined on import.header.csv and substitute
                        # values from data based on column name in csv and Data in CSV
                        #
                    
                        search = self.make_domain_search(field.search, data ,header_dict)
                        id = self.pool.get(field.relation_model).search(cr,uid,search)
                        vals[field.name] = id
                        
                        # if related record not Found then to posible routes
                        #
                        #      if the  flag to create is set for this field  then  attempt to Create a record with Default values, Log this create in Error log and line  number 
                        #
                        #      Else If Related Record missing  then Skip import line IN CSV and Log in Error log record Skipped reason and line  number 
                        #  
                        # 
                            
                    else:
                        vals[field.name] = data(field.index) 
                
                # Update or Create Import Records  
                try:
                    if record_ids:
                        self.pool.get(import_csv.model_id.name).write(cr, uid, record_ids, vals )
                        _logger.info('Update  Line Number %s  ',n)

                    else:
                        self.pool.get(import_csv.model_id.name).create(cr, uid, vals, context=context)
                        _logger.info('Imported Line Number%s  ',n)
                 
                except:
                    e = sys.exc_info()
                    _logger.info(_('Error  %s record not created for line Number %s' % (e,n,)))
                    error_log += _('Error  %s at Record %s -- %s, %s \n' % (e,n, )) 
                  
                  
                # This is only a Test Roll Back Records exit loop and create POP UP With Info statistic about Import 
                                       
                
                    if n == wiz_rec.test_sample_size  and context.get('test',False):
                        try:
                            t2 = datetime.now()
                            time_delta = (t2 - time_start)
                            time_each = time_delta // wiz_rec.test_sample_size
                            list_size = len(partner_data)
                             
                            estimate_time = (time_each * list_size)
                            
                            
                            msg = _('Time for %s records  is %s (hrs:min:sec) \n %s' % (list_size, estimate_time ,error_log))
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
                            return False

                        

                    
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
