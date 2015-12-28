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