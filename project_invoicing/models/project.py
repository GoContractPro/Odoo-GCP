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
    
class Analytic_Account(models.Model):
        
    _inherit = "account.analytic.account"
        
        

        
class Project_Poject(models.Model):
        
    _inherit = "project.project"

    @api.multi
    @api.depends('sale_order_ids')
    def _compute_sales_totals(self):
        
        for project in self:
            
            project.sale_orders_total = sum([order. amount_total for order in project.sale_order_ids])  
        
    sale_order_ids = fields.One2many('sale.order','project_id',string='Project Orders')
    sale_orders_total = fields.Float('Project Sale Total', compute='_compute_sales_totals')
    
    @api.multi
    def action_view_sale_orders(self):
        self.ensure_one()
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sale.action_orders')
        list_view_id = imd.xmlid_to_res_id('sale.view_order_tree')
        form_view_id = imd.xmlid_to_res_id('sale.view_order_form')

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if self.timesheet_count > 0:
            result['domain'] = "[('id','in',%s)]" % self.sale_order_ids.ids
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
