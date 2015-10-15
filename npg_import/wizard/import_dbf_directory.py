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



from openerp import models, fields, api,exceptions, _
import csv
import glob
import os
import sys
import dbf


from datetime import datetime
import time


import logging 
import sys          

_logger = logging.getLogger(__name__)

class import_dbf_directory(models.TransientModel): 
    
    _name = 'import.dbf.directory'
    _description = 'Create Import header maps for  all DBF files in Directory'
     
    dir_path = fields.Char('Source Directory',size=256) 
    
    @api.multi 
    def get_files_dbf(self, path):
        files = glob.glob(path+'*.dbf') + glob.glob(path+'/*.DBF')
        
        if not files: 
            raise exceptions.Warning('No DBF Files Found')
        return files
    
    @api.multi
    def action_load_dbf_files_headers(self):
        
        if self.dir_path:
           
            import_data_file = self.env['import.data.file'] 
            
            
            files = self.get_files_dbf(self.dir_path) or None
            for dbf_file in files:
                
                # test if file can be open and has data

                
                vals = {'name':os.path.basename(dbf_file),
                        'dbf_path': dbf_file,
                        }
                import_data_file = import_data_file.create(vals)           
                print dbf_file
                import_data_file.action_get_headers_dbf()
                self.env.cr.commit()
        else: 
            raise exceptions.Warning('Please Enter Direcrtory Path ')

            
                

                
                
                
                