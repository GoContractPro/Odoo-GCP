# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _

class ir_cron(models.Model):


    _inherit = "ir.cron"
    
    import_data_ids =  fields.One2many('import.data.file','ir_cron_id', string="Import Data Source",)
    is_import_data_job = fields.Boolean('Is Import Job')
    email_to =  fields.Many2many('res.partner', 'ir_cron_res_partner_rel','ir_cron_id','res_partner_id',string='Email Partner')
   
    @api.multi
    def action_select_data_imports(self):
        return {
            'name': 'Imports',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'import.data.file',
            'type': 'ir.actions.act_window',
            'domain': [('ir_cron_id','=',False)]
        }
        
        