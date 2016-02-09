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


row_count = 0
count = 0

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
    


def index_get(L, i, v=None):
    try: return L.index(i)
    except: return v
     
class import_substitution_values(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.substitution.values"
    _description = "Create new value Substitutions functionality in Fields mapping"
    
    def _substitute_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}

        for record in self.browse(cr, uid, ids, context=context):
                res[record.id] = record.src_value or ' '  + ' >> ' + record.odoo_value or ' ' 
        return res

    
    _columns = {'name': fields.function(_substitute_name_get_fnc, type="char", string='Name'),
                'src_value':fields.char('Source field value', size=64,required=True),
                'odoo_value':fields.char('Corresponding odoo value', size=64,required=True),
                }
    
    def _get_import_header_map_id(self,cr,uid,context=None):
        return context.get('default_import_map_id',False)
    _defaults = {
                 'header_map':_get_import_header_map_id
                 }
       
class import_substitute_sets(osv.osv):
    
    _name = "import.substitute.sets"
    _description = "Import Substitution maps"
    
    _columns = { 'name':fields.char('Name', size=64, required=True),
                  'import_m2o_substitutions':fields.many2many('import.substitution.values', 'import_substitute_sets_rel', 'substitutions_id','substitute_set_id', 'Substitution Set' )
                  }
    
class import_related_header(osv.osv): 
    # The Model Is a map from Odoo Data to CSV Sheet Data
    _name = "import.related.fields"
    _description = "Sublevel Related Fields mapping"
    
    
    _columns = { 
                'name': fields.char('Related Fields Map'),
                'import_data_headers':fields.many2many('import.data.header', 'import_related_fields_rel', 'import_related_id','import_data_header_id','Import Field', required=False, ondelete='cascade'),
               
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
    _description = "Holds import Data Source information"

   
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
            'header_ids': fields.one2many('import.data.header','import_data_id','Import Fields ',limit=300, copy=True),
#            'index':fields.integer("Index"),
            'dbf_path':fields.char('DBF Path',size=256),
            'record_num':fields.integer('Current Record'),
            'tot_record_num':fields.integer("Total Records"),
            'record_external':fields.boolean('Use External ID' ,
                help = '''Create External ID on Record,  if any fields set for External build id on fields
                else use row number and import source name for External ID
                '''),
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
            'sequence': fields.integer("Sequence"),
            'import_values':fields.text("Import Record Values")
            }
    
    _defaults = {
        'test_sample_size':10,
        'record_num':1,
        'src_type':'csv',
        'state': 'draft',
        }

    _order = 'sequence'
    
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
                rid = self.pool.get('import.data.header').create(cr,uid,{'name':header, 'csv_id':rec.id, 'model_field':fids and fids[0] or False, 'model':rec.model_id.id},context=context)
                
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
    
          
    def get_row_count_odbc(self,qry,cur):
        
        pos = qry.lower().find('from')
        count_qry = qry[pos-1:]
        count_qry = 'select count(*) as rows ' + count_qry
        cur.execute(count_qry)
        count_result = cur.fetchone()
        for tot_count in count_result:
            return tot_count
            
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
    

        

     
class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'    

    _defaults = {
                 'model_id': lambda self,cr,uid,ctx=None: (ctx and ctx.get('default_model_id',False)),  
                 }        
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
