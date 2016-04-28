# -*- coding: utf-8 -*-

from openerp import models, fields, api, exceptions, _

class ir_cron(models.Model):


    _inherit = "ir.cron"
    
    import_data_ids =  fields.One2many('import.data.file','ir_cron_id', string="Import Data Source")
    is_import_data_job = fields.Boolean('Is Import Job')
    
    @api.multi
    def action_import_scheduled(self):
        domain = [('state','=','ready'),('ir_cron_id','=',self.id)]
        recs = self.env['import.data.file'].search(domain,order='sequence' )
        for rec in recs:
            rec.action_import()