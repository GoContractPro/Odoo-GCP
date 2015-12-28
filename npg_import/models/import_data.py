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
import datetime 
import logging 
import sys, traceback
import contextlib
from string import strip

from __builtin__ import False
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT 
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
import base64


_logger = logging.getLogger(__name__)

SOURCE_TYPES = []
 
SOURCE_TYPES.append(('csv', 'CSV'))

try:
    import dbf
    SOURCE_TYPES.append(('dbf', 'DBF File'))  
except:
    _logger.info("Python DBF not available. Please install dbf python package."  )
    
try:
    import pyodbc  
    SOURCE_TYPES.append(('odbc', 'ODBC Connection'))
     
except:
    _logger.info("Python ODBC not available. Please install pyodbc python package."  )
    
row_count = 0
count = 0

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
    _inherit = 'import.data.header'
    
    _columns = { 
                'import_field_id':fields.many2one('import.data.header', 'Field', required=True, ondelete='cascade'),
                }
    
    def _get_model(self,cr,uid,context=None):
        return context.get('default_model',False)
    def _get_import_id(self,cr,uid,context=None):
        return context.get('default_import_id',False)
    
    _defaults = {
                 'model':_get_model,
                 'import_data_id':_get_import_id,
                 }
         
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
            'start_time': fields.datetime('Start Time',  readonly=True),
            'end_time': fields.datetime('End Time',  readonly=True),
            'attachment': fields.many2many('ir.attachment',
                'data_import_ir_attachments_rel',
                'import_data_id', 'attachment_id', 'CSV File'),
            'error_log': fields.text('Status Log'),
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
            'row_count':fields.integer("Rows Processed"),
            'count':fields.integer("Rows Imported"),
            'time_estimate':fields.float("Time Estimate"),
            'start_row':fields.integer("Import Start Row"),
            'base_external_dbsource' : fields.many2one('base.external.dbsource', string="ODBC Connection", help="External Database connection to foreign databases using ODBC, MS-SQL, Postgres, Oracle Client or SQLAlchemy."),
            'src_table_name' : fields.char('Source Table Name',size=256),
            'src_type' : fields.selection(SOURCE_TYPES, "Data Source Type", required=True),
            'sql_source': fields.text('SQL', help='Write a valid "SELECT" SQL query to fetch data from Source database'),
            'schedule_import': fields.many2one('ir.cron','Related Source Table'),
            
            'state': fields.selection([('draft','Draft'),('map','Mapping Fields'),('ready','Map Confirmed'),('importing','Import Running')], "Status"),
            }
    
    _defaults = {
        'test_sample_size':10,
        'record_num':1,
        'src_type':'csv',
        'state': 'draft',
        }

    
    def import_schedule(self, cr, uid, ids, context=None):
        cron_obj = self.pool.get('ir.cron')
        for imp in self.browse(cr, uid, ids, context):
            cron_id = False
            if not imp.schedule_import:
                new_create_id = cron_obj.create(cr, uid, {
                    'name': 'Import ODBC tables',
                    'interval_type': 'hours',
                    'interval_number': 1,
                    'numbercall': -1,
                    'model': 'import.data.file',
                    'function': 'action_import',
                    'doall': False,
                    'active': True
                })
                imp.write({'schedule_import':new_create_id})
                cron_id = new_create_id
            else:
                cron_id = imp.schedule_import.id
        return {
            'name': 'Import ODBC tables',
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'ir.cron',
            'res_id': cron_id,
            'type': 'ir.actions.act_window',
        }
    
    
    

    def onchange_record_external(self,cr,uid, ids, record_external, context=None):
        
        if record_external:
            return {'value': {'external_id_field': False}}
        

    def action_set_confirmed(self,cr, uid,ids,context=None):
        vals = {'state':'ready'}
        self.write(cr,uid,ids[0],vals)
        return{'value':vals}
        
    def action_get_headers(self, cr, uid, ids, context=None):
        
        for rec in self.browse(cr, uid, ids, context=context):
            if rec.src_type == 'dbf':
                self.action_get_headers_dbf(cr, uid, ids, context)
                
            elif rec.src_type == 'csv':
                self.action_get_headers_csv(cr, uid, ids, context)
                
            elif rec.src_type == 'odbc':
                self.action_get_headers_odbc(cr, uid, ids, context)
            
            vals = {'state':'map'}
            self.write(cr,uid,ids[0],vals)
            return{'value':vals}
            
        raise osv.except_osv('Warning', 'No Data files to Import')
    
    def get_label_match_index(self, cr, uid, dbf_table ):
        
        
        dbf_path = dbf_table.filename
        dbf_directory = os.path.dirname(dbf_path)
        table_name = os.path.basename(dbf_path).split('.')[0]

        fldlabel_path = dbf_directory + '/FLDLABEL.DBF'
        fldlabel_dbf_table = dbf.Table(fldlabel_path)
        fldlabel_dbf_table.open()
        
        if not fldlabel_dbf_table:
            
            e = 'No Labels Table found at DBF Path %s:'  % (fldlabel_path, )
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
                            'model':rec.model_id and rec.model_id.id,
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
                sys_info = sys.exc_info()[1][1]
                e = 'Error opening DBF Import  %s: \n%s \n%s' % (rec.dbf_path, sys_info[1],sys_info) 
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
            row = 0
            for header in headers_list:
                row+= 1
                fids = self.pool.get('ir.model.fields').search(cr,uid,['|',('field_description','ilike',header),('name','ilike',header), ('model_id', '=', rec.model_id.id)])
                rid = self.pool.get('import.data.header').create(cr,uid,{'name':header,'index': row, 'csv_id':rec.id, 'model_field':fids and fids[0] or False, 'model':rec.model_id.id},context=context)
                
        return True
    
    def action_get_headers_odbc(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            
            src_table = str(rec.src_table_name).strip()
            if rec.sql_source:
                qry = str(rec.sql_source)
            else:
                qry = "select TOP 1 * from %s" % src_table
                
            result = rec.base_external_dbsource.execute(sqlquery=qry,metadata=True)
            if not result.has_key('cols'):
                continue
            has_row = result.has_key('rows')
            header_csv_obj = self.pool.get('import.data.header')
            header_csv_ids=header_csv_obj.search(cr, uid,[('import_data_id','=',ids[0])])
            
            if header_csv_ids:
                header_csv_obj.unlink(cr,uid,header_csv_ids,context=None)
            
            headers_list = result['cols']
            row_data = result['rows']
            n=0
            for col in headers_list:
                
                header = col[0]
                fld_obj = self._match_import_header(cr, uid, rec.model_id.id, header, header)    

                vals = {'name':header, 'import_data_id':rec.id,
                            'model_field':fld_obj and fld_obj.id or False,
                            'model':rec.model_id and rec.model_id.id,
                            'field_label': header or False,
                            'field_type':col[1],
                            'field_val' : False,
                            }
                if has_row:
                        if not  isinstance(row_data[n], bytearray):
                            vals.update({'field_val' : row_data[n],})
                        
                        else:
                            vals.update({'field_val' : "Binary"})
                        n += 1
                self.pool.get('import.data.header').create(cr,uid,vals,context=context)
                
            conn = self.pool.get('base.external.dbsource').conn_open(cr, uid, rec.base_external_dbsource.id)
            cur = conn.cursor()
            tot_records = self.get_row_count_odbc(qry, cur)
               
            vals = {'error_log':'Successful Header Import',
                    'has_errors':False,
                    'tot_record_num':tot_records, 
                    }
            self.write(cr,uid,ids[0],vals)    
                
                
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

             
    def convert_backslash_string(self,s):
        
        if '//' in s:
            if isinstance(s, str):
                s = s.encode('string-escape')
            elif isinstance(s, unicode):
                s = s.encode('unicode-escape')
            return s
        else:
            return s
    
    def get_field_val_from_record(self, import_record, rec, field):        
        
        if not field.name:
            return field.default_val
                
        if rec.src_type == 'dbf':
            field_raw =  import_record[field.name] or False
        elif rec.src_type == 'csv':
            field_raw = field.name and import_record[field.name]  or False
        elif rec.src_type == 'odbc':
            field_raw =  field.name and getattr(import_record, field.name )  or False
        else: raise ValueError('Error! Source Data Type Not Set')
        
        
        if not field_raw and field.default_val:
            return field.default_val
        elif not field_raw:
            return False
        else: 
            if isinstance( field_raw, str):
                field_val = field_raw.strip()
    
            elif isinstance(field_raw, unicode):
                field_val =  field_raw.strip()
    
            elif isinstance(field_raw, datetime.datetime):
                field_val =  field_raw.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            
            elif isinstance(field_raw , datetime.date):
                field_val =  field_raw.strftime(DEFAULT_SERVER_DATE_FORMAT)
    
            elif isinstance(field_raw, bytearray):
                field_val =  base64.b64encode(field_raw)
            else: field_val =  str(field_raw)

            return field_val
     
    def skip_current_row_filter(self, field_val, search_filter):
        
        if not  search_filter or search_filter == '[]':
            return False
        
        
        search_filter =  search_filter.replace('[','')
        search_filter =  search_filter.replace(']','')
        
        search_list = tuple(search_filter.split(','))
        if not search_list:
            search_list.append(search_filter)
            
        if field_val in search_list:
            return False
            
        else:
            return True
    
    def do_substitution_mapping(self,field_val,substituions):
        
        substitutes = {}
        if substituions:
            for sub in substituions:
                substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()})
                
        return substitutes.get(field_val, field_val)
                    
     
    def search_records(self, cr,uid, field_search_val, field, context=None ): 
            
        related_obj = self.pool.get(field.relation)
                  
            
        if related_obj:
    
            if field.search_related_external:
                search = [('name','=',field_search_val),('model','=', field.relation)]                     
                ext_ids =  self.pool.get('ir.model.data').search(cr,uid,search) or None
                if ext_ids:
                    res = self.pool.get('ir.model.data').browse(cr, uid, ext_ids[0])
                    return res and res.res_id or False
                
            if field.search_name:
                self.convert_backslash_string( field_search_val)
                res = related_obj.name_search(cr,uid,name=field_search_val )
                return res and res[0][0]
                    
            if field.search_other_field:    
                search = [(field.search_other_field.name,'=',field_search_val)]
                res = related_obj.search(cr, uid, search)
                return res and res[0]  or False
        
        return False
                
    def create_related_record(self, cr, uid, ids,rec,import_record, field, field_val, context= None ):
        
        vals = False
        try:
            odoo_vals = self.do_related_vals_mapping(cr, uid, ids, rec=rec, field=field, import_record=import_record,  context=context)
            if odoo_vals['required_missing']:
                res_id = False
            else:
                vals = odoo_vals['field_val']
                res_id =  self.pool.get(field.relation).create(cr,uid, vals ,context = context) or False
            
            if not res_id:
                log = _('Warning!: Related record for  value \'%s\' Not Created for relation \'%s\' row %s' % ( field_val, field.relation,row_count )) 
                rec.error_log += '\n'+ log
                _logger.info( log)
                return   False 
            
            #if searching on related external IDs then create the related  external ID based on  field_val used to search 
            if res_id and field.search_related_external: 
                vals = {'name':field_val,
                    'model': field.relation,
                    'res_id':res_id,
                    'module':field.relation
                    }

                self.pool.get('ir.model.data').create(cr,uid,vals, context=context)
            
            log = _('Related record ID %s : value \'%s\' Created for relation \'%s\' row %s' % (res_id, field_val, field.relation,row_count )) 
            rec.error_log += '\n'+ log
            _logger.info( log)    
            
            return res_id
            
        except:
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Error: Related record vals \'%s\'  for model \'%s\'' % (vals or 'No Values Dictionary Created' ,field.relation))
            self.update_log_error(cr, uid, ids, rec, error_txt, context)
            
            return False
     
    def create_import_record(self, cr, uid, ids, rec, vals, external_id_name = False, model=False, context=None): 
        
        try:
            res_id = False
            
            model = model or rec.model_id.model
            
            model_obj = self.pool.get(model)

            res_id = model_obj.create(cr,uid, vals, context)
              
            if external_id_name:                   
                external_vals = {'name':external_id_name,
                                 'model':rec.model_id.model,
                                 'res_id':res_id,
                                 'module':rec.model_id.model
                                 }
                
                self.pool.get('ir.model.data').create(cr,uid,external_vals, context=context)
                
            _logger.info(_('Created record %s ID: %s from Source row %s' % (external_id_name or '',res_id, row_count)))

            return res_id

        except:
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Error: Import vals %s not created for model \'%s\'' % (vals, model))
            self.update_log_error(cr, uid, ids, rec, error_txt, context)
            
            return False
   
    def search_external_id(self, cr, uid, external_id_name, model, context = None):
        
                
        search = [('name','=',external_id_name),('model','=', model)]                     
        ext_ids =  self.pool.get('ir.model.data').search(cr,uid,search) or None
        if ext_ids:
            res = self.pool.get('ir.model.data').browse(cr, uid, ext_ids[0])
            return res and res.res_id or False
        
        return False
    
    def update_log_error(self, cr, uid, ids,rec, error_txt = '', context = None):

        e = traceback.format_exc()
        
        if row_count:
            error_txt = 'Row: ' + str(row_count) + ' ' + error_txt
        logger_msg = error_txt + '\n' + 'TraceBack: ' + e[:2000]
        _logger.error(logger_msg)
        
        e = sys.exc_info()
        e = traceback.format_exception(e[0], e[1], e[2], 1)
        error_msg = e[2]
         
        rec.error_log +=  error_txt + '\n' + error_msg +'\n' 
        log_vals = {'error_log': rec.error_log,
                'has_errors':rec.has_errors}
        self.write(cr,uid,ids,log_vals)
        cr.commit()
        return log_vals
    
    def check_external_id_name(self, cr, uid, rec, external_id_name = False):  
           
        #  When Using field for External ID 
        if external_id_name:
            return external_id_name 
        #  When using Record Row External ID and No field External ID            
        elif rec.record_external:         
            return ('%s_%s' % ( rec.name.split('.')[0],row_count,))
        else:
            return False  
                 
    
    def do_related_vals_mapping(self, cr, uid, ids, rec, field,  import_record, context=None):
        vals={}
        for rel_field in field.m2o_values:

            field_val = self.get_field_val_from_record(import_record, rec = rec, field=rel_field)
           
            odoo_vals = self.convert_odoo_data_types(cr, uid, ids, rec=rec, field= rel_field, field_val=field_val, import_record = import_record, context=context)  
            if odoo_vals['required_missing']:
                vals = None
                break 
            
            vals[rel_field.model_field.name] = odoo_vals['field_val']
                                                 
            #TODO add functionality to build other Relate values defaults from list or other Tables
        return {'required_missing':odoo_vals['required_missing'], 'field_val': vals}
        
    def convert_odoo_data_types(self, cr, uid, ids, rec, field, field_val, import_record=None, rec_val=None, context = None):
        
        
        if field.model_field_type == 'many2one' and field_val:
            
            res_id = self.search_records(cr, uid, field_search_val=field_val, field=field, context=context)
            
            if not res_id and field.create_related: 
                # If Success found the related record 
                res_id = self.create_related_record(cr, uid, ids,rec=rec, import_record=import_record, field=field, field_val=field_val, context=context)
                
            field_val = res_id
        
        elif field.model_field_type == 'boolean' and  field_val:
            try:
                field_val = bool(field_val)
            except:
                rec.has_errors = True
                field_val = False
                error_txt = ('Error: Field %s -- %s is not required Boolean type' % (field.model_field.name,field_val,))
                self.update_log_error( cr, uid, ids, rec, error_txt, context)
            
        elif field.model_field_type == 'float' and  field_val:
                
            if field_val.lower() == 'false': field_val = '0.0'
            
            try:
                field_val = float(field_val)
            except:
                rec.has_errors = True
                field_val = 0.0
                error_txt = _('Error: Field %s -- %s is not required  Floating Point type' % ( field.model_field.name,field_val))
                self.update_log_error( cr, uid, ids, rec, error_txt, context)

        elif field.model_field_type == 'integer' and  field_val:
              
            if field_val.lower() == 'false': field_val = '0'
            try:
                field_val = int(field_val)
            except:
                rec.has_errors = True
                field_val = 0
                error_txt = _('Error:  Field %s -- not required Integer  type' % (field.model_field.name,field_val))
                self.update_log_error( cr, uid, ids, rec, error_txt, context)

        elif field.model_field_type == 'selection' and  field_val:
            pass
        
        elif field.model_field_type in ['char', 'text','html'] and  field_val:
            pass
        elif field.model_field_type == 'binary' and  field_val: 
            pass
        elif field.model_field_type in ['one2many','many2many']:
   
            m2o = self.get_o2m_m2m_vals(cr, uid, ids,field=field, rec=rec, field_val=field_val, import_record=import_record, context=context) 
            
            if rec_val:
                if m2o: m2o['field_val'] = rec_val.append(m2o['field_val'])
               
            else:
                if m2o: m2o['field_val'] = [m2o['field_val']]
                
            return m2o
         
        # If field is marked as Unique in mapping append to search on unique to use to confirm no duplicates before creating new record    
        if field.model_field.required and not field_val:
            rec.has_errors = True
            error_txt = _('Error: Required field %s  has no value ' % (field.model_field.name ))
            self.update_log_error( cr, uid,ids,rec, error_txt, context)
            required_missing =  True
        else: required_missing =  False
        
        return {'required_missing':required_missing,'field_val':field_val}
                            
    def get_o2m_m2m_vals(self, cr, uid, ids, field, rec, field_val, import_record, context = None ): 
        
        external_id_name = field_val
        if field.o2m_external_field2:
            external_id_name += '--' + self.get_field_val_from_record(import_record,  rec, field.o2m_external_field2)
       
        res_id = self.search_external_id(cr, uid, external_id_name, model = field.relation , context=context)
        
        if res_id:
            return (4,res_id)
        elif field.create_related:
            odoo_vals = self.do_related_vals_mapping(cr, uid, ids, rec=rec, field=field, import_record=import_record, context=context)
            if odoo_vals['required_missing']: 
                return odoo_vals
            else:
                res_id = self.create_import_record(cr, uid, ids, rec=rec, vals=odoo_vals['field_val'], external_id_name=external_id_name, 
                                                    model = field.relation, context=context)
                if res_id:return {'required_missing':False, 'field_val':(4,res_id)}
                else: return None
        else:
            return None
        
    def update_statistics(self, cr, uid, ids, rec, remaining=True):   
        '''params:
        rec: The main record set for import File
        processed_rows: Current number of Rows processed from Data Source
        count: Total number of Rows actually imported without Skipped
        
        '''

        estimate_time = self.estimate_import_time( rec, processed_rows=row_count, remaining=remaining)    
            
        stats_vals = {'start_time':rec.start_time,
                    'end_time': False,
                    'error_log': rec.error_log,
                    'time_estimate': estimate_time,
                    'row_count': row_count,
                    'count': count}
        
        if not remaining:
            stats_vals['end_time'] =  datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)  
            if rec.has_errors:stats_vals['state'] = 'map'
            else: stats_vals['state'] = 'ready'
            
                        
        self.write(cr,uid,ids,stats_vals) 
        
        return stats_vals
        
    def estimate_import_time(self, rec, processed_rows, remaining = True):
        '''params:
        start_time: Time in string format YYYY-MM-DD HH:MM:SS when import started
        processed_rows: Current number of Rows processed from Data Source
        tot_record_num: Total number of Rows in data Source
        remaining: Boolean if Tru return time left in import if false return total Estimated time
        '''
        t2 = datetime.datetime.now()
        time_delta = (t2 - datetime.datetime.strptime(rec.start_time, DEFAULT_SERVER_DATETIME_FORMAT))
        if processed_rows > 0:
            time_each = time_delta / processed_rows
            time_each = time_each.total_seconds()
        else: time_each = 0.0
        
        if remaining:
            
            return (time_each * (rec.tot_record_num - processed_rows)) / 3600 # return time in hours
                          
        else:
            return (time_each * rec.tot_record_num) / 3600 
          
    def get_row_count_odbc(self,qry,cur):
        
        pos = qry.lower().find('from')
        count_qry = qry[pos-1:]
        count_qry = 'select count(*) as rows ' + count_qry
        cur.execute(count_qry)
        count_result = cur.fetchone()
        for tot_count in count_result:
            return tot_count
            
        return False
    
    def do_process_import_row(self, cr, uid, ids, rec, import_record, context):

        global row_count
        global count
        
        vals = {}
        search_unique =[]
        
        external_id_name = ''
        skip_record = False
        row_count += 1
       
        if row%25 == 0: # Update Statics every 10 records
            self.update_statistics(cr,uid ,ids ,  rec=rec, remaining=True)
                    
        for field in rec.header_ids:

            try:   # Building Vals DIctionary
                if not field.model_field: continue                       
                res_id = False
                field_val = False
                
                # test  Clean and convert Raw incoming Data values to stings to allow comparing to search filters and substitutions         
                field_val = self.get_field_val_from_record(import_record, rec, field)
                if not field_val:continue
                    
                
                # IF Field value not found in Filter Search list skip out to next import record row
                if self.skip_current_row_filter(field_val,field.search_filter):
                    return False                          
                
               
                if not field.model_field: continue # Skip to next Field if no Odoo field set
                
                if field.is_unique_external:
                    if external_id_name != '': external_id_name += '/'
                    external_id_name += field_val
                
                # Update Field value if Substitution Value Found. 
                field_val = self.do_substitution_mapping(field_val,field.substitutions)
                
                #Convert to Odoo Data types and add field to Record Vals Dictionary
                odoo_vals = self.convert_odoo_data_types(cr, uid, ids, rec=rec, field=field, field_val=field_val, import_record=import_record,
                                                                             rec_val=vals.get(field.model_field.name,False),  context=context)
                if odoo_vals and odoo_vals['required_missing']:
                    return False
                     
                # If field is marked as Unique in mapping append to search on unique to use to confirm no duplicates before creating new record    
                if field.is_unique and not field_val:
                    
                    error_txt = _('Error: Required unique field %s is not set' % (field.model_field.name))
                    self.update_log_error( cr, uid,ids,rec, error_txt, context)
                    skip_record = True
                    return False
                 
                elif field.is_unique:
                    search_unique.append((field.model_field.name,"=", field_val))
                    
                vals[field.model_field.name] = odoo_vals['field_val']
                                                            
            except: # Buidling Vals DIctionary
                cr.rollback()
                rec.has_errors = True
                error_txt = _('Error: Building Vals Dict for Field: %s == %s \n  %s ' %(field.model_field.name, field_val, vals,))
                self.update_log_error( cr, uid, ids,rec, error_txt, context)
                skip_record = True
                return False
        
        if skip_record : # this Record does not match filter skip to next Record in import Source
            return False
        
        try:  # Finding existing Records  
            
            if len(search_unique) > 0:      
                search_ids = self.pool.get(rec.model_id.model).search(cr,uid,search_unique)
            else:
                search_ids = False
                
            external_id_name = self.check_external_id_name(cr, uid, rec=rec, external_id_name = external_id_name)

            if external_id_name:
            
                res_id = self.search_external_id(cr, uid, external_id_name, rec.model_id.model, context)
                    
                if rec.do_update and  search_ids and res_id and res_id != search_ids[0]:
                    error_txt = _('Error: External Id and Unique Field not Id not matched  %s %s record skipped' % (search_unique, external_id_name,))
                    self.update_log_error( cr, uid, ids, rec, error_txt, context)
                    
                    return False

            elif search_ids and not rec.do_update:
                    error_txt = _('Error: Duplicate records on unique fields %s  found, record skipped' % (search_unique,))
                    self.update_log_error( cr, uid, ids, rec, error_txt, context)
                    return False
                
            elif search_ids:
                res_id = search_ids[0] 
            else:
                res_id = False   
                
            
        except: # Finding Existing Records
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Error: Search for Existing records: %s-%s ' % (search_unique,external_id_name))
            self.update_log_error(cr, uid, ids, rec, error_txt, context)                    
            return False
        
        try: # Writing or Create Records          
            
            if res_id and rec.do_update:
                
                self.pool.get(rec.model_id.model).write(cr,uid,res_id, vals,context=context)
                _logger.info(_('Updated row %s Odoo Database ID: %s') % ( row_count, res_id,))
            
            elif res_id and not rec.do_update:
                
                error_txt = _('Error: External ID: %s Already exists in Database, record was skipped') % (external_id_name,)
                self.update_log_error( cr, uid, ids, rec, error_txt, context)
                return False
         
            else: # no record Found So Create new record
                
                self.create_import_record(cr, uid, ids, rec=rec, vals=vals, external_id_name=external_id_name, context=context)
                
            count += 1
            return count
        
        except: # Error Writing or Creating Records
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Writing or Creating vals %s ' % ( vals,))
            self.update_log_error(cr, uid, ids, rec, error_txt, context)
            return False
  
    def action_import_cron(self, cr, uid, ids, context=None):
        
        for rec in self.browse(cr, uid, ids, context=context):      
                   
            vals={'name': 'Import %s' % (rec.name),
                    'user_id': uid,
                    'model': 'import.data.file',
                    'function':'action_import',
                    'args': repr([ids[0]])\
                    }
                 
            self.pool.get('ir.cron').create(cr, uid, vals)
                
            stats_vals = {'start_time':False,
                'end_time': False,
                'error_log': '',
                'time_estimate': False,
                'row_count': False,
                'count': False,
                'state': 'importing'}   
            
            self.write(cr,uid,ids,stats_vals)
            cr.commit()
            return stats_vals
        
            
        raise osv.except_osv('Warning', 'No Data files to Import')
    
    def check_test_mode(self,cr, rec, test_mode):
        
        
        if  test_mode and (count >= rec.test_sample_size  or row_count >= rec.test_sample_size + 100) :
            
            if rec.rollback: cr.rollback()
            # Exit Import Records Loop  
            return True
        elif not test_mode:
            cr.commit()
            
        return False
        
    def action_import(self, cr, uid, ids, context={}): 
      
        for rec in self.browse(cr, uid, ids, context=context):
            
            if not rec.header_ids:
                raise osv.except_osv('Warning', 'No Fields import map')
            
            test_mode = context.get('test',False)
            
            rec.has_errors = False
            rec.error_log = '' 
            rec.row_count = 0
            rec.count = 0
            rec.start_time = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            
            self.update_statistics(cr, uid, ids, rec, remaining = True)
            cr.commit()
         
            if rec.src_type == 'dbf':
                return self.action_import_dbf(cr, uid, ids, rec, test_mode, context)
                
            elif rec.src_type == 'csv':
                return self.action_import_csv(cr, uid, ids, rec, test_mode, context)
                
            elif rec.src_type == 'odbc':
                return self.action_import_odbc(cr, uid, ids, rec, test_mode, context)
                

    def action_import_dbf(self, cr, uid, ids, rec, test_mode, context=None):
        
        if context is None:
            context = {}
        
        try:
           
            dbf_table = dbf.Table(rec.dbf_path)
            dbf_table.open()
            rec.tot_record_num = len(dbf_table)
   
            for import_record in dbf_table:
                
                self.do_process_import_row(cr, uid, ids, rec, import_record, context)
                
                if self.check_test_mode(cr, rec, test_mode):
                    return{'value':self.update_statistics(cr, uid, ids, rec=rec, remaining=False)}
        except:
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error( cr, uid, ids, rec, error_txt, context)
        
        return {'value':self.update_statistics(cr, uid, ids, rec=rec, remaining=False)}
    
    def action_import_odbc(self, cr, uid, ids, rec, test_mode = False, context={}):
        
        conn = False 
        
        try:
            qry = self.odbc_import_query(rec, test_mode)
                            
            conn = self.pool.get('base.external.dbsource').conn_open(cr, uid, rec.base_external_dbsource.id)
            cur = conn.cursor()
            
            rec.tot_record_num = self.get_row_count_odbc(qry, cur)
            cur.execute(qry)
            
            all_data = True
            while all_data:
                all_data = cur.fetchmany(500)
                if not all_data:
                    break
                for import_record in all_data:
                    
                    self.do_process_import_row(cr, uid, ids, rec, import_record, context)
                   
                    if self.check_test_mode(cr, rec, test_mode):
                        return{'value':self.update_statistics(cr, uid, ids, rec=rec, remaining=False)}
                        
            conn.close()
        except:
            cr.rollback()
            if conn:
                conn.close()
            rec.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error( cr, uid, ids, rec, error_txt, context)
        
        return{'value':self.update_statistics(cr, uid, ids, rec=rec, remaining=False)}
       
    def odbc_import_query(self, rec, test_mode):
        
        src_table = str(rec.src_table_name).strip()  
        if rec.sql_source:         
            qry = str(rec.sql_source)
        elif test_mode:
            qry = "select TOP %s * from %s" % (rec.test_sample_size, src_table)
        else:
            qry = "select * from %s" % src_table

        return 'set textsize 2147483647 ' + qry
    
    def action_import_csv(self, cr, uid, ids, rec, test_mode, context={}):

        try:    
            csv_data = self.get_csv_data_file(cr, uid, ids, rec, context)
            header_dict = self.get_csv_header_dict(rec, csv_data)
            
            for csv_row in csv_data[1:]:

                import_record = self.convert_cvs_row_dict(cr,uid,ids,header_dict,csv_row,context)
                 
                self.do_process_import_row(cr, uid, ids, rec, import_record, context)
                
                if self.check_test_mode(cr, rec, test_mode):
                    return{'value':self.update_statistics(cr, uid, ids, rec=rec, remaining=False)}
                    
        except:
            cr.rollback()
            rec.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error( cr, uid, ids, rec, error_txt, context)
        
        return {'value':self.update_statistics(cr, uid, ids, rec=rec, remaining=False)}
       
    def get_csv_data_file(self, cr, uid, ids,rec , context = {}):
        
        try:
            # open only the first Attachment no other attachments valid
            for attach in rec.attachment:
                data_file = attach.datas
                continue
            
            str_data = base64.decodestring(data_file)
            
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            
            return list(csv.reader(cStringIO.StringIO(str_data)))
            
        except:
            error_txt = "Error: Unable to open CSV Data"
            self.update_log_error( cr, uid, ids, rec, error_txt, context)
            raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            return False
   
    def get_csv_header_dict(self, rec, csv_data):
        
        headers_list = []
        for header in csv_data[0]:
            headers_list.append(header.strip())
        
        header_map = {}
        
        for hd in rec.header_ids:
            if hd.model_field:
                label = hd.model_field.field_description or ''
                header_map.update({hd.model_field.name : hd.name})
                    
        if not header_map:
            raise osv.except_osv('Warning', 'No Header mapped with Model Field in Header line!')
                    
        headers_dict = {}
        for field, label in header_map.iteritems():  
            headers_dict[field] = index_get(headers_list,label)   
    
        return headers_dict
    
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

        if record_num < 1:
            raise    osv.except_osv('Warning', "The Record Number must be positive value")
            return {}

        for rec in self.browse(cr, uid, ids, context=context):
            header_ids_vals = []
            if rec.src_type == 'odbc':
                raise   osv.except_osv('Warning', "Record set Values  is not available on ODBC")
                return {}        
    
            elif rec.src_type == 'csv':
                raise   osv.except_osv('Warning', "Record set Values  is not available on CSV")
                return {}
    
            elif rec.src_type == 'dbf':
                       
                dbf_table = dbf.Table(rec.dbf_path)
                if not dbf_table:
                
                    e = 'Error opening DBF Import  %s:'  % (rec.dbf_path, )
                    _logger.error(_('Error %s' % (e,)))
                    raise osv.except_osv('Warning', e)
            
                dbf_table.open()
                dbf_table_rec = dbf_table[record_num-1]   
        
                header_ids_vals = []
                header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0]),('name','!=',False)])
                for header_rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):
        
                    vals = {  'field_val':dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False}
                    header_ids_vals.append((1,header_rec.id, vals))
                header_rec.write({"field_val":dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False})
                
                
            else:
                return {}    
    
            header_ids_vals = []
            header_ids = self.pool('import.data.header').search(cr,uid,[('import_data_id','=',ids[0]),('name','!=',False)])
            for header_rec in self.pool('import.data.header').browse(cr,uid, header_ids, context = context):

                    vals = {  'field_val':dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False}
                    header_ids_vals.append((1,header_rec.id, vals))
        
            header_rec.write({"field_val":dbf_table_rec and header_rec and dbf_table_rec[header_rec.name] or False})
    
            return{'value':{'header_ids':header_ids_vals}}

     
class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'    

    _defaults = {
                 'model_id': lambda self,cr,uid,ctx=None: (ctx and ctx.get('default_model_id',False)),  
                 }        
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
