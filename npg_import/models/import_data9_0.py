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

from openerp import models, fields, api, exceptions, _

import csv
import os
import cStringIO
import datetime, pytz 
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
    _logger.info("Python DBF not available. Please install dbf python package.")
    
try:
    import pyodbc  
    SOURCE_TYPES.append(('odbc', 'ODBC Connection'))
     
except:
    _logger.info("Python ODBC not available. Please install pyodbc python package.")

# define Globals
row_count = 0
count = 0

start_time = None
ProcessStartTime = None
current_record = 0
dbf_table = None
odbc_cursor = None
csv_file = None
test_mode = False      
#error_log = ""

class import_data_file(models.Model): 
            
    _inherit = "import.data.file"  
    
    @api.multi 
    def import_schedule(self):
        cron_obj = self.env['ir.cron']
        tz = self.env.context['tz']
        tz = pytz.timezone(tz)
        today = datetime.datetime.now(tz).date() + datetime.timedelta(days=1)
        midnight = tz.localize(datetime.datetime.combine(today,datetime.time(0,0)))
        next_start = midnight.astimezone(pytz.utc).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
              
        for imp in self:
            cron_id = False
            if not imp.ir_cron_id:
                new_create_id = cron_obj.create( {
                    'name': ('Import %s'% imp.name) , 
                    'interval_type': 'days',
                    'interval_number': 1,
                    'numbercall': -1,
                    'nextcall': next_start,
                    'model': 'import.data.file',
                    'function': 'action_import_scheduled',
                    'doall': False,
                    'active': False,
                    'is_import_data_job':True,
                })
                cron_id = new_create_id.id
                new_create_id.write({'args':'(%s,)'% cron_id})
                imp.write({'ir_cron_id':cron_id})
                
            else:
                cron_id = imp.ir_cron_id.id
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
  
                
    @api.multi
    def check_selection_field_value(self, model, field, field_val):
        
        sel_list = self.env[model]._fields[field]._column_selection
        field_val_lower = field_val.lower()
        try:
            for select_val in sel_list:
                for value in select_val:
                    if value.lower() == field_val:
                        return select_val[0]
        except:
            return field_val   
        return False
    
    @api.multi
    def check_external_id_name(self, external_id_name=False):  
          
        #  When Using field for External ID 
        if external_id_name:
            return external_id_name 
        #  When using Record Row External ID and No field External ID            
        elif self.record_external:         
            return ('%s_%s' % (self.name, row_count,))
        else:
            return False    
    
    @api.multi
    def get_external_name(self, import_record, fields=False):
        rec = self
        external_name = False
        for field in fields:
            if field.is_unique_external:
                field_val = self.get_field_val_from_record(import_record, field)
#                field = self.convert_odoo_data_types(field, field_val, import_record)
                if not external_name: external_name = field_val
                else: external_name += '/' + field_val
        return self.check_external_id_name(external_name)
       
    @api.multi
    def search_external_id(self, external_id_name, model): 
                
        search = [('name', '=', external_id_name), ('model', '=', model)]                     
        record = self.env['ir.model.data'].search(search) or None
        if record:
            return record.res_id or False
        else:
            return False  
                 
    @api.multi
    def search_unique_id(self, fields, import_record, model):
        
        rec = self
        search_unique = []
        for field in fields:
            if field.is_unique:
                field_val = self.get_field_val_from_record(import_record, field)
                result = self.convert_odoo_data_types(field, field_val, import_record)
                field_val = result and result.get('field_val', False)
                if not field_val: 
                    error_txt = _('Error: Required unique field %s is not set' % (field.model_field.name))
                    self.update_log_error(error_txt=error_txt)
                    return -1
                search_unique.append((field.model_field.name, "=", field_val))
        
        if len(search_unique) > 0:      
            record = self.env[model.model].search(search_unique)
            if record:
                try:
                    record.ensure_one()
                    return record.id
                except:
                    error_txt = _('Error: Unique Record duplicates found in model %s, search on values %s' % (model.model, search_unique,))
                    self.update_log_error(error_txt=error_txt)
                    return -1
                
                
            else:
                return 0
        else:
            return 0
   
    @api.multi
    def do_search_record(self, fields, import_record, model):
        
        ''' Search for existing records using external Id, name search, or search on specific fields
        external id can be created from row number or based on field values, name search will use Odoo
        standard name search method, search specific field searching on specific fields is base on unique settings on fields
        '''
        rec = self
        external_id_name = self.get_external_name(import_record, fields) 
        external_id = self.search_external_id(external_id_name, model.model)
        search_result = {'external_id_name': external_id_name
                         }
        
        search_unique_id = self.search_unique_id(fields=fields, import_record=import_record, model=model)
        if not external_id and  search_unique_id == -1 :
            search_result['res_id'] = -1
            return search_result 
              
        if search_unique_id and external_id and external_id != search_unique_id:
            error_txt = _('Warning: Model %s External Id and Unique Field not Id not matched  %s <> %s external Id will be used' % (model.model, external_id, search_unique_id,))
            self.update_log_error(error_txt=error_txt)
            search_result['res_id'] = external_id
            return search_result
       
        search_result['res_id'] = external_id or search_unique_id
           
        return search_result
    
    @api.multi
    def do_search_related_records(self, field, import_record, field_val): 
        
        model = field.relation_id.model
        
        search_result = self.do_search_record(fields=field.child_ids, import_record=import_record , model=field.relation_id)                     
        if search_result['external_id_name']: 
            return search_result
        
        if field.search_related_external:
            external_id_name = field_val
            if field.o2m_external_field2:
                external_id_name += '--' + self.get_field_val_from_record(import_record, field.o2m_external_field2)
            res_id = self.search_external_id(field_val, model) 
            if res_id: 
                search_result['external_id_name'] = field_val
                search_result['res_id'] = res_id
                return search_result   
        
        if field.search_other_field:    
            search = [(field.search_other_field.name, '=', field_val)]
            result = self.env[model].search(search)
            if result:
                if result.ensure_one():
                    search_result['res_id'] = result.id or False
                    return search_result
                else:
                     error_txt = _('Warning: duplicate records found in model %s, search on %s' % (model, search,))
                     self.update_log_error(error_txt=error_txt)      
        
        return search_result
        # If not found then do  New External and Search unique Using the Child Map Related Fields settings            
    
    @api.multi
    def get_o2m_m2m_vals(self, field, field_val, import_record): 
        
        rec = self
               
        search_result = self.do_search_related_records(field, import_record, field_val)
        res_id = search_result.get('res_id', False)
        external_id_name = search_result.get('external_id_name', False)
        if res_id == 0 and not field.create_related:
            return False
        if res_id == -1:
            return False
        
        if res_id == 0 and field.create_related:
            odoo_vals = self.do_related_vals_mapping(field=field, import_record=import_record)
            if not odoo_vals['required_missing']: 
                res_id = self.create_import_record(vals=odoo_vals['field_val'], external_id_name=external_id_name,
                                                    model=field.relation) 
                
        if res_id:
            
            return {'field_val':(4, res_id)}
        else: 
            return False
     
    @api.multi
    def do_related_vals_mapping(self, field, import_record):
              
        vals = {}
        for rel_field in field.child_ids:

            if not rel_field.model_field:
                continue
            
            field_val = self.get_field_val_from_record(import_record, field=rel_field)
            if rel_field.skip_if_empty and not field_val:
                return {'required_missing':False, 'field_val': False}
           
            odoo_vals = self.convert_odoo_data_types(field=rel_field, source_field_val=field_val, import_record=import_record)  
            
            if odoo_vals['required_missing']:
                vals = None
                break 
            
            vals[rel_field.model_field.name] = odoo_vals['field_val']
                                                 
            # TODO add functionality to build other Relate values defaults from list or other Tables
        return {'required_missing':odoo_vals['required_missing'], 'field_val': vals}

    
    def process_related(self,field,import_record,field_val):
                
        search_result = self.do_search_related_records(field, import_record, field_val)
        if not search_result: res_id = False
        else: 
            res_id = search_result.get('res_id', False)
            
            external_id_name = search_result.get('external_id_name', False)
        
            if not res_id and field.create_related: 
                res_id = self.create_related_record(import_record=import_record, field=field, field_val=field_val, external_id_name=external_id_name)
            
            if res_id == -1: 
                res_id = False
            
        return res_id
        
            
    @api.multi    
    def convert_odoo_data_types(self, field, source_field_val, import_record=None, append_vals=None):
        
        # Update Field value if Substitution Value Found. 
        field_val = self.do_substitution_mapping(source_field_val, field)
        
 
        required_missing = False
        
        if field.model_field_type == 'many2one' and field_val:
            
            field_val = self.process_related(field, import_record, field_val)
         
        elif field.model_field_type == 'boolean' and  field_val:

            try:
                field_val = field_val.lower()
                if field_val in ('1', 't', 'true', 'y', 'yes'):
                    field_val = True
                elif field_val in ('0', 'f', 'false', 'n', 'no', ''):
                    field_val = False
                else:
                    field_val = False
                    error_txt = ('Error: Field value %s -- %s is not Boolean type value set False' % (field.model_field.name, field_val,))
                    self.update_log_error(error_txt=error_txt)
                
            except:
                field_val = False
                error_txt = ('Error: Converting Field %s -- %s to Boolean value set False' % (field.model_field.name, field_val,))
                self.update_log_error(error_txt=error_txt)
            
        elif field.model_field_type == 'float':
       
            if field_val == False or field_val is None: field_val = '0'
                
            try:
                field_val = float(field_val)
            except:
                self.has_errors = True
                field_val = 0.0
                error_txt = _('Error: Field: %s -- %s is not required  Floating Point type' % (field.model_field.name, field_val))
                self.update_log_error(error_txt=error_txt)

        elif field.model_field_type == 'integer' and  field_val:
            
            if field.is_db_id:
                
                field_val = self.process_related(field, import_record, field_val)
                
            else:  
                if field_val.lower() == 'false': field_val = '0'
                try:
                    field_val = int(field_val)
                except:
                    self.has_errors = True
                    field_val = 0
                    error_txt = _('Error:  Field %s -- not required Integer  type' % (field.model_field.name, field_val))
                    self.update_log_error(error_txt=error_txt)

        elif field.model_field_type == 'selection' and  field_val:
            
            field_val = self.check_selection_field_value(field.model.model, field.model_field.name, field_val)
            
            if field_val:
                pass
            else:
                self.has_errors = True
                field_val = False
                error_txt = _('Error: Incorrect Selection Field %s - %s  Import Value %s: %s' % (field.model.model, field.model_field.name, field.name,field_val))
                self.update_log_error(error_txt=error_txt)
        
        elif field.model_field_type in ['char', 'text', 'html'] and  field_val:
            if not field_val:
                field_val = ''
            else:
                pass
        elif field.model_field_type == 'binary' and  field_val:
            
            pass
        elif field.model_field_type in ['one2many', 'many2many'] and  field_val:
   
            result = self.get_o2m_m2m_vals(field=field, field_val=field_val, import_record=import_record)
            if result and [result.get('field_val', False)]:
                field_val = [result.get('field_val', False)]
            else:
                error_txt = _('Warning: Create %s for Model: %s Field: %s Val: %s has no result set.' % (field.model_field_type, field.model.model, field.model_field.name, field_val))
                self.update_log_error(error_txt=error_txt)
                field_val = False
                return {'required_missing':True, 'field_val':field_val}
            
        if field.model_field.required and not field_val:
            
            error_txt = _('Error: %s %s Required Field: %s Has No Odoo Value For Source: %s : %s' % (field.model_field_type, field.model.model, field.model_field.name, field.name, source_field_val))
            self.update_log_error(error_txt=error_txt)
            required_missing = True
                
        if append_vals:
            
            if field.model_field_type in ['one2many', 'many2many']:
            
                if field_val: 
                    append_vals.append(field_val)
                    field_val = append_vals
                else:field_val = append_vals
                
            elif field.model_field_type in ['char', 'text', 'html']:
                if field_val: field_val = append_vals + field_val
            else:
                if field_val and append_vals:
                    error_txt = _('Warning: Odoo field has been Mapped to multiple source fields, Last value found used for import')
                 
        return {'required_missing':required_missing, 'field_val':field_val}
     
    @api.multi    
    def do_substitution_mapping(self, field_val, field):
        
        substitutes = {}
        # if field.substitutions:
        #    for sub in field.substitutions:
        #       substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()})
        
        for sub in field.substitute_sets.import_substituion_value_ids:
            substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()})
         
        try:    
            # see if m20 map exist
            for sub in  field.substitution_m2o_ids:       
                substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()}) 
        except:
            pass       
        return substitutes.get(field_val, field_val)
                    
    def get_field_val_from_record(self, import_record, field): 
               
        src_type = self.src_type
        
        if not field.name:
            return field.default_val
                
        if src_type == 'dbf':
            field_raw = import_record[field.name] or False
        elif src_type == 'csv':
            field_raw = field.name and import_record[field.name]  or False
        elif src_type == 'odbc':
            field_raw = field.name and getattr(import_record, field.name)  or False
        else: raise ValueError('Error! Source Data Type Not Set')
            
        if not field_raw  and field.default_val:
            return field.default_val
        if not field_raw:
            return None
        else: 
            if isinstance(field_raw, str):
                
                field_val = field_raw.strip()
                if field_val == "": 
                    field_val = field.default_val or ""
                
    
            elif isinstance(field_raw, unicode):
                field_val = field_raw.strip()
                if field_val == "":
                    field_val = field.default_val or ""
    
            elif isinstance(field_raw, datetime.datetime):
                field_val = field_raw.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            
            elif isinstance(field_raw , datetime.date):
                field_val = field_raw.strftime(DEFAULT_SERVER_DATE_FORMAT)
    
            elif isinstance(field_raw, bytearray):
                field_val = base64.b64encode(field_raw)
            elif isinstance(field_raw, bool):
                field_val = str(field_raw)
            else: field_val = str(field_raw)

        if field.sub_string:
            sub_str_split = field.sub_string.split(":")
            start = sub_str_split[0] or None
            end = sub_str_split[1] or None 
            start = int(start)
            end = int(end)
            field_val = field_val[start:end]
        
        return field_val                       

    @api.multi
    def create_related_record(self, import_record, field, field_val, external_id_name=False):
        
        rec = self
        vals = False
        res_id = False
        try:
            odoo_vals = self.do_related_vals_mapping(field=field, import_record=import_record)
            if not odoo_vals or odoo_vals['required_missing']:
                res_id = False
            else:
                vals = odoo_vals['field_val']
                res_id = self.create_or_update_record(0, vals, external_id_name, field.relation, update = field.update_related)

            if not res_id:
                error_txt = _('Warning: Relation: %s record Not Created for Value: %s' % (field.relation, field_val)) 
                self.update_log_error(error_txt=error_txt)
                return   False    
            
            return res_id
            
        except:
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Error: Related record Vals: %s   Model: %s' % (vals or 'No Values Dictionary Created' , field.relation))
            self.update_log_error(error_txt=error_txt)
            
            return False
     
    def create_import_record(self, vals, external_id_name=False, model=False): 
        
        try:
            res_id = False
            
            model = model or self.model_id.model
            
            model_obj = self.env[model]

            record_obj = model_obj.create(vals)
            res_id = record_obj and  record_obj.id or False
            if external_id_name:                   
                external_vals = {'name':external_id_name,
                                 'model':model,
                                 'res_id':res_id,
                                 'module':model
                                 }
                
                self.env['ir.model.data'].create(external_vals)
                
            _logger.info(_('Created Record in %s with ID: %s %s from Source row %s' % (model, external_id_name , res_id, row_count)))

            return res_id

        except:
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Error: Import vals %s not created for model \'%s\'' % (vals, model))
            self.update_log_error(error_txt=error_txt)
            
            return False
        
    def create_or_update_record(self, res_id, vals, external_id_name, model, update):        
        
        try:  # Update or Create Records          
            
            dbWriteStartTime = datetime.datetime.now()
            if res_id == -1:
                # Errors in UNique Search or Duplicated records found.
                result = False
  
            elif res_id == 0: 
                 res_id = self.create_import_record(vals=vals, external_id_name=external_id_name, model=model)
                 result =  res_id
                
            elif res_id and update:
                record_obj = self.env[model].browse(res_id)
                record_obj.write(vals)
                if record_obj: 
                    res_id = record_obj.id
                    _logger.info(_('Source row %s Updated Odoo Model %s ID: %s %s') % (row_count, model, external_id_name or '', res_id,)) 
                    result =  res_id
                else:
                    _logger.info(_('Source row %s Update Failed Odoo Model %s ID: %s %s') % (row_count, model, external_id_name or '', res_id,)) 
                    result =  False
            
            elif res_id and not self.do_update:
                error_txt = _(('Warning: %s Duplicate found in Odoo Model %s ID: %s %s, record skipped') % (row_count, model, external_id_name or '', res_id,)) 
                self.update_log_error(error_txt=error_txt)
                result =  False   
            time_delta = datetime.datetime.now() - dbWriteStartTime
            _logger.info(_("Model %s Write Time %s") %(model, time_delta))
            
            return result
        except:  # Error Writing or Creating Records
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Writing or Creating vals %s ' % (vals,))
            self.update_log_error(error_txt=error_txt)
            return self.show_warn(error_txt)
       
    @api.multi    
    def do_process_import_row(self, import_record):

        global row_count
        global count
        rec = self
        
        vals = {}
        search_unique = []
        
        external_id_name = ''
        skip_record = False
        row_count += 1
        
        self.row_process_time(set_start=True)      
        if row_count % 25 == 0:  # Update Statics every 10 records
            self.update_statistics(remaining=True)
               
               
                    
        for field in self.header_ids:

            try:  # Building Vals DIctionary
                
                
                                      
                res_id = False
                field_val = False
                
                # test  Clean and convert Raw incoming Data values to stings to allow comparing to search filters and substitutions         
                field_val = self.get_field_val_from_record(import_record, field)
                
                # IF Field value not found in Filter Search list skip out to next import record row
                if self.skip_current_row_filter(field_val, field):
                    return False                          
              
                #if not field_val:continue
             
                if not field.model_field: continue  # Skip to next Field if no Odoo field set
                
                # Convert to Odoo Data types and add field to Record Vals Dictionary

                odoo_vals = self.convert_odoo_data_types(field=field, source_field_val=field_val, import_record=import_record,
                                                                             append_vals=vals.get(field.model_field.name, False))
                if odoo_vals and odoo_vals['required_missing']:
                    return False                     
                    
                vals[field.model_field.name] = odoo_vals['field_val']
                                                            
            except:  # Buidling Vals DIctionary
                self.env.cr.rollback()
                self.has_errors = True
                error_txt = _('Error: Building Vals Dict at Field: %s == %s \n Val Dict:  %s ' % (field.model_field.name, field_val, vals,))
                self.update_log_error(error_txt=error_txt)
                skip_record = True
                return False
        
        try:  # Finding existing Records  

            search_result = self.do_search_record(fields=self.header_ids, import_record=import_record, model=self.model_id)
            res_id = search_result.get('res_id', False)
            external_id_name = search_result.get('external_id_name', False)
        except:  # Finding Existing Records
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Error: Search for Existing records: %s-%s ' % (search_unique, external_id_name))
            self.update_log_error(error_txt=error_txt)                    
            return False
        
        if self.create_or_update_record(res_id, vals, external_id_name, self.model_id.model, update = self.do_update):
            self.row_process_time()
            count += 1
            return count
            
        else:
            self.row_process_time()
            return  False
            
  
    @api.multi
    def exit_test_mode(self):
        
        
        if  test_mode and (count >= self.test_sample_size  or row_count >= self.test_sample_size + 100) :
            
            if self.rollback: self.env.cr.rollback()
            
            # Exit Import Records Loop  
            return True
        elif not test_mode or not self.rollback and self.remove_records == '0':
            self.env.cr.commit()
            return False
        return False
    
    def show_warn(self,error_txt):
        return {'warning':{'title':_('Warning'),'message':error_txt}}
   
    @api.multi
    def update_log_error(self, error_txt='' , has_errors = False):
        
        #global error_log
        
        if not self.error_log:
            self.error_log = ""
        
        e = traceback.format_exc()
        
        if row_count:
            error_txt = 'Row: ' + str(row_count) + ' ' + error_txt
        logger_msg = error_txt + '\n' + 'TraceBack: ' + e
        _logger.error(logger_msg)
        
        e = sys.exc_info()
        self.error_log += error_txt + '\n'
        if e[2]:
            e = traceback.format_exception(e[0], e[1], e[2], 1)
            error_msg = e[2]
            self.error_log += error_msg + '\n'
             
        log_vals = {'error_log': self.error_log,
                'has_errors':self.has_errors or has_errors}
        self.write(log_vals)
#        self.env.cr.commit()
        return log_vals
    
    @api.multi
    def update_statistics(self, remaining=True, stats_vals=False):   
        '''params:
        rec: The main record set for import File
        processed_rows: Current number of Rows processed from Data Source
        count: Total number of Rows actually imported without Skipped
        
        '''
        global count
        global row_count
        
        
        estimate_time = self.estimate_import_time(processed_rows=row_count, remaining=remaining)    
        
        if stats_vals:
            stats_vals['time_estimate'] = estimate_time  
        else: 
            stats_vals = {
                    'start_time':start_time,  
                    'end_time': False,
                    'error_log': self.error_log,
                    'time_estimate': estimate_time,
                    'row_count': row_count,
                    'count': count,
                    'tot_record_num':self.tot_record_num}
            
        update_sql = ''' update import_data_file 
            set start_time =  %s,
                    error_log =  %s,
                    time_estimate = %s,
                    row_count = %s,
                    count = %s,
                    tot_record_num = %s 
                    where id = %s)
                    '''
        self.env.cr.execute(update_sql,(start_time,self.error_log,estimate_time, row_count,count,self.tot_record_num,self.id))
        
        if not remaining:
            stats_vals['end_time'] = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)  
            if self.has_errors:stats_vals['state'] = 'map'
            else: stats_vals['state'] = 'ready'
            count = 0
            row_count = 0
                        
        #self.write(stats_vals) 
        self.env.cr.execute(update_sql,(start_time,self.error_log,estimate_time, row_count,count,self.tot_record_num,self.id))
        
        return stats_vals
    
    @api.multi   
    def estimate_import_time(self, processed_rows, remaining=True):
        '''params:
        start_time: Time in string format YYYY-MM-DD HH:MM:SS when import started
        processed_rows: Current number of Rows processed from Data Source
        tot_record_num: Total number of Rows in data Source
        remaining: Boolean if Tru return time left in import if false return total Estimated time
        '''
        t2 = datetime.datetime.now()
        time_delta = (t2 - datetime.datetime.strptime(start_time, DEFAULT_SERVER_DATETIME_FORMAT))
        if processed_rows > 0:
            time_each = time_delta / processed_rows
            time_each = time_each.total_seconds()
        else: time_each = 0.0
        
        if remaining:
            
            return (time_each * (self.tot_record_num - processed_rows)) / 3600  # return time in hours
                          
        else:
            return (time_each * self.tot_record_num) / 3600 


        
    @api.onchange('model_id') 
    def onchange_model(self):
        
        header_ids_vals = []
        if not self.state == 'draft' :
            for rec in self.header_ids:    
            
                vals = { 
                        'model': self.model_id.id,
                        }
                header_ids_vals.append((1, rec.id, vals))
                rec.model = self.model_id.id
            return{'value':{"header_ids":header_ids_vals}}
            
            
            return {}
        if self.model_id:
           
            for rec in self.header_ids:    
                odoo_field_id = self._match_import_header( self.model_id.id, rec.name, rec.field_label)
                vals = { 'model_field':odoo_field_id,
                        'model': self.model_id.id,
                        }
                header_ids_vals.append((1, rec.id, vals))
                rec.model = self.model_id.id 
                
            return{'value':{"header_ids":header_ids_vals}}
    
        else:
            return {}

    
    def action_import_scheduled(self,cr,uid,cron_id=False):
        if cron_id:
            domain = [('state','=','ready'),('ir_cron_id','=',cron_id)]
            obj = self.pool('import.data.file')
            ids = obj.search(cr,uid,domain,order='sequence')
            recs = obj.browse(cr,uid,ids)
            for rec in recs:
                rec.action_import()
            return True
            
    @api.multi
    def action_import(self):
        
        global row_count
        global count
        global start_time
        global test_mode

        #global error_log

        row_count = 0
        count = 0
           
        if not self.header_ids:
            error = 'No  import map fields'
            return  
        
        test_mode = self.env.context.get('test', False)
        '''
        self.has_errors = False
        self.error_log = '' 
        self.row_count = 0
        self.count = 0
        self.tot_record_num = 0
        
        self.start_time = start_time
        '''
        start_time = datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        stats = {'has_errors':False,
                'error_log':'',
                'row_count':0,
                'count':0,
                'tot_record_num':0,
                'start_time':datetime.datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                }
        if self.src_type == 'dbf':
            return self.action_import_dbf()
            
        elif self.src_type == 'csv':
            return self.action_import_csv()
            
        elif self.src_type == 'odbc':
            return self.action_import_odbc(stats_vals=stats)
     
    @api.multi      
    def remove_records(self):    
        
        domain =  []
        domain += eval(self.remove_records_filter)
        if self.remove_records == '1' : 
             record_objs = self.env[self.model_id.model].search(domain)
             records_objs.delete()
        elif self.remove_records == '2' :
            record_objs = self.env[self.model_id.model].search(domain)
            records_objs.update({'active' : False})   
         
    @api.multi
    def action_import_dbf(self,stats_vals=None):
        
        try:
           
            dbf_table = dbf.Table(self.dbf_path)
            dbf_table.open()
            self.tot_record_num = len(dbf_table)
            self.update_statistics(remaining=True)
            self.env.cr.commit()
            
           
            n = (self.start_row and self.start_row > 1 and self.start_row - 1) or 0
            while n < self.tot_record_num:
                 
                import_record = dbf_table[n]
                
                self.do_process_import_row(import_record)
                
                if self.exit_test_mode():
                    return{'value':self.update_statistics(remaining=False)}
                n += 1
        except:
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error(error_txt=error_txt)
        
        return {'value':self.update_statistics(remaining=False)}
    
    @api.multi
    def action_import_odbc(self,stats_vals=None):
        
        conn = False 
        
        try:
                
            conn = self.env['base.external.dbsource'].conn_open(self.base_external_dbsource.id)
            cur = conn.cursor()
            
#            self.tot_record_num = self.get_row_count_odbc(self.odbc_import_query(),cur)
            stats_vals['tot_record_num'] = self.get_row_count_odbc(self.odbc_import_query(),cur)
            self.update_statistics(remaining=True, stats_vals=stats_vals)
            self.env.cr.commit()
            qry = self.odbc_import_query()
            cur.execute(qry)
            
            all_data = True
            if test_mode and self.start_row and self.start_row > 0:
                cur.skip(self.start_row)

            while all_data:
                
                all_data = cur.fetchmany(500)
                
                if not all_data:
                    break
                for import_record in all_data:
                    
                    self.do_process_import_row(import_record)
               
                    if self.exit_test_mode():
                        return{'value':self.update_statistics(remaining=False)}
                  
            conn.close()
        except:
            self.env.cr.rollback()
            if conn:
                conn.close()
            self.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error(error_txt=error_txt)        
        return{'value':self.update_statistics(remaining=False)}
       
    def odbc_import_query(self):
        
        src_table = str(self.src_table_name).strip()  
        if self.sql_source:         
            qry = str(self.sql_source)
        elif test_mode:
            qry = "select TOP %s * from %s" % (self.test_sample_size, src_table)
        else:
            qry = "select * from %s" % src_table

        return qry
              
    def get_row_count_odbc(self,qry,cur):
        
    #    pos = qry.lower().find('from')
    #    count_qry = qry[pos-1:]
    #    count_qry = 'select count(*) as rows  ' + count_qry
        count_qry = 'SELECT count(*) as rows  FROM (' + qry + ') AS subquery'
        cur.execute(count_qry)
        count_result = cur.fetchone()
        for tot_count in count_result:
            
            return tot_count
            
        return False
    
    @api.multi
    def action_import_csv(self):

        try:    
            csv_data = self.get_csv_data_file()
            header_dict = self.get_csv_header_dict(rec, csv_data)
            self.update_statistics(remaining=True)
            self.env.cr.commit()
            
            for csv_row in csv_data[1:]:

                import_record = self.convert_cvs_row_dict(header_dict, csv_row)
                 
                self.do_process_import_row(import_record)
                
                if self.exit_test_mode():
                    return{'value':self.update_statistics(remaining=False)}
                    
        except:
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Import Aborted')
            return self.update_log_error(error_txt=error_txt)
        
        return {'value':self.update_statistics(remaining=False)}
    
    @api.multi   
    def get_csv_data_file(self):
        
        try:
            # open only the first Attachment no other attachments valid
            for attach in self.attachment:
                data_file = attach.datas
                continue
            
            str_data = base64.decodestring(data_file)
            
            if not str_data:
                raise  ValueError( 'The file contains no data')
            
            return list(csv.reader(cStringIO.StringIO(str_data)))
            
        except:
            error_txt = "Error: Unable to open CSV Data"
            self.update_log_error(error_txt=error_txt)
            raise  ValueError( 'Make sure you saved the file as .csv extension and import!')
            return False
   
    def get_csv_header_dict(self, csv_data):
        
        headers_list = []
        for header in csv_data[0]:
            headers_list.append(header.strip())
        
        header_map = {}
        
        for hd in self.header_ids:
            if hd.model_field:
                label = hd.model_field.field_description or ''
                header_map.update({hd.model_field.name : hd.name})
                    
        if not header_map:
            raise  ValueError( 'No Header mapped with Model Field in Header line!')
                    
        headers_dict = {}
        for field, label in header_map.iteritems():  
            headers_dict[field] = index_get(headers_list, label)   
    
        return headers_dict

        
    def skip_current_row_filter(self, field_val , field):
        '''
             if record to be skipped return True
        '''    
        # Skip if empty Record
        if field.skip_if_empty and (field_val == '' or not field_val ):
            error_txt = _('Warning: Source %s : %s for Odoo Field %s  Has no value is Skipped ' % (field.name, field_val,field.model_field.name))
            self.update_log_error(error_txt=error_txt)
            to_be_skipped = True
            return to_be_skipped
        
        if field.name == 'kits':
            pass
        
        # Skip if found in list to be Skipped
        if field.skip_filter and not field.skip_filter == '[]':
        
            skip_list = []
            skip_filter = field.skip_filter.replace('[', '')
            skip_filter = field.skip_filter.replace(']', '')
            
            skip_list = tuple(field.skip_filter.split(','))
            
            if not skip_list:
                skip_list.append(field.skip_filter)
                              
            if field_val in skip_list:
                to_be_skipped = True
                return to_be_skipped
              
        if field.search_filter and not field.search_filter == '[]':
        
            search_list = []
            search_filter = field.search_filter.replace('[', '')
            search_filter = field.search_filter.replace(']', '')
            
            search_list = tuple(field.search_filter.split(','))
            
            if not search_list:
                search_list.append(field.search_filter)
            
            if field_val not in search_list:
                to_be_skipped = True
                return to_be_skipped
            
        return False

    def row_process_time(self, set_start=False):
    
        
        global RowStartTime
        
        if set_start:
            RowStartTime = datetime.datetime.now()
            return
        else:
            time_delta = datetime.datetime.now()- RowStartTime
            _logger.info(_("Row: %s Process Time: %s seconds" ) %(row_count, time_delta))
            
            return                                               
    
    def get_label_match_index(self, dbf_table ):        
        
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
      
    
    @api.multi 
    def refresh_header_list(self):
                
        self.delete_header_columns()
        
        if self.src_type == 'dbf':
            fields = self.get_dbf_header_list()
            
        elif self.src_type == 'csv':
            fields = self.get_csv_header_list()
            
        elif self.src_type == 'odbc':
            fields = self.get_odbc_header_list()
#        self.env.cr.commit()
        return
    
    @api.multi 
    def delete_header_columns(self):
        
        if self.env.context.get('refresh', False) == False:   
            for field in self.header_ids:
                
                field.unlink()
         
        for field in self.header_list_ids:
            field.unlink()          
    
    def set_header_columns_from_odoo_vals(self, model_field, sequence = 0): 
  
            model = self.env['ir.model'].search([('model','=',model_field.model)])
            
            field = self.match_odoo_field_to_header_list(model_field)
            vals = {'model_field':model_field.id,
                    'model': self.model_id.id,
                    'relation_id': model and model.id or None,
                    'header_list': field and field.id or None,
                    'name':field and field.name or None,
                    'field_label': field and field.field_label or None,
                    'field_type': field and field.field_type or None,
                    'sequence': sequence,
                    } 
            return (0,0,vals)
    
   

    
    def set_header_columns_from_source_vals(self,field, sequence = 0): 
  
            model_field =  self.match_import_header_to_odoo(self.model_id.id, field)
            if model_field:
                model = self.env['ir.model'].search([('model','=',model_field.model)])
            else:
                model = None
            vals = {'header_list':field.id,
                    'name':field.name,
                    'field_label': field.field_label,
                    'field_type': field.field_type,                  
                    'model_field': model_field and model_field.id or None,
                    'relation_id': model and model.id or None,
                    'model': self.model_id.id,
                    'sequence': sequence,
                    } 
            return (0,0,vals)
     
    @api.multi
    def match_import_header_to_odoo(self, model_id, field):
        """ Attempts to match a given header to a field of the
        import source to a corresponding field in Odoo data models

        :param str header: header name from the data file
        :param fields:
        :returns: False if the header couldn't be matched, or
                  the fields object
        :rtype: field object
        """

        name = (field.name and field.name.strip().lower()) or '' 
        field_label = (field.field_label and field.field_label.strip().lower()) or ''

        search_domain = [('name', '!=', 'display_name'), '&', 
                        ('model_id', '=', model_id), '|', '|', ('field_description', 'ilike', name),
                        ('field_description', 'ilike', field_label),
                        '|', ('name', 'ilike', name), ('name', 'ilike', field_label)]
  
        model_fields = self.env['ir.model.fields']
        fields_odoo = model_fields.search(search_domain)
        
        if len(fields_odoo) == 1:
            return fields_odoo[0]

        for field_odoo in fields_odoo:
            
            odoo_description = field_odoo['field_description']
            odoo_description = (odoo_description and odoo_description.strip().lower()) or ''
            odoo_name = field_odoo['name']
            odoo_name = (odoo_name and odoo_name.strip().lower()) or ''
            if name == odoo_description or name == odoo_name \
                    or field_label == odoo_description or field_label == odoo_name:
                return field_odoo

        return None   
    
    @api.multi
    def match_odoo_field_to_header_list(self, model_field):
        
        for field in self.header_list_ids:
            
            if field.name ==  model_field.field_description or field.name == model_field.name \
                or field.field_label == model_field.field_description or field.field_label == model_field.name:
                
                return field
                        
            else:
                return None
            
    @api.multi 
    def create_map_from_source(self):        

        self.refresh_header_list()
        headers_vals= []
            
        sequence = 0
        for field in self.header_list_ids:
            sequence =+ 1
            vals = self.set_header_columns_from_source_vals(field, sequence)
            headers_vals.append(vals)
            
        vals = {'error_log':'Successful Header Import',
            'has_errors':False,
            'tot_record_num':self.tot_record_num, 
            'description':self.model_id.info,
            'header_ids': headers_vals,
            }   
        self.write(vals)
#            self.env.cr.commit()
        return {'value': vals}
        
        
        if self.env.context.get('refresh_all_import_columns',False):
            vals = {'state':'map'}
            self.write(vals)
            return{'value':vals}
        else :
            return 
     
    @api.multi 
    def create_map_from_odoo_model(self):
        
        header_vals = []
        if self.model_id:
            self.refresh_header_list()
            sequence=0
            for model_field in self.model_id.field_id:
                sequence  += 1
                vals = self.set_header_columns_from_odoo_vals(model_field, sequence)
                header_vals.append(vals)
            vals = {'error_log':'Successful Header Import',
                    'has_errors':False,
                    'tot_record_num':self.tot_record_num, 
                    'description':self.model_id.info,
                    'header_ids': header_vals,
                    }   
            self.write(vals)
#            self.env.cr.commit()
            return {'value': vals}
        
        else:
            
            raise ValueError('Error! Model Not Set')

            return {}
       


                      
    @api.multi
    def get_dbf_header_list(self):
        
        if  self.dbf_path:
        
            self.tot_record_num = 0
            self.record_num = 1
    
            try:
                             
                dbf_table = dbf.Table(self.dbf_path)
                dbf_table.open()
                info = dbf.info(self.dbf_path)
                
                structure = dbf.structure(self.dbf_path)
    
                if not dbf_table:
                    
                    e = 'Error opening DBF Import  %s:'  % (self.dbf_path, )
                    return self.update_log_error(error_txt=e, has_errors = True)
                 
                self.tot_record_num = len(dbf_table)    
                if self.tot_record_num == 0:
                    e = 'Table has no data to Import  %s:'  % (self.dbf_path, )
                    return self.update_log_error(error_txt=e,has_errors = True)
                    
                dbf_label_index = self.get_label_match_index(dbf_table)
                
                for field in structure:
                    field = field.split()
                    
                    vals = {
                            'name' :field[0],
                            'field_label': self.vision_match_field_label(field[0],index = dbf_label_index),
                            'field_type' :field[1],
                            'import_data_id':self.id,
                            }
                    self.env['import.data.header.list'].create(vals)
                
            except:
                
                error_txt = _('Error opening DBF Import  %s' % (self.dbf_path,))
                return self.update_log_error(error_txt=error_txt, has_errors=True) 
     
            return {'value': vals}
        else:
            error_txt = _('Error! Data Source not set') 
            self.update_log_error(error_txt=error_txt,has_errors = True) 
            raise ValueError(error_txt)     
            return False
    
    def get_csv_header_list(self):
        
        if self.attachment:
                
            for attach in self.attachment:
                data_file = attach.datas
                continue
            
            str_data = base64.decodestring(data_file) 
            
            if not str_data:
                raise osv.except_osv('Warning', 'The file contains no data')
            try:
                partner_data = list(csv.reader(cStringIO.StringIO(str_data)))
            except:
                raise osv.except_osv('Warning', 'Make sure you saved the file as .csv extension and import!')
            
            self.delete_header_columns()
            
            headers_list = []
            for header in partner_data[0]:
                headers_list.append(header.strip())
            
            for field in headers_list:
                
                vals = {
                        'name' :field,
                        'field_label': None,
                        'field_type' : 'char',
                        'import_data_id':self.id,
                        }
                self.env['import.data.header.list'].create(vals)
                         
            return True
        
        else:
            error_txt = _('Error! Data Source not set') 
            self.update_log_error(error_txt=error_txt,has_errors = True) 
            raise ValueError(error_txt)     
            return False
    
    def get_odbc_header_list(self):
        
        if self.base_external_dbsource:
        
            qry = self.odbc_import_query()    
            result = self.base_external_dbsource.execute(sqlquery=qry,metadata=True)
            
            if not result.has_key('cols'):
                raise ValueError('Error! Source Data Type no column info')
            
            self.delete_header_columns()
            
            headers_list = result['cols']
            row_data = result['rows']
                
            for field in headers_list:
                
                vals = {
                        'name' :field[0],
                        'field_label': None,
                        'field_type' : field[1],
                        'import_data_id':self.id,
                        }
                self.env['import.data.header.list'].create(vals)
                         
            return True    
        else:
            error_txt = _('Error! Data Source not set') 
            self.update_log_error(error_txt=error_txt,has_errors = True) 
            raise ValueError(error_txt)     
            return False
 
    def vision_match_field_label(self, field_name, index ):         
        
        for fld_label in index:
            
            label_fld_name = fld_label.fldname.lower().strip()
                        
            if  label_fld_name == field_name:
                return fld_label.fldlabel.lower().strip()
        return None
    
#############################################    
# Record Step Viewer  
    
    @api.multi
    def record_forward(self):
        
        if self.record_num  < self.tot_record_num :
            return self.step_record_next( direction='forward')
        else:
            raise ValueError( "End of Record Set")
        
    @api.multi
    def record_backward(self):
           
        if self.record_num > 1:  
            return self.onchange_record_num(direction="back")
        else:
            raise ValueError( "Beginning of Record Set")
    
    @api.onchange('record_num')          
    def onchange_record_num(self):
        
        return self.step_record_next(direction=False)
        
    def step_record_next(self,  direction = "forward"): 
        
        if self.record_num < 1:
            raise ValueError( "The Record Number must be positive value")
            return {}
        
        if self.src_type == 'odbc':
            
            vals = self.odbc_get_next_record( direction)        
        
        elif self.src_type == 'csv':
            
            vals = self.cvs_get_next_record( direction)
        
        elif self.src_type == 'dbf':
            
            vals = self.dbf_get_next_record( direction)
            
        else:
            return {}    
        
        return {"value":{"header_ids":vals, "record_num":self.record_num}} 
        
    def get_next_record(self, import_record, direction=False):
       
        if not import_record:
            error_txt = _("No Import Record Values")
            return self.show_warn(error_txt)
            
         
        header_ids_vals = []
           
        for field in self.header_ids:
            try:
                skip = False
                field_val = self.get_field_val_from_record(import_record, field)
                                
                if field.search_filter or field.skip_if_empty or field.skip_filter:

                    if direction and  self.skip_current_row_filter(field_val, field):
                        
                        if direction == "backward":self.rec_number -= 1
                        else: self.rec_number += 1 
                        skip = True
                        
                if skip and direction:
                    return {'next':True,'header_vals':None}
                
                val = {'field_val': field_val}
                header_ids_vals.append((1, header_rec.id, val))
            except:
                error_txt = ( "Error field %s" % (field.name,))
                self.update_log_error(error_txt=error_txt)
                raise  ValueError(error_txt)
        return {'next':False, 'header_vals' :header_id_vals}
    
    def dbf_get_next_record(self,  direction=False):
        
        global dbf_table
        
        if not dbf_table:
            dbf_table = dbf.Table(self.dbf_path)
            if not dbf_table:
                
                e = 'Error opening DBF Import  %s:' % (self.dbf_path,)
                _logger.error(_('Error %s' % (e,)))
                raise  ValueError( e)
                return False
            
            dbf_table.open()
            self.row_count = len(dbf_table)
            
        while self.record_num < self.tot_record_num or self.record_num > - 1:
            
            import_record = dbf_table[self.record_num]
            res = self.get_next_record( import_record, direction)
            if res['next'] == False:
                return res.get(header_vals,False)
            
        return 
             
    def csv_get_next_record(self,  direction=False):
      
        global csv_file
        
        if not csv_file:
            csv_file = self.get_csv_data_file()
            
        vals = {}
        
        while self.record_num < self.tot_record_num or self.record_num > - 1: 
            
            import_record = self.convert_cvs_row_dict(header_dict, csv_file[self.record_num])
            res = self.get_next_record(import_record, direction)
            if res['next'] == False:
                return res.get(header_vals,False)
                
        return
    
    def odbc_get_next_record(self, direction=False):
        
        return self.show_warn("Not Active Functionality")
        global odbc_cursor
        global current_record
        
        if not odbc_cursor:
            self.record_num                
            conn = self.env['base.external.dbsource'].conn_open( self.base_external_dbsource.id)
            odbc_cursor = conn.cursor()
            
            self.tot_record_num = self.get_row_count_odbc(self.odbc_import_query(),odbc_cursor)
            
            qry = self.odbc_import_query()
            odbc_cursor.open(qry)
            odbc_cursor.fetchone()
       
        while self.record_num < self.tot_record_num or self.record_num > - 1:
            
            skip = self.record_num - current_record 
            if skip:
                for import_record in odbc_cursor.skip(skip):
                    continue
                
            else:
                for import_record in odbc_cursor:
                    continue

            
            res = self.get_next_record(import_record, direction)
            if res['next'] == False:
                return res.get(header_vals,False)
                
        return    
                                            