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
                  'import_substituion_value_ids':fields.many2many('import.substitution.values', 'import_substitute_values_rel', 'substitutions_id','substitute_set_id', 'Substitution Set' )
                  }
    
            
class import_data_file(osv.osv):


    _name = "import.data.file"
    _description = "Holds import Data Source information"
         
    _columns = {
            'name':fields.char('Name',size=32,required = True ), 
            'description':fields.text('Description',), 
            'model_id': fields.many2one('ir.model', 'Model',  required= False,
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
            'header_ids': fields.one2many('import.data.header','import_data_id','Map Fields ', copy=True),
            'header_list_ids': fields.one2many('import.data.header.list','import_data_id','Source Fields ', copy=True),
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
            'start_row':fields.integer("Test Start Row"),
            'base_external_dbsource' : fields.many2one('base.external.dbsource', string="ODBC Connection", help="External Database connection to foreign databases using ODBC, MS-SQL, Postgres, Oracle Client or SQLAlchemy."),
            'src_table_name' : fields.char('Source Table Name',size=256),
            'src_type' : fields.selection(SOURCE_TYPES, "Data Source Type", required=False),
            'sql_source': fields.text('SQL', help='Write a valid "SELECT" SQL query to fetch data from Source database'),
            'state': fields.selection([('draft','Draft'),('map','Mapping Fields'),('ready','Map Confirmed'),('importing','Import Running')], "Status"),
            'sequence': fields.integer("Sequence"),
            'ir_cron_id': fields.many2one('ir.cron', 'Scheduled Job',domain="[('is_import_data_job','=',True)]",),
            #'remove_records_xyz' : fields.selection([('1','Delete'),('2' ,'Set In-Active'),('0','No Action' )],'Remove Old Records') ,
            #'remove_records_filter': fields.char( "Remove Filter" , size=256, help="set domain filter for removing records") ,
            
            }
    
    _defaults = {
        'test_sample_size':10,
        'record_num':1,
        'state': 'draft',
        }

    _order = 'sequence'



     
class ir_model_fields(osv.osv):
    _inherit = 'ir.model.fields'    

    _defaults = {
                 'model_id': lambda self,cr,uid,ctx=None: (ctx and ctx.get('default_model_id',False)),  
                 }        
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
