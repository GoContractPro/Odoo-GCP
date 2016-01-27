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

row_count = 0
count = 0

class import_data_file(models.Model): 
    
    _inherit = "import.data.file"
    
    external_id_field = fields.Many2one('import.data.header', string='External Id Field', domain="[('import_data_id','=',active_id)]")
           
    @api.multi
    @api.onchange('external_id_field')
    def _onchange_external_id_field(self):
        
        for fld in self.header_ids:
            
            if self.external_id_field.id ==  fld.id:
                fld.is_unique_external = True
            else: 
                fld.is_unique_external = False
                
    @api.multi
    def check_selection_field_value(self,model,field,field_val):
        
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
    def check_external_id_name(self, external_id_name = False):  
        rec = self  
        #  When Using field for External ID 
        if external_id_name:
            return external_id_name 
        #  When using Record Row External ID and No field External ID            
        elif rec.record_external:         
            return ('%s_%s' % ( rec.name,row_count,))
        else:
            return False    
    
    @api.multi
    def get_external_name(self, import_record, fields = False):
        rec =  self
        external_name = False
        for field in fields:
            if field.is_unique_external:
                field_val = self.get_field_val_from_record(import_record,  field)
                field = self.convert_odoo_data_types(field, field_val, import_record)
                if not external_name: external_name = field_val
                else: external_name += '/' + field_val
        return self.check_external_id_name(external_name)
       
    @api.multi
    def search_external_id(self, external_id_name, model): 
                
        search = [('name','=',external_id_name),('model','=', model)]                     
        record =  self.env['ir.model.data'].search(search) or None
        if record:
            return record.res_id or False
        else:
            return False  
                 
    @api.multi
    def search_unique_id(self, fields, import_record, model  ):
        
        rec = self
        search_unique = []
        for field in fields:
            if field.is_unique:
                field_val = self.get_field_val_from_record(import_record,  field)
                result = self.convert_odoo_data_types(field, field_val, import_record)
                field_val = result and result.get('field_val',False)
                if not field_val: 
                    error_txt = _('Error: Required unique field %s is not set' % (field.model_field.name))
                    self.update_log_error(error_txt=error_txt)
                    return -1
                search_unique.append((field.model_field.name,"=", field_val))
        
        if len(search_unique) > 0:      
            record = self.env[model.model].search(search_unique)
            if record:
                try:
                    record.ensure_one()
                    return record.id
                except:
                    error_txt = _('Error: Unique Record duplicates found in model %s, search on values %s' % (model.model, search_unique, ))
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
            error_txt = _('Warning: External Id and Unique Field not Id not matched  %s <> %s external Id will be used' % (external_id, search_unique_id, ))
            self.update_log_error( rec, error_txt)
            search_result['res_id'] = external_id
            return search_result
       
        search_result['res_id'] = external_id or search_unique_id
           
        return search_result
    @api.multi
    def do_search_related_records(self, field, import_record, field_val): 
        
        model = field.relation_id.model
        
        search_result = self.do_search_record(fields= field.child_ids, import_record= import_record , model=field.relation_id)                     
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
            search = [(field.search_other_field.name,'=',field_val)]
            result = self.env[model].search(search)
            if result:
                if result.ensure_one():
                    search_result['res_id'] = result.id or False
                    return search_result
                else:
                     error_txt = _('Warning: duplicate records found in model %s, search on %s' % (model, search, ))
                     self.update_log_error(error_txt=error_txt)      
        
        # If not found then do  New External and Search unique Using the Child Map Related Fields settings

                
    
    @api.multi
    def get_o2m_m2m_vals(self, field, field_val, import_record ): 
        
        rec = self
               
        search_result = self.do_search_related_records(field, import_record, field_val)
        res_id = search_result.get('res_id', False)
        external_id_name = search_result.get('external_id_name',False)
        if res_id == 0 and not field.create_related:
            return False
        if res_id == -1:
            return False
        
        if res_id == 0 and field.create_related:
            odoo_vals = self.do_related_vals_mapping(field=field, import_record=import_record)
            if not odoo_vals['required_missing']: 
                res_id = self.create_import_record( vals=odoo_vals['field_val'], external_id_name=external_id_name, 
                                                    model = field.relation) 
                
        if res_id:
            
            return {'field_val':(4,res_id)}
        else: 
            return False
     
    @api.multi
    def do_related_vals_mapping(self, field, import_record):
        
        rec = self
        vals={}
        for rel_field in field.child_ids:

            if not rel_field.model_field:
                continue
            field_val = self.get_field_val_from_record(import_record, field=rel_field)
           
            odoo_vals = self.convert_odoo_data_types(field=rel_field, field_val=field_val, import_record=import_record)  
            if odoo_vals['required_missing']:
                vals = None
                break 
            
            vals[rel_field.model_field.name] = odoo_vals['field_val']
                                                 
            #TODO add functionality to build other Relate values defaults from list or other Tables
        return {'required_missing':odoo_vals['required_missing'], 'field_val': vals}

    @api.multi    
    def convert_odoo_data_types( self, field, field_val, import_record=None, current_fld_val=None):
        rec = self
        # Update Field value if Substitution Value Found. 
        field_val = self.do_substitution_mapping(field_val,field)
        
        if field.model_field_type == 'many2one' and field_val:
            
            search_result = self.do_search_related_records(field, import_record, field_val)
            if not search_result: res_id = False
            else: 
                res_id = search_result.get('res_id',False)
                
                external_id_name = search_result.get('external_id_name',False)
            
                if not res_id and field.create_related: 
                    res_id = self.create_related_record(import_record=import_record, field=field, field_val=field_val, external_id_name=external_id_name)
                
                if res_id == -1: 
                    res_id = False
                
            field_val = res_id
        
        elif field.model_field_type == 'boolean' and  field_val:

            try:
                field_val = field_val.lower()
                if field_val in ('1','t','true','y','yes'):
                    field_val = True
                elif field_val in ('0','f','false','n','no',''):
                    field_val = False
                else:
                    field_val = False
                    error_txt = ('Error: Field value %s -- %s is not Boolean type value set False' % (field.model_field.name,field_val,))
                    self.update_log_error(rec, error_txt)
                
            except:
                field_val = False
                error_txt = ('Error: Converting Field %s -- %s to Boolean value set False' % (field.model_field.name,field_val,))
                self.update_log_error(rec, error_txt)
            
        elif field.model_field_type == 'float' and  field_val:
                
            if field_val.lower() == 'false': field_val = '0.0'
            
            try:
                field_val = float(field_val)
            except:
                rec.has_errors = True
                field_val = 0.0
                error_txt = _('Error: Field %s -- %s is not required  Floating Point type' % ( field.model_field.name,field_val))
                self.update_log_error(error_txt=error_txt)

        elif field.model_field_type == 'integer' and  field_val:
              
            if field_val.lower() == 'false': field_val = '0'
            try:
                field_val = int(field_val)
            except:
                rec.has_errors = True
                field_val = 0
                error_txt = _('Error:  Field %s -- not required Integer  type' % (field.model_field.name,field_val))
                self.update_log_error(error_txt=error_txt)

        elif field.model_field_type == 'selection' and  field_val:
            
            field_val = self.check_selection_field_value(field.model.model, field.model_field.name, field_val)
            
            if field_val:
                pass
            else:
                rec.has_errors = True
                field_val = False
                error_txt = _('Error: Field %s -- %s is correct Selection Value' % ( field.model_field.name,field_val))
                self.update_log_error(rec, error_txt)
        
        elif field.model_field_type in ['char', 'text','html'] and  field_val:
            pass
        elif field.model_field_type == 'binary' and  field_val:
            
            pass
        elif field.model_field_type in ['one2many','many2many']:
   
            result = self.get_o2m_m2m_vals(field=field, field_val=field_val, import_record=import_record)
            field_val = result and [result.get('field_val',False)] or False
            
        if current_fld_val:
            
            if field.model_field_type in ['one2many','many2many']:
            
                if field_val: 
                    current_fld_val.append(field_val)
                    field_val = current_fld_val
                else:field_val = current_fld_val
                
            elif field.model_field_type in ['char', 'text','html']:
                if field_val: field_val = field_val + current_fld_val
            else:
                if field_val and current_fld_val:
                    error_txt = _('Warning: Odoo field has been Mapped to multiple source fields, Last value found used for import')
         
        # If field is marked as Unique in mapping append to search on unique to use to confirm no duplicates before creating new record    
        if field.model_field.required and not field_val:
            rec.has_errors = True
            error_txt = _('Error: Required field %s  has no value ' % (field.model_field.name ))
            self.update_log_error(rec, error_txt)
            required_missing =  True
        else: required_missing =  False
        
        return {'required_missing':required_missing,'field_val':field_val}
     
    @api.multi    
    def do_substitution_mapping(self,field_val,field):
        
        substitutes = {}
        #if field.substitutions:
        #    for sub in field.substitutions:
        #       substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()})
        
        for sub in field.substitute_sets.import_m2o_substitutions:
            substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()})
         
        try:    
            #see if m20 map exist
            for sub in  field.substitution_m2o_ids:       
                substitutes.update({str(sub.src_value).strip() : str(sub.odoo_value).strip()}) 
        except:
            pass       
        return substitutes.get(field_val, field_val)
                    
    def get_field_val_from_record(self, import_record,field): 
               
        src_type = self.src_type
        
        if not field.name:
            return field.default_val
                
        if src_type == 'dbf':
            field_raw =  import_record[field.name] or False
        elif src_type == 'csv':
            field_raw = field.name and import_record[field.name]  or False
        elif src_type == 'odbc':
            field_raw =  field.name and getattr(import_record, field.name )  or False
        else: raise ValueError('Error! Source Data Type Not Set')
        
        
        if not field_raw  and field.default_val:
            return field.default_val
        if not field_raw:
            return False
        else: 
            if isinstance( field_raw, str):
                
                field_val = field_raw.strip()
                if field_val == "" and field.default_val:
                    field_val = field.default_val
    
            elif isinstance(field_raw, unicode):
                field_val =  field_raw.strip()
                if field_val == "" and field.default_val:
                    field_val = field.default_val
    
            elif isinstance(field_raw, datetime.datetime):
                field_val =  field_raw.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            
            elif isinstance(field_raw , datetime.date):
                field_val =  field_raw.strftime(DEFAULT_SERVER_DATE_FORMAT)
    
            elif isinstance(field_raw, bytearray):
                field_val =  base64.b64encode(field_raw)
            elif isinstance(field_raw, bool):
                field_val = str(field_raw)
            else: field_val =  str(field_raw)

        if field.sub_string:
            sub_str_split = field.sub_string.split(":")
            start = sub_str_split[0] or None
            end = sub_str_split[1] or None 
            start = int(start)
            end = int(end)
            field_val = field_val[start:end]
        
        return field_val                       

    @api.multi
    def create_related_record(self, import_record, field, field_val, external_id_name = False):
        
        rec = self
        vals = False
        res_id = False
        try:
            odoo_vals = self.do_related_vals_mapping( field=field, import_record=import_record)
            if odoo_vals['required_missing']:
                res_id = False
            else:
                vals = odoo_vals['field_val']
                res_id = self.create_or_update_record(0, vals, external_id_name, field.relation)

            if not res_id:
                log = _('Warning!: Related record for  value \'%s\' Not Created for relation \'%s\' row %s' % ( field_val, field.relation,row_count )) 
                rec.error_log += '\n'+ log
                _logger.info( log)
                return   False    
            
            return res_id
            
        except:
            self.env.cr.rollback()
            rec.has_errors = True
            error_txt = _('Error: Related record vals \'%s\'  for model \'%s\'' % (vals or 'No Values Dictionary Created' ,field.relation))
            self.update_log_error(error_txt=error_txt)
            
            return False
     
    def create_import_record(self,vals, external_id_name = False, model=False): 
        
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
                
            _logger.info(_('Created Record in %s with ID: %s %s from Source row %s' % (model, external_id_name ,res_id, row_count)))

            return res_id

        except:
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Error: Import vals %s not created for model \'%s\'' % (vals, model))
            self.update_log_error(error_txt=error_txt)
            
            return False
        
    def create_or_update_record(self, res_id, vals, external_id_name, model):        
        
        try: # Update or Create Records          
            
            if res_id == -1:
                # Errors in UNique Search or Duplicated records found.
                return False
  
            elif res_id == 0: 
                 res_id = self.create_import_record(vals=vals, external_id_name=external_id_name)
-                return res_id
                
            elif res_id and self.do_update:
                record_obj = self.env[model].browse(res_id)
                record_obj.write(vals)
                if record_obj: 
                    res_id = record_obj.id
                    _logger.info(_('Source row %s Updated Odoo Model %s ID: %s %s') % (  row_count,model, external_id_name or '', res_id,)) 
                    return res_id
                else:
                    _logger.info(_('Source row %s Update Failed Odoo Model %s ID: %s %s') % (  row_count,model, external_id_name or '', res_id,)) 
                    return False
            
            elif res_id and not self.do_update:
                error_txt = _(('Warning: %s Duplicate found in Odoo Model %s ID: %s %s, record skipped' )% (  row_count,model, external_id_name or '', res_id,)) 
                self.update_log_error(error_txt=error_txt)
                return False   
       
        except: # Error Writing or Creating Records
            self.env.cr.rollback()
            self.has_errors = True
            error_txt = _('Writing or Creating vals %s ' % ( vals,))
            self.update_log_error(error_txt=error_txt)
            return False
       
    @api.multi    
    def do_process_import_row(self, import_record):

        global row_count
        global count
        rec = self
        
        vals = {}
        search_unique =[]
        
        external_id_name = ''
        skip_record = False
        row_count += 1
       
        if row_count%25 == 0: # Update Statics every 10 records
            self.update_statistics( rec=rec, remaining=True)
                    
        for field in rec.header_ids:

            try:   # Building Vals DIctionary
                if not field.model_field: continue                       
                res_id = False
                field_val = False
                
                # test  Clean and convert Raw incoming Data values to stings to allow comparing to search filters and substitutions         
                field_val = self.get_field_val_from_record(import_record, field)
                if not field_val:continue
                    
                
                # IF Field value not found in Filter Search list skip out to next import record row
                if self.skip_current_row_filter(field_val,field.search_filter):
                    return False                          
                
               
                if not field.model_field: continue # Skip to next Field if no Odoo field set
                
                #Convert to Odoo Data types and add field to Record Vals Dictionary
                odoo_vals = self.convert_odoo_data_types( field=field, field_val=field_val, import_record=import_record,
                                                                             current_fld_val=vals.get(field.model_field.name, False))
                if odoo_vals and odoo_vals['required_missing']:
                    return False                     
                    
                vals[field.model_field.name] = odoo_vals['field_val']
                                                            
            except: # Buidling Vals DIctionary
                self.env.cr.rollback()
                rec.has_errors = True
                error_txt = _('Error: Building Vals Dict at Field: %s == %s \n Val Dict:  %s ' %(field.model_field.name, field_val, vals,))
                self.update_log_error(error_txt=error_txt)
                skip_record = True
                return False
        
        if skip_record : # this Record does not match filter skip to next Record in import Source
            return False
        
        try:  # Finding existing Records  

            search_result = self.do_search_record( fields=rec.header_ids, import_record=import_record, model= rec.model_id)
            res_id = search_result.get('res_id', False)
            external_id_name = search_result.get('external_id_name', False)
        except: # Finding Existing Records
            self.env.cr.rollback()
            rec.has_errors = True
            error_txt = _('Error: Search for Existing records: %s-%s ' % (search_unique,external_id_name))
            self.update_log_error(error_txt=error_txt)                    
            return False
        
        if self.create_or_update_record(res_id, vals, external_id_name, rec.model_id.model):
            count += 1
            return count
        else:
            return False
  
    @api.multi
    def exit_test_mode(self, test_mode):
        
        rec = self
        
        if  test_mode and (count >= rec.test_sample_size  or row_count >= rec.test_sample_size + 100) :
            
            if rec.rollback: self.env.cr.rollback()
            # Exit Import Records Loop  
            return True
        elif not test_mode or not rec.rollback:
            self.env.cr.commit()
            return False
        return False

   
    @api.multi
    def update_log_error(self, rec= None, error_txt = ''):

        if not rec: rec =  self
        e = traceback.format_exc()
        
        if row_count:
            error_txt = 'Row: ' + str(row_count) + ' ' + error_txt
        logger_msg = error_txt + '\n' + 'TraceBack: ' + e[:2000]
        _logger.error(logger_msg)
        
        e = sys.exc_info()
        rec.error_log +=  error_txt + '\n'
        if e[2]:
            e = traceback.format_exception(e[0], e[1], e[2], 1)
            error_msg = e[2]
            rec.error_log +=  error_msg +'\n'
             
        log_vals = {'error_log': rec.error_log,
                'has_errors':rec.has_errors}
        self.write(log_vals)
        self.env.cr.commit()
        return log_vals
    
    @api.multi
    def update_statistics(self, rec, remaining=True):   
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
            
                        
        self.write(stats_vals) 
        
        return stats_vals
    
    @api.multi   
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
