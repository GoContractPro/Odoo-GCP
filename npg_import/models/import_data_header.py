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


class import_data_header(models.Model): 

    @api.one
    @api.depends('model_field')
    def _get_relation_id(self):
        
        if self.relation:
            model_ids = self.env['ir.model'].search([('model','=',self.relation)])
            self.relation_id = model_ids and model_ids[0]
        else:
            self.relation_id = False
            
    _name = "import.data.header"
    _description = "Map Odoo Fields to Import Fields"
    
    name=fields.Char('Import Field Name', size=64)
    field_label =fields.Char(string='Description', size=64,)
    field_type =fields.Char(string='Data Type', size=64,)
    field_val =fields.Char(string='Record Value', size=128)
    field_selector = fields.Many2one('import.data.header', 'Select Source Field', domain="[('import_data_id','=',import_data_id)]")
   
    import_data_id = fields.Many2one(comodel_name='import.data.file',string='Import Source',required=False, ondelete='cascade',)
    parent_id = fields.Many2one(comodel_name='import.data.header', string='Parent Header Field', required=False, ondelete='cascade')
    child_ids = fields.One2many('import.data.header', 'parent_id', string="Related Field Map", copy=True, 
                                 help="Default Values or source values to map to create related and parent records")
    is_unique = fields.Boolean(string='Use in Unique Search', help ='Value for Field  Should be unique name or reference identifier and not Duplicated ')
    model = fields.Many2one(comodel_name='ir.model',string='Model')
    model_field = fields.Many2one(comodel_name='ir.model.fields',string='Odoo Field', domain="[('model_id','=',model)]")
    model_field_type = fields.Selection(related='model_field.ttype',readonly=True )
    model_field_name = fields.Char(related='model_field.name', readonly=True )
    relation=fields.Char(related='model_field.relation', size = 128,
                    help="The technical name of  Model this field is related to"
                    ,readonly=True)
    relation_id = fields.Many2one(comodel_name='ir.model', compute='_get_relation_id', string='Odoo Related Field', readonly=True)
    import_child_ids = fields.One2many('import.data.header','parent_id', string= 'Related Field', required=True, ondelete='cascade')
    relation_field = fields.Char(related='model_field.relation_field', string='Odoo Related Field', size = 128,
                    help="For one2many fields, the field on the target model that implement the opposite many2one relationship")
    search_filter =fields.Char('Filter Source', size=256,
                      help='''Use to create Filter on incoming records Field value in source must match values in list or row is skipped on import,
                           Can use mulitple values for filter,  format as python type list for values example "value1","value2","value3". ''')           
    create_related =fields.Boolean('Create Related', help = "Will create the related records using system default values if missing" )

    default_val =fields.Char(string='Default Import Val', size = 256, help = 'The Default if no values for field in imported Source')
    substitutions =fields.One2many('import.m2o.substitutions','header_map', string="Deprecated Source Value Substitutions", copy=True)
    substitution_ids =fields.Many2many('import.m2o.substitutions','import_substitution_rel','header_field_id','substitutions_id', string="Deprecated Source Value Substitutions", copy=True)
    substitute_sets = fields.Many2one(comodel_name='import.substitute.sets', string='Substitution Sets',
                                      help='Allows mapping and Converting values from Source Data into correct values for ODoo data ')
    is_unique_external =fields.Boolean('Use in External ID', readonly=False ,
                                help ='Check if this field is Unique e.g. an Account Number or A vendor Number. Its value will be used in odoo external ID')
    m2o_values = fields.One2many('import.m2o.values', 'import_field_id', string="Related Map", copy=True, 
                                 help="Deprecated (Default Values or source values to map to create related and parent records)")
    m2o_create_external =fields.Boolean('Create External on Related')
    o2m_external_field2 =fields.Many2one(comodel_name='import.data.header',string='[Deprecated]O2M External' , domain="[('import_data_id','=',import_data_id')]",
                                                      help='Deprecated -- use Map Related Fields instead' )
    search_related_external =fields.Boolean(string='External ID Search', 
                            help='''Selecting this Will use this import value For  searching External IDs on this Data model.
                                 Optionally it is possible to specify External Id search if adding fields to Map Related Fields
                                 this allows combining multiple fields to create External ID search value. ''')
    search_name = fields.Boolean(string='Name Search')
    search_other_field = fields.Many2one(comodel_name='ir.model.fields',string='Other Search Field', domain="[('model_id','=',relation_id)]", 
                                help='Select field  to match in related record othe than Name or External ID')
    related_import_source = fields.Many2one(comodel_name='import.data.file',string='Related Import Source',
                                           help='Secondary Table or file Source to provide Values for related Records')
    sequence = fields.Integer('Sequence')
    sub_string = fields.Char('Substring',size=8)
    
    
        
    def _get_model(self,cr,uid,context=None):
        return context.get('model',False)
    def _get_import_data_id(self,cr,uid,context=None):
        return context.get('default_import_data_id',False)
    
    _defaults = {
                 'model':_get_model,
                 'search_name':False,
                 'import_data_id':_get_import_data_id
                 }
    _order = 'sequence,model_field'
    
    
    @api.multi
    @api.onchange('field_selector')
    def onchange_field_selector(self):
        if self.field_selector:
            self.name = self.field_selector.name
            self.field_label = self.field_selector.field_label 
            self.field_val = self.field_selector.field_val
            self.field_type = self.field_selector.field_type
          
    @api.multi
    @api.onchange('model_field')
    def onchange_model_field(self, model_field = None):

        fld = self.env['ir.model.fields'].browse(model_field)
        if fld:
            
            self.o2m_external_field1 = self.id
        

        else:

            self.o2m_external_field1 =  False 



