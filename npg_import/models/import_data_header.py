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

class import_data_header_list(models.Model):
   
    _name = "import.data.header.list"
    _description = "List of  Source Data Header Columns"
    
    name = fields.Char('Source Field Name', size=64)
    field_label = fields.Char(string='Source Description', size=64,)
    field_type = fields.Char(string='Source Data Type', size=64,)
    field_val = fields.Char(string='Source Record Value', size=128)
    import_data_id = fields.Many2one(comodel_name='import.data.file', string='Data File Source', required=False, ondelete='cascade',) 

class import_data_header(models.Model): 

    @api.one
    def _get_import_source(self):
        self.import_source_filter = self.env.context.get('default_import_data_id', False)

    @api.one
    @api.depends('model_field')
    def _get_relation_id(self):
        
        if self.model_field:
            self.relation_id = self.env['ir.model'].search([('model','=',self.model_field.relation)])
        else:
            self.relation_id = None
            
    _name = "import.data.header"
    _description = "Map Odoo Fields to Import Fields"
    
    name = fields.Char('Source Field Name', size=64)
    field_label = fields.Char(string='Source Description', size=64,)
    field_type = fields.Char(string='Source Data Type', size=64,)
    field_val = fields.Char(string='Source Record Value', size=128)
    field_selector = fields.Many2one('import.data.header', string='Select Source Field', domain="[('import_data_id','=',import_data_id)]")
    header_list = fields.Many2one('import.data.header.list', string='Select Source Field', domain="[('import_data_id','=',import_data_id)]")
    import_data_id = fields.Many2one(comodel_name='import.data.file', string='Data File Source', required=False, ondelete='cascade',)
    parent_id = fields.Many2one(comodel_name='import.data.header', string='Parent Header Column', required=False, ondelete='cascade')
    child_ids = fields.One2many('import.data.header', 'parent_id', string="Child Header Column", copy=True,
                                 help="Default Values or source values to map to create related and parent records")
    is_unique = fields.Boolean(string='Use in Unique Search', help='Value for Field  Should be unique name or reference identifier and not Duplicated ')
    model = fields.Many2one(comodel_name='ir.model', string='Model')
    model_field = fields.Many2one(comodel_name='ir.model.fields', string='Odoo Field', domain="[('model_id','=',model)]")
    model_field_type = fields.Selection(related='model_field.ttype', string='Odoo Field Type', readonly=True)
    model_field_name = fields.Char(related='model_field.name', string='Odoo Field Name', readonly=True)
    relation = fields.Char(related='relation_id.model', string='Related Technical Name', size=128,
                    help="The technical name of  Model this field is related to"
                    , readonly=True)
    relation_id = fields.Many2one(comodel_name='ir.model', string='Related Model Name', compute='_get_relation_id', readonly=False, store=True)
    relation_field = fields.Char(related='model_field.relation_field', string='Odoo Related Field', size=128,
                    help="For one2many fields, the field on the target model that implement the opposite many2one relationship")
    search_filter = fields.Char('Filter Include', size=256,
                      help='''Use to create Filter on incoming records Field value in source must match values in list or row is skipped on import,
                           Can use multiple values for filter,  format as python type list for values example "value1","value2","value3". ''')           
    skip_filter = fields.Char('Filter Skip', size=256,
                      help='''Use to create Filter on incoming records Field value in source must match values in list or row is skipped on import,
                           Can use multiple values for filter,  format as python type list for values example "value1","value2","value3". ''')           
    skip_if_empty = fields.Boolean('Skip if Empty')
    create_related = fields.Boolean('Create Related', help="Will create the related records  if missing")
    update_related = fields.Boolean('Update Related', help="Will update the related records with source values if found")

    default_val = fields.Char(string='Default Import Val', size=256, help='The Default if no values for field in imported Source')
    substitute_sets = fields.Many2one(comodel_name='import.substitute.sets', string='Substitution Sets',
                                      help='Allows mapping and Converting values from Source Data into correct values for ODoo data ')
    is_unique_external = fields.Boolean('Use in External ID', readonly=False ,
                                help='Check if this field is Unique e.g. an Account Number or A vendor Number. Its value will be used in odoo external ID')
    o2m_external_field2 = fields.Many2one(comodel_name='import.data.header', string='[Deprecated]O2M External' , domain="[('import_data_id','=',import_data_id')]",
                                                      help='Deprecated -- use Map Related Fields instead')
    search_related_external = fields.Boolean(string='External ID Search',
                            help='''Selecting this Will use this import value For  searching External IDs on this Data model.
                                 Optionally it is possible to specify External Id search if adding fields to Map Related Fields
                                 this allows combining multiple fields to create External ID search value. ''')
    search_name = fields.Boolean(string='Name Search')
    search_other_field = fields.Many2one(comodel_name='ir.model.fields', string='Other Search Field', domain="[('model_id','=',relation_id)]",
                                help='Select field  to match in related record other than Name or External ID')
    sequence = fields.Integer('Sequence')
    sub_string = fields.Char('Substring', size=8)
    is_db_id = fields.Boolean('Is Record ID')
    m2o_skip = fields.Boolean('Many2One  Skip', help='Create  record only if the Many to One relation exists and is active')
      
    def _get_model(self, cr, uid, context=None):
        
        return context.get('model', False)
    
    def _get_import_data_id(self, cr, uid, context=None):
        return context.get('default_import_data_id', False)
    
    _defaults = {
                 'model':_get_model,
                 'search_name':False,
                 'import_data_id':_get_import_data_id
                 }
    
    _order = 'sequence,model_field'
   
    @api.onchange('header_list')
    def onchange_header_list(self):
        if self.header_list:
            self.name = self.header_list.name
            self.field_label = self.header_list.field_label 
            self.field_type = self.header_list.field_type
    
    @api.onchange('model_field')
    def onchange_model_field(self, model_field=None):

        fld = self.env['ir.model.fields'].browse(model_field)
        if fld:
            
            self.o2m_external_field1 = self.id

        else:

            self.o2m_external_field1 = False 



