# -*- coding: utf-8 -*-
#See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, exceptions, _

class Task(models.Model):
    _inherit = "project.task"
    
    sale_line_id2 = fields.Many2one('sale.order.line', string='Sale Orders Line', related='')
    invoice_parent_id = fields.Many2one('project.task',string='Parent Task',
                help='Parent tasks for organizing and linking multiple task to Sale order lines for invoicing',
                domain="[('project_id','=',project_id)]",)
    invoice_child_id = fields.One2many('project.task','invoice_parent_id',string='Child Tasks',
                help='Child tasks for organizing and linking multiple task to Sale order lines for invoicing')
    analytic_account = fields.Many2one(related='project_id.analytic_account_id',store=False, readonly=True,)
    
    
      
    @api.onchange('invoice_parent_id')
    def onchange_invoice_parent_id(self):
        self.procurement_id = self.invoice_parent_id.procurement_id
    
    @api.model   
    def default_procurement_id(self):
        return self._context.get('default_procurement_id',False)
        
        
    
    def onchange_project(self, cr, uid, ids, project_id, context=None):
        
        result = super(Task, self).onchange_project(cr, uid, ids, project_id, context=context)
        
        project = self.pool.get('project.project').browse(cr, uid, project_id, context=context)  
        if project:
            order_line = self.pool.get('sale.order.line').search(cr,uid,[
                ('order_id.project_id', '=', project.analytic_account_id.id),
                ('state', '=', 'sale'),
                ('product_id.track_service', '=', 'timesheet'),
                ('product_id.type', '=', 'service')],
                limit=1)
            if 'value' not in result:
                result['value'] = {}
            
            if order_line:
                result['value']['sale_line_id2'] = order_line[0]
        return   result 