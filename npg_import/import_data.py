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


from openerp.osv import fields, osv, orm
from openerp import tools
from openerp.tools.translate import _
import csv
import cStringIO
import base64
from datetime import datetime
import time
from  dbfread import DBF

import logging 
import sys

_logger = logging.getLogger(__name__)

def index_get(L, i, v=None):
    try: return L.index(i)
    except: return v

class import_data_header(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.data.header"
    _description = "Map Odoo Fields to Import Fields"
    
    _columns = { 'name':fields.char('Import Field Name', size=64, required = True),
                'import_data_file_id':fields.many2one('import.data.file','Import Data',required=True, ondelete='cascade',),
                'o2m_id':fields.many2one('some.data.o2m','o2m test',required=True, ondelete='cascade',),
                'is_unique':fields.boolean('Is Unique', help ='Value for Field  Should be unique name or reference identifier and not Duplicated '),
                'model':fields.many2one('ir.model','Model'),
                'model_field':fields.many2one('ir.model.fields','Odoo Model Field'),
                'relation_model': fields.many2one('ir.model', 'Relation Model',
                    help="The  model this field is related to"),
                'search_domain':fields.char('Domian Search  ', size=256,
                     help="Define search domains for related records subsitute Values from CSV columns in search using ${'Column Name'} example: [('odoo_field_name', '=', ${'Column Name'}] "),           
                'create':fields.boolean('Create Related', help = "Will create the related records using system default values if missing" ),
                'descr':fields.text('description')
                }
    
    def _get_model(self,cr,uid,context={}):
        return context.get('model',False)
    
    _defaults = {
                 'model':_get_model,
                 }
    
    def onchange_name(self, cr, uid, ids, name, context=None):
        # TODO set model_field value to Search  if Name matches the models Field Name,
        # TODo set relation_model if the model_field is found and is a Relation Feild
        return    


class import_data_file(osv.osv):
    
    _name = "import.data.file"
    _description = "Holds import Data file information"
    
    _columns = {
        'name':fields.char('Name',size=32,required = True ), 
        'model_id': fields.many2one('ir.model', 'Model', ondelete='cascade', required= False,
            help="The model to import"),
        'start_time': fields.datetime('Start',  readonly=True),
        'end_time': fields.datetime('End',  readonly=True),
        'attachment': fields.many2many('ir.attachment',
            'data_import_ir_attachments_rel',
            'import_data_id', 'attachment_id', 'Import File'),
        'error_log': fields.text('Error Log'),
        'test_sample_size': fields.integer('Test Sample Size'),
        'do_update': fields.boolean('Allow Update', 
                help='If Set when  matching unique fields on records will update values for record, Otherwise will just log duplicate and skip this record '),
        'header_ids': fields.one2many('import.data.header','import_data_file_id','Fields Map'),
        'index':fields.integer("Index"),
        }
    
    _defaults = {
        'test_sample_size':10
        }
    def _match_header(self, header, fields, options):
        """ Attempts to match a given header to a field of the
        imported model.

        :param str header: header name from the data file
        :param fields:
        :param dict options:
        :returns: an empty list if the header couldn't be matched, or
                  all the fields to traverse
        :rtype: list(Field)
        """
        for field in fields:
            # FIXME: should match all translations & original
            # TODO: use string distance (levenshtein? hamming?)
            if header == field['name'] \
              or header.lower() == field['string'].lower():
                return [field]

        if '/' not in header:
            return []

        # relational field path
        traversal = []
        subfields = fields
        # Iteratively dive into fields tree
        for section in header.split('/'):
            # Strip section in case spaces are added around '/' for
            # readability of paths
            match = self._match_header(section.strip(), subfields, options)
            # Any match failure, exit
            if not match: return []
            # prep subfields for next iteration within match[0]
            field = match[0]
            subfields = field['fields']
            traversal.append(field)
        return traversal
    
    def action_get_headers_dbf(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for wiz_rec in self.browse(cr, uid, ids, context=context):
            for attach in wiz_rec.attachment:
                data_file = attach.datas
                continue
            try:
                table_data = DBF(data_file)
            except:
                raise osv.except_osv('Warning', 'Make sure you are using a DBF format File!')
            
            if not table_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            
                header_obj = self.pool.get('import.data.header')
                header_ids=header_obj.search(cr, uid,[('data_id','=',ids[0])])
                    
                if header_ids:
                    header_obj.unlink(cr,uid,header_ids,context=None)
                    

                
                for record in table_data:
                    n=0
                    for header, data in record:
                        n += 1
                        field_ids = self.pool.get('ir.model.fields').search(cr,uid,[('field_description','ilike',header), ('model_id', '=', wiz_rec.model_id.id)])
                        header_id = self.pool.get('import.data.header').create(cr,uid,{'name':header,'index': n , 'data_id':wiz_rec.id, 'model_field':field_ids and field_ids[0] or False, 'model':wiz_rec.model_id.id},context=context)
                    continue    
#             model_obj = self.pool[wiz_rec.model_id.model]
#             fields_got = model_obj.fields_get(cr, uid, context=context)
#             blacklist = orm.MAGIC_COLUMNS + [model_obj.CONCURRENCY_CHECK_FIELD]
#             for name, field in fields_got.iteritems():
#                 if name in blacklist:
#                     continue
        return 
    
    def action_get_headers_csv(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for wiz_rec in self.browse(cr, uid, ids, context=context):

            for attach in wiz_rec.attachment:
                data_file = attach.datas
                continue
            str_data = base64.decodestring(data_file)
            
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                partner_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            header_csv_obj = self.pool.get('import.data.header')
            header_csv_ids=header_csv_obj.search(cr, uid,[('data_id','=',ids[0])])
            
            if header_csv_ids:
                header_csv_obj.unlink(cr,uid,header_csv_ids,context=None)
            
            headers_list = []
            for header in partner_data[0]:
                headers_list.append(header.strip())
            n=0
            for header in headers_list:
                n += 1
                fids = self.pool.get('ir.model.fields').search(cr,uid,[('field_description','ilike',header), ('model_id', '=', wiz_rec.model_id.id)])
                rid = self.pool.get('import.data.header').create(cr,uid,{'name':header,'index': n , 'csv_id':wiz_rec.id, 'model_field':fids and fids[0] or False, 'model':wiz_rec.model_id.id},context=context)
                
#             model_obj = self.pool[wiz_rec.model_id.model]
#             fields_got = model_obj.fields_get(cr, uid, context=context)
#             blacklist = orm.MAGIC_COLUMNS + [model_obj.CONCURRENCY_CHECK_FIELD]
#             for name, field in fields_got.iteritems():
#                 if name in blacklist:
#                     continue
        return True
    
    def search_header_exists(self, cr, uid, ids, model_id, header_dict, context = None): 
        ir_model_obj = self.pool.get('ir.model')
        ir_model_fields_obj = self.pool.get('ir.model.fields')
#         model=ir_model_obj.browse(cr,uid,model_id)
#         model_name=model.model
#         model_ids = ir_model_obj.search(cr, uid, [('model', '=',model_name)], context=context)
        if model_id:
            field_ids = ir_model_fields_obj.search(cr, uid, [('field_description','=',header_dict['name']), ('model_id', '=', model_id)], context=context)
            if field_ids:
                field_id = field_ids[0]
    
    def search_record_exists(self, cr, uid, wiz_rec, data,header_dict, unique_fields=[]):
        if not unique_fields: return False
        ir_model_obj = self.pool.get('ir.model')
        ir_model_fields_obj = self.pool.get('ir.model.fields')
        
        dom = []
        for col in unique_fields:
            dom.append((col, '=', data[header_dict[col]]))
            
        obj = self.pool[wiz_rec.model_id.model]
        return obj.search(cr,uid,dom)
        
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
            
            if not wiz_rec.header_ids:
                raise osv.except_osv('Warning', 'No Header selected in Header list')
            
            for attach in wiz_rec.attachment:
                data_file = attach.datas
                continue
            str_data = base64.decodestring(data_file)
            
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                csv_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            error_log = ''
            n = 1
            
            time_start = datetime.now()
            print "time_start",time_start
            headers_list = []
            for header in csv_data[0]:
                headers_list.append(header.strip())
            
            header_map = {}
            unique_fields = []
            for hd in wiz_rec.header_ids:
                if hd.model_field:
                    label = hd.model_field.field_description or ''
                    header_map.update({hd.model_field.name : hd.name})
                    if hd.is_unique:
                        unique_fields.append(hd.model_field.name)
                        
            if not header_map:
                raise osv.except_osv('Warning', 'No Header mapped with Model Field in Header line!')
                        
            headers_dict = {}
            for field, label in header_map.iteritems():  
                headers_dict[field] = index_get(headers_list,label)
                
            for data in csv_data[1:]:
#               Check if Uniques already exist in Data if so then if Do update is True then write Records else Skip
                # TODO add Code here to Search on Uniques
                n += 1
                
                record_ids = self.search_record_exists(cr,uid,wiz_rec,data,headers_dict,unique_fields)
                print record_ids 
                if record_ids and not wiz_rec.do_update: 
                    
                    #TODO  need to add the Unique Record Field and Value Found to this Log
                    
                    _logger.info(_('Error Duplicate Name Found at line %s record skipped') % (n))
                    error_log += _('Error Duplicate Name Found at line %s record skipped\n') %(n)
                    
                    continue
                    
                # Create Vals Dict    
                vals ={}
                for hd in wiz_rec.header_ids:
                    model_field = hd.model_field
                    if not model_field or not headers_dict.has_key(model_field.name): continue
                    field_text = data[headers_dict[model_field.name]]
                    if model_field.ttype == 'many2one':
#                         Verts TODO: Generally many2one fields represented by "Name" Field. It can be any field from relation table. 
#                         Needs to change logic here according to appropriate fields
                        rel_id = self.pool[model_field.relation].search(cr,uid,[('name','=',field_text)])
                        if rel_id : 
                            vals.update({model_field.name : rel_id[0]})
                        else:
                            vals.update({model_field.name : False})
                            _logger.info(_('Value \'%s\' not found for the relation field \'%s\'') % (field_text, model_field.field_description))
                            error_log += _('Value \'%s\' not found for the relation field \'%s\'') % (field_text, model_field.field_description)
                    elif model_field.ttype == 'boolean':
#                         Verts: Check if the field type is boolean the eval corresponding cell string for this field
                        field_text = field_text.upper()
                        if field_text in ['TRUE','1','T']:
                            vals.update({model_field.name : True})
                        elif field_text in ['0','FALSE','F']:
                            vals.update({model_field.name : False})
                        else:
                            vals.update({model_field.name : False})
                    else:
                        vals.update({model_field.name : field_text})
                        
                        # Search on Related Model using Search Domain and Get ID
                        # TODO: update code Search must be created from search defined on import.header.csv and substitute
                        # values from data based on column name in csv and Data in CSV
                        #
                    
#                         search = self.make_domain_search(field.search, data ,header_dict)
#                         id = self.pool.get(field.relation_model).search(cr,uid,search)
#                         vals[field.name] = id
                        
                        # if related record not Found then to posible routes
                        #
                        #      if the  flag to create is set for this field  then  attempt to Create a record with Default values, Log this create in Error log and line  number 
                        #
                        #      Else If Related Record missing  then Skip import line IN CSV and Log in Error log record Skipped reason and line  number 
                        #  
                        # 
                            
#                     else:
#                         vals[field.name] = data(field.index) 
                
                # Update or Create Import Records  
                try:
                    if record_ids:
                        self.pool.get(wiz_rec.model_id.model).write(cr, uid, record_ids, vals )
                        _logger.info('Update  Line Number %s  ' % n)

                    else:
                        self.pool.get(wiz_rec.model_id.model).create(cr, uid, vals, context=context)
                        _logger.info('Imported Line Number%s  ' % n)
                 
                except:
                    e = sys.exc_info()
                    _logger.info(_('Error  %s record not created for line Number %s') % (e,n,))
                    error_log += _('Error  %s at Record %s --\n') % (e,n, ) 
                  
                  
                # This is only a Test Roll Back Records exit loop and create POP UP With Info statistic about Import 
                                       
                
                if n == wiz_rec.test_sample_size  and context.get('test',False):
                    try:
                        t2 = datetime.now()
                        time_delta = (t2 - time_start)
                        time_each = time_delta / wiz_rec.test_sample_size
                        list_size = len(csv_data)
                          
                        estimate_time = (time_each * list_size)
                         
                        print "time_end,time_delta,estimate_time",t2,time_delta,estimate_time
                        msg = _('Time for %s records  is %s (hrs:min:sec) \n %s') % (list_size, estimate_time ,error_log)
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
