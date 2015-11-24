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
import os
import cStringIO
import base64
from datetime import datetime
import dateutil.parser
import time
#from  dbfread import DBF
#from dbfread import field_parser
import dbf

import logging 
import sys, traceback

import contextlib
from string import strip
from  types import *

_logger = logging.getLogger(__name__)

def index_get(L, i, v=None):
    try: return L.index(i)
    except: return v
    
class import_m2o_substitutions(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.m2o.substitutions"
    _description = "Create new value Substitutions functionality in Fields mapping"
    
    _columns = { 
                'header_map':fields.many2one('import.data.header', 'Header Map', required=True, ondelete='cascade'),
                'src_value':fields.char('Source field value', size=64,required=True),
                'odoo_value':fields.char('Corresponding odoo value', size=64,required=True),
                }
    
class import_m2o_values(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.m2o.values"
    _description = "Create new value Substitutions functionality in Fields mapping"
    
    _columns = { 
                'header_map':fields.many2one('import.data.header', 'Header Map', required=True, ondelete='cascade'),
                'default_value':fields.char('Source Default value', size=64,required=True),
                'source_field':fields.many2one('import.data.header', 'Source Field', Domain="[('import_data_id','=', header_map)]"),
                'odoo_field':fields.many2one('ir.model.fields','Corresponding Odoo Field',Domain="[('model_id','=', header_map.model)]" ),
                }



class import_data_header(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.data.header"
    _description = "Map Odoo Fields to Import Fields"
    
    _columns = { 'name':fields.char('Import Field Name', size=64),
                'import_data_id':fields.many2one('import.data.file','Import Data',required=True, ondelete='cascade',),
                'is_unique':fields.boolean('Is Unique', help ='Value for Field  Should be unique name or reference identifier and not Duplicated '),
                'model':fields.many2one('ir.model','Model'),
                'model_field':fields.many2one('ir.model.fields','Odoo Field', domain="[('model_id','=',model)]"),
                'model_field_type':fields.char('Odoo Data Type', size = 128),
                'model_field_name':fields.char('Odoo Field Name', size = 128),
                'relation': fields.char('Odoo Related Model', size = 128,
                    help="The tecnmical name of  Model this field is related to"),
                'relation_id': fields.many2one('ir.model','Odoo Related Model ID'),
                'relation_field': fields.char('Odoo Relation Field', size = 128,
                    help="The  technical name of Field Relation field in one2many and many2many "),
                'search_filter':fields.char('Filter Source', size=256,
                      help="""Use to create Filter on incoming records Field value in source must match values in list or row is skipped on import, \n
                      Can use mulitple values for filter,  format as python type list for values example ['value1','value2','value3'], """),           
                'create_related':fields.boolean('Create Related', help = "Will create the related records using system default values if missing" ),
                'field_label':fields.char('Description', size=32,),
                'field_type':fields.char('Data Type', size=8,),
                'field_val':fields.char('Record Value', size=128),
                'default_val':fields.char('Default Import Val', size = 256, help = 'The Default if no values for field in imported Source'),
                'm2o_substituions':fields.one2many('import.m2o.substitutions','header_map', string="Source Value Substitutions"),
                'is_unique_external':fields.boolean('External ID Field', readonly=True ,
                                help ='Check if this field is Unique e.g. an Account Number or A vendor Number. Its value will be used in odoo external ID'),
                'm2o_values':fields.one2many('import.m2o.values','header_map', string="Default Values or source values to map to create related and parent records"),
                'm2o_create_external':fields.boolean('Create External on Related'),
                'search_related_external':fields.boolean('External ID Search'),
                'search_name' : fields.boolean('Name Search'),
                'search_other_field' : fields.many2one('ir.model.fields','Other Search Field', domain="[('model_id','=',relation_id)]", 
                                help='Select field  to match in related record othe than Name or External ID'),
                'related_source_table': fields.many2one('import.data.file','Related Source Table'),
                }
    
  
    
    def _get_model(self,cr,uid,context={}):
        return context.get('model',False)
    
    _defaults = {
                 'model':_get_model,
                 'search_filter' : [],
                 }
    
    
    def onchange_model_field(self, cr, uid, ids, model_field, context=None):
        if not ids:
            return {}
        fld = self.pool.get('ir.model.fields').browse(cr,uid,model_field)
        if fld:
            '''    if fld.ttype == 'one2many':
                #TODO add the functionality for o2m and remove this exception
                vals =  {'model_field_type': False,
                    'model_field_name': False,
                    'relation_field': False,
                    'relation_id': False,
                    'relation': False,
                    'model_field': False,}
                self.write(cr,uid,ids[0],vals)
                
                raise osv.except_osv(_('Warning'), _("one2many not yet supported!"))
            '''
                
        
            relation_id = self.pool.get('ir.model').search(cr,uid,[('model','=',fld.relation)])
            vals = {'model_field_type': fld.ttype,
                    'model_field_name': fld.name,
                    'relation_field': fld.relation_field,
                    'relation_id': relation_id and relation_id[0] or False,
                    'relation': fld.relation,
                    }
            self.write(cr,uid,ids[0],vals)
            return {'value':vals}
            
        else:
            vals =  {'model_field_type': False,
                    'model_field_name': False,
                    'relation_field': False,
                    'relation_id': False,
                    'relation': False,}
            self.write(cr,uid,ids[0],vals)
          
            return {'value':vals}
        
class import_data_file(osv.osv):
    
    _name = "import.data.file"
    _description = "Holds import Data file information"
   
    def _get_external_id_field(self, cr, uid, ids, fields, arg, context=None):
        
        header_fld_obj = self.pool.get('import.data.header')
        search = [('is_unique_external','=',True),('import_data_id','=',ids[0])]
        extern_fld = header_fld_obj.search(cr,uid, search)[0].name or None
        return extern_fld
        
         
    _columns = {
            'name':fields.char('Name',size=32,required = True ), 
            'description':fields.text('Description',), 
            'model_id': fields.many2one('ir.model', 'Model', ondelete='cascade', required= False,
                help="The model to import"),
            'start_time': fields.datetime('Start',  readonly=True),
            'end_time': fields.datetime('End',  readonly=True),
            'attachment': fields.many2many('ir.attachment',
                'data_import_ir_attachments_rel',
                'import_data_id', 'attachment_id', 'CSV File'),
            'error_log': fields.text('Error Log'),
            'test_sample_size': fields.integer('Test Sample Size'),
            'do_update': fields.boolean('Allow Update', 
                    help='If Set when  matching unique fields on records will update values for record, Otherwise will just log duplicate and skip this record '),
            'header_ids': fields.one2many('import.data.header','import_data_id','Fields Map',limit=300),
            'index':fields.integer("Index"),
            'dbf_path':fields.char('DBF Path',size=256),
            'record_num':fields.integer('Current Record'),
            'tot_record_num':fields.integer("Total Records"),
            'record_external':fields.boolean('Use External ID' , help = 'record number and File name to be used for External ID'),
            'has_errors':fields.boolean('Has Errors'),
            'rollback':fields.boolean('Roll Back Test Records'),
            'external_id_field':fields.many2one('import.data.header', string='External Id Field', domain="[('import_data_id','=',active_id)]"),
            }
    
    _defaults = {
        'test_sample_size':10,
        'record_num':1,
        }

    def onchange_record_external(self,cr,uid, ids, record_external, context=None):
        
        if record_external:
            return {'value': {'external_id_field': False}}
        
    def onchange_external_id_field(self,cr,uid, ids, external_id_field,  context=None):
       
        if ids: 
            header_ids_vals = []
            header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0])])
            for header_rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):
            
                if header_rec.id == external_id_field:
                    value = True
                else:
                    value = False
                    
                vals = {  'is_unique_external': value}
                header_ids_vals.append((1,header_rec.id, vals))
                
            return{'value':{"header_ids":header_ids_vals}}
        else:
            return {}

    def action_get_headers(self, cr, uid, ids, context=None):
        
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.dbf_path:
                self.action_get_headers_dbf(cr, uid, ids, context)
                return
            if rec.rec.attachment:
                self.action_get_headers_csv(cr, uid, ids, context)
                return
            
        raise osv.except_osv('Warning', 'No Data files to Import')
    
    def get_label_match_index(self, cr, uid, dbf_table ):
        
        
        dbf_path = dbf_table.filename
        dbf_directory = os.path.dirname(dbf_path)
        table_name = os.path.basename(dbf_path).split('.')[0]

        fldlabel_dbf_table = dbf.Table(dbf_directory + '/FLDLABEL.DBF')
        fldlabel_dbf_table.open()
        
        if not fldlabel_dbf_table:
            
            e = 'No Labels in DBF Import  %s:'  % (fldlabel_path, )
            _logger.error(_('Error %s' % (e,)))
              
        index = fldlabel_dbf_table.create_index(lambda rec: rec.table)
        
        return index.search(match=table_name.ljust(10))
                
 
    
    def action_get_headers_dbf(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        tot_records = 0
        for rec in self.browse(cr, uid, ids, context=context):
            rec.record_num = 1
            try:
         
                header_obj = self.pool.get('import.data.header')
                header_ids=header_obj.search(cr, uid,[('import_data_id','=',ids[0])])
                    
                if header_ids:
                    header_obj.unlink(cr,uid,header_ids,context=None)
               
                dbf_table = dbf.Table(rec.dbf_path)
                dbf_table.open()
                info = dbf.info(rec.dbf_path)
                
                structure = dbf.structure(rec.dbf_path)


                if not dbf_table:
                    
                    e = 'Error opening DBF Import  %s:'  % (rec.dbf_path, )
                    _logger.error(_('Error %s' % (e,)))
                    vals = {'error_log': e,
                            'has_errors':True}
                    self.write(cr,uid,ids[0],vals) 
                 
                tot_records = len(dbf_table)    
                if tot_records == 0:
                    e = 'Table has no data to Import  %s:'  % (rec.dbf_path, )
                    _logger.error(_('Error %s' % (e,)))
                    vals = {'error_log': e,
                            'has_errors':True}
                    self.write(cr,uid,ids[0],vals)
                    return
                    
                dbf_label_index = self.get_label_match_index(cr, uid, dbf_table)
                

                for field in structure:
           
                    field = field.split()

                    field_label =  self.vision_match_field_label(cr, uid, field[0], index = dbf_label_index)
        
                    fld_obj = self._match_import_header(cr, uid, rec.model_id.id, field[0], field_label)    
                        
                    vals = {'name':field[0], 'import_data_id':rec.id,
                            'model_field':fld_obj and fld_obj.id or False,
                            'model_field_name' :fld_obj and fld_obj.name or False,
                            'model_field_type' : fld_obj and fld_obj.ttype or False,
                            'model':rec.model_id and rec.model_id.id,
                            'relation': fld_obj and fld_obj.relation or False,
                            'relation_field' : fld_obj and fld_obj.relation_field or False,
                            'field_label': field_label or False,
                            'field_val':dbf_table[0][field[0]],
                            'field_type':field[1]
                            
                            
                            }
                    header_id = self.pool.get('import.data.header').create(cr,uid,vals,context=context)
                    
                vals = {'error_log':'Successful Header Import',
                    'has_errors':False,
                    'tot_record_num':tot_records, 
                    'description':info
                    }
                self.write(cr,uid,ids[0],vals)    
                
                return {'value': vals}
                
            except:
                sys_info = sys.exc_info()
                e = 'Error opening DBF Import  %s: \n%s \n%s'  % (rec.dbf_path, sys_info[1],sys_info[2]) 
                print e
                _logger.error(_('Error:  %s ' % (e,)))
                vals = {'error_log': e,
                        'has_errors':True}
                self.write(cr,uid,ids[0],vals)  
 
        return {'value': vals}
    
    def action_get_headers_csv(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):

            for attach in rec.attachment:
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
            header_csv_ids=header_csv_obj.search(cr, uid,[('import_data_id','=',ids[0])])
            
            if header_csv_ids:
                header_csv_obj.unlink(cr,uid,header_csv_ids,context=None)
            
            headers_list = []
            for header in partner_data[0]:
                headers_list.append(header.strip())
            n=0
            for header in headers_list:
                row+= 1
                fids = self.pool.get('ir.model.fields').search(cr,uid,[('field_description','ilike',header), ('model_id', '=', rec.model_id.id)])
                rid = self.pool.get('import.data.header').create(cr,uid,{'name':header,'index': row, 'csv_id':rec.id, 'model_field':fids and fids[0] or False, 'model':rec.model_id.id},context=context)
                
        return True
 
    def vision_match_field_label(self, cr ,uid,field_name, index ):         
        
        for fld_label in index:
            
            label_fld_name = fld_label.fldname.lower().strip()
                        
            if  label_fld_name == field_name:
                return fld_label.fldlabel.lower().strip()
        return None                                  
 
    def _match_import_header(self, cr,uid, model_id, field, field_label):
        """ Attempts to match a given header to a field of the
        imported model.

        :param str header: header name from the data file
        :param fields:
        :returns: False if the header couldn't be matched, or
                  the fields object
        :rtype: field object
        """
        #print field or '*' + '-' + field_label or '*'
        field = (field and field.strip().lower()) or '' 
        field_label = ( field_label and field_label.strip().lower()) or ''
        #print field + '-' + field_label
        
        search_domain =[('name','!=','display_name'), '&', ('model_id', '=', model_id),'|','|',('field_description','ilike',field),('field_description','ilike',field_label ),
                                                               '|',('name','ilike',field),('name','ilike',field_label)]
    
        #print search_domain   
        model_fields = self.pool.get('ir.model.fields')
        fields_odoo = model_fields.search(cr,uid,search_domain)
        fields_odoo = model_fields.browse(cr,uid,fields_odoo)
        if len(fields_odoo) == 1:
            return fields_odoo[0]
        
        for field_odoo in fields_odoo:
            
            field = field.strip().lower()
            odoo_description = field_odoo['field_description']
            odoo_description = (odoo_description and odoo_description.strip().lower()) or ''
            odoo_name =  field_odoo['name']
            odoo_name = (odoo_name and odoo_name.strip().lower()) or ''
        #    print field + ' == ' + odoo_name + ' or ' + odoo_description
            if field == odoo_description or field == odoo_name \
                    or field_label == odoo_description or field_label == odoo_name:
                return field_odoo

        return None    
        

    def search_record_exists(self, cr, uid, rec, data,header_dict, unique_fields=[]):
        if not unique_fields: return False
        ir_model_obj = self.pool.get('ir.model')
        ir_model_fields_obj = self.pool.get('ir.model.fields')
        
        dom = []
        for col in unique_fields:
            dom.append((col, '=', data[header_dict[col]]))
            
        obj = self.pool[rec.model_id.model]
        return obj.search(cr,uid,dom)
        
        #Todo Add Code here to  search on fields in header_dict which are flaged as Unique Record
        # for example a Name or Ref Field
        # if Found Return record ID (most also Consider is possible could be multiple records if search field not Truely unique Will update all these)
        # if not Found Return false
        
        
        return False  
    
    def action_import(self, cr, uid, ids, context=None):
        
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.dbf_path:
                self.action_import_dbf(cr, uid, ids, context)
                return
            if rec.rec.attachment:
                self.action_import_csv(cr, uid, ids, context)
                return
            
        raise osv.except_osv('Warning', 'No Data files to Import')
            
    def action_import_dbf(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}
        
        time_start = datetime.now()
        list_size =0 
        for rec in self.browse(cr, uid, ids, context=context):

            model_data_obj = self.pool.get('ir.model.data')
            model_model = rec.model_id.model
            model =  self.pool.get(model_model)
            
            dbf_table = dbf.Table(rec.dbf_path)
            dbf_table.open()
            list_size = len(dbf_table)
            row = 0
            count = 0
            error_log = ""
            for import_record in dbf_table:
                row+= 1
                domain_filter_skip = False
                vals = {}
                search_unique =[]
                external_id_ids = None
                is_field_unique_external = False
                external_id_name = False
                
                if  count >= rec.test_sample_size  and context.get('test',False):

                    t2 = datetime.now()
                    time_delta = (t2 - time_start)
                    time_each = time_delta / rec.test_sample_size                   
                      
                    estimate_time = (time_each * list_size)
                     
                    print "time_end,time_delta,estimate_time",t2,time_delta,estimate_time
                    msg = _('Time for %s records  is %s (hrs:min:sec) \n %s') % (list_size, estimate_time ,error_log)
                    if rec.rollback: cr.rollback()
                    vals = {'start_time':time_start.strftime('%Y-%m-%d %H:%M:%S'),
                            'end_time': time.strftime('%Y-%m-%d %H:%M:%S' ),
                            'error_log':error_log}
                
                    self.write(cr,uid,ids[0],vals)
                    return self.show_warning(cr, uid, msg , context = context)
            
                try:
                    o2m = {}
                    domain_filter_skip = False
                    for field in rec.header_ids:

                        if not field.model_field: continue # Skip where no Odoo field set
    
                        relation_id = False
                               
                        field_val =  field.name and import_record[field.name]  or False
                        field_type = type(field_val)
                        if field_type in (StringType, UnicodeType):
                            field_val = field_val.strip()
                            
                        if (not field_val or field_val == 0 or field_val == 0.0) and field.default_val:
                            field_val = field.default_val
                        
                        if field.search_filter and str(field_val) not in field.search_filter:
                            row-= 1 # this Record does not match filter skip to record in import Source
                            domain_filter_skip = True
                            break
                     
                        if field.model_field_type == 'many2one' and field_val:
                            substitutes = {}
                            for sub in field.m2o_substituions:
#                                 substitutes[str(sub.src_value).strip()] = str(sub.odoo_value).strip()
                                substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()})
                            field_val = str(field_val).strip()
                            field_val = substitutes.get(field_val, field_val)
                            related_obj = self.pool.get(field.relation)
                            field_val = field_val.strip()
                            
                            
                                
                            if field.search_related_external:
                                search = [('name','=',field_val),('model','=', model_model)]                     
                                ext_ids =  model_data_obj.search(cr,uid,search) or None
                                if ext_ids:
                                    res = model_data_obj.browse(cr, uid, ext_ids[0])
                                    relation_id = res and res.res_id
                            if field.search_name and not relation_id:
                                res = related_obj.name_search(cr,uid,name= field_val )
                                if res:
                                    relation_id = res[0][0] and False
                            if field.search_other_field and not relation_id:    
                                search = [(field.search_other_field.name,'=',field_val)]
                                res = related_obj.search(cr, uid, search)
                                relation_id = res and res[0]  or False
                            if relation_id: # Success found the related record
                                field_val = relation_id
                            else:  # No Related Record is Found decide to create or Skip
                                if field.create_related:
                                    try:
                                        id = related_obj.create(cr,uid,{'name':field_val},context = context)
                                        e = _(('Value \'%s\' Created for the relation field \'%s\'') % (field_val,field.model_field.name )) 
                                        error_log += '\n'+ e
                                        _logger.info( e)
                                        e = False
                                    except:
                                        
                                        e = _(('Error  \'%s\' not created for the relation field \'%s\'') % (field_val,field.model_field.name ))
                                        error_log += '\n'+ e
                                        field_val = False
                                        _logger.info( e)
                                        e = False
                                else: 
                                       
                                    e = _(('Value \'%s\' not found for the relation field \'%s\' related not set') % (field_val,field.model_field.name ))
                                    error_log += '\n'+ e
                                    field_val = False
                                    _logger.info( e)
                                    e = False
                                
                        elif field.model_field_type == 'date' and field_val :
                            
                            field_val = field_val.strftime("%Y-%m-%d")
                            
                        elif field.model_field_type == 'datetime' and field_val :
                            
                            field_val = field_val.strftime('%Y-%m-%d %H:%M:%S')
                            
                        elif field.model_field_type == 'boolean' and  field_val:
#                             field_val = field.model_field.name
                            field_val = bool(field_val)
                            
                        elif field.model_field_type == 'float' and  field_val:
#                             field_val = field.model_field.name
                            field_val = float(field_val)
                            
                        elif field.model_field_type == 'integer' and  field_val:
#                             field_val = int(field.model_field.name)
                            field_val = int(field_val)
                          
                        elif field.model_field_type == 'many2many' and  field_val:
                            #TODO: Add Functionality to handle Many2Many
                            field_val = False
                            
                        elif field.model_field_type == 'one2many' and  field_val:
                            if field.model_field.name in vals:
                                vals[field.model_field.name].update({'name':field_val})
                            else:
                                vals[field.model_field.name] = {'name':field_val}
                            field_val = False 
                        elif field.model_field_type == 'char' and  field_val:
                            field_val = str(field_val).strip()
                            
                        elif field_val: # Default Assumes is String
                            
                            field_val = str(field_val).strip()
                                
                        else :
                            # NO data field is False
                            pass
                            
                        
                        if field_val:
                            vals[field.model_field.name] = field_val
                        
                            if field.is_unique:
                                search_unique.append((field.model_field.name,"=", field_val))
                        
                            if field.is_unique_external:
                                is_field_unique_external = field_val
                    
                    
                    if domain_filter_skip : # this Record does not match filter skip to next Record in import Source
                        continue 
                    
                    if len(search_unique) > 0:      
                        search_ids = model.search(cr,uid,search_unique)
                    else:
                        search_ids = False
                        
                         
                    if search_ids and not rec.do_update:
                        e = ('Error Duplicate on Uniquie %s  Found at line %s record skipped') % (search_unique,row,)
                        _logger.info(_(e))
                        error_log += '\n'+ _(e)
                        continue
                                   
                    #  When using Record Row External ID
                    if is_field_unique_external:
                        external_id_name = is_field_unique_external   
                                         
                    #  When Using field for External ID                 
                    if rec.record_external:         
                        external_id_name = ('%s_%s' % ( rec.name.split('.')[0], row,))
                        
                    if external_id_name:
                        
                        search = [('name','=',external_id_name),('model','=', model_model)]                     
                        ext_ids =  model_data_obj.search(cr,uid,search) or None
                        if ext_ids:
                            res = model_data_obj.browse(cr, uid, ext_ids[0])
                            res_id = res and res.res_id or False
                     
                    if rec.do_update and  search_ids and res_id and res_id != search_ids[0]:
                        e = ('Error External Id and Unique not matching %s %s  Found at line %s record skipped') % (search_unique,external_id_name,row,)
                        _logger.info(_(e))
                        error_log += '\n'+ _(e)
                        e = False
                        continue
                     
                    if res_id and rec.do_update:
                        count += 1
                        model.write(cr,uid,res_id,vals,context=context)
                    elif not res_id and external_id_name:
                        
                        res_id = model.create(cr,uid,vals, context=context) 
                        external_vals = {'name':external_id_name,
                                         'model':model_model,
                                         'res_id':res_id,
                                         'module':''
                                         }
                        count += 1
                        model_data_obj.create(cr,uid,external_vals, context=context)
                        
                        _logger.info(_('Created record %s values %s external %s') % (row,vals,external_id_name))
                                     
                    elif external_id_ids and not rec.do_update:
                        e = ('Error Duplicate External %s ID  Found at line %s record skipped') % (external_id_name,row,)
                        _logger.info(_(e))
                        error_log += '\n'+  _(e)
                        e = False
                        continue
                 
                    else:
                        count += 1 
                        model.create(cr,uid,vals, context=context)       
                        
                        _logger.info(_('Created record %s values %s') % (row,vals,))
                        
                        
                except:
                    e = traceback.format_exc()
                    sys_err = sys.exc_info()
                    _logger.error(_('Error %s' % (e,)))
                    log_vals = {'error_log': sys_err,
                            'has_errors':True}
                    cr.rollback()
                    self.write(cr,uid,ids[0],log_vals)
                    return vals
        log_vals = {'start_time':time_start.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': time.strftime('%Y-%m-%d %H:%M:%S'),
                'error_log':error_log}
        if context.get('test',False) and rec.rollback:
            cr.rollback()
        self.write(cr,uid,ids[0],log_vals)
        result = {} 
        result['value'] = log_vals   
        return result        
     

    
    def action_import_csv(self, cr, uid, ids, context=None):

        start = time.strftime('%Y-%m-%d %H:%M:%S')       
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            
            if not rec.header_ids:
                raise osv.except_osv('Warning', 'No Header selected in Header list')
            
            
            for attach in rec.attachment:
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
            for hd in rec.header_ids:
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
                n+= 1
                
                record_ids = self.search_record_exists(cr,uid,rec,data,headers_dict,unique_fields)
                print record_ids 
                if record_ids and not rec.do_update: 
                    
                    #TODO  need to add the Unique Record Field and Value Found to this Log
                    
                    _logger.info(_('Error Duplicate Name Found at line %s record skipped') % (n))
                    error_log += _('Error Duplicate Name Found at line %s record skipped\n') %(n)
                    
                    continue
                    
                # Create Vals Dict    
                vals ={}
                for hd in rec.header_ids:
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
                        
                try:
                    if record_ids:
                        self.pool.get(rec.model_id.model).write(cr, uid, record_ids, vals )
                        _logger.info('Update  Line Number %s  ' % n)

                    else:
                        self.pool.get(rec.model_id.model).create(cr, uid, vals, context=context)
                        _logger.info('Imported Line Number%s  ' % n)
                 
                except:
                    e = sys.exc_info() + '\n' + traceback.format_exc()
                    _logger.info(_('Error  %s record not created for line Number %s') % (e,n,))
                    error_log += _('Error  %s at Record %s --\n') % (e,n, ) 
                  
                  
                # This is only a Test Roll Back Records exit loop and create POP UP With Info statistic about Import 
                                       
                
                if n== rec.test_sample_size  and context.get('test',False):
                    try:
                        t2 = datetime.now()
                        time_delta = (t2 - time_start)
                        time_each = time_delta / rec.test_sample_size
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

                    
        vals = {'start_time':start,
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
    
    def onchange_model(self, cr, uid, ids, model_id=False,  context=None):
        if not ids:
            return {}
        if model_id:
            header_ids_vals = []
            header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0])])
            for rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):
                  
                odoo_field_id = self._match_import_header(cr, uid, model_id, rec.name, rec.field_label)
                vals = { 'model_field':odoo_field_id,
                        'model': model_id,
                        }
                header_ids_vals.append((1,rec.id, vals))
                
            return{'value':{"header_ids":header_ids_vals}}
    
        else:
            return {}
    def record_forward(self,cr,uid,ids,context=None):
        
        rec= self.browse(cr,uid,ids[0],context)
        rec.record_num += 1
        self.onchange_record_num(cr, uid, ids, rec.record_num)

        
    def record_backward(self,cr,uid,ids,context=None):
        rec= self.browse(cr,uid,ids[0],context)
        if rec.record_num >1:
            rec.record_num -= 1
            self.onchange_record_num(cr, uid, ids, rec.record_num)
            return {"value":{"record_num":rec.record_num}}
        return
                
    def onchange_record_num(self,cr,uid,ids,record_num, context=None):
        
        if context is None:
            context = {}
        
        header_ids_vals = []
        if record_num > 0:

            for rec in self.browse(cr, uid, ids, context=context):
            
                dbf_table = dbf.Table(rec.dbf_path)
                if not dbf_table:
                    
                    e = 'Error opening DBF Import  %s:'  % (rec.dbf_path, )
                    _logger.error(_('Error %s' % (e,)))
                    raise osv.except_osv('Warning', e)
                    
                dbf_table.open()
                dbf_table_rec = dbf_table[record_num-1]   
                
                header_ids_vals = []
                header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0])])
                for header_rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):
                
                    vals = {  'field_val':dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False}
                    header_ids_vals.append((1,header_rec.id, vals))
                    header_rec.write({"field_val":dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False})
                
                

            return{'value':{"header_ids":header_ids_vals}}
    
        else:
            return {}    
     
     
class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'    

    _defaults = {
                 'model_id': lambda self,cr,uid,ctx=None: (ctx and ctx.get('default_model_id',False)),  
                 }        
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
