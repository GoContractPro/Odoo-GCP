# -*- coding: utf-8 -*-
#See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, exceptions, _

from openerp.exceptions import UserError

class ProcurementOrder(models.Model):
    
    _inherit = "procurement.order"
    
    
    def _create_service_task(self, cr, uid, procurement, context=None):
        
        task_id = super(ProcurementOrder,self)._create_service_task( cr, uid, procurement, context=None)
        
        
        self.pool.get('project.task').write(cr, uid,[task_id],{'sale_line_id': procurement.sale_line_id.id},context=context)
        return task_id