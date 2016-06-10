# -*- coding: utf-8 -*-
#See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _
from openerp.exceptions import UserError
from openerp.tools import float_is_zero, float_compare

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
   
    tasks_ids = fields.Many2many('project.task', compute='_compute_tasks_ids', string='Tasks associated to this sale line')
    tasks_count = fields.Integer(string='Tasks', compute='_compute_tasks_ids')


    
    @api.multi
    @api.depends('product_id.project_id')
    def _compute_tasks_ids(self):
        for order_line in self:
            domain = ['|',('sale_line_id', '=', order_line.id),('sale_line_id2', '=', order_line.id)]
            order_line.tasks_ids = self.env['project.task'].search(domain)
            order_line.tasks_count = len(order_line.tasks_ids)
    
    @api.multi
    @api.depends('name', 'order_id.name')
    def name_get(self):
        result = []
        for line in self:
            name = line.order_id.name + ':' + line.name
            result.append((line.id, name))
        return result
    
    @api.multi
    def _compute_analytic(self, domain=None):
        if not domain:
            # To filter on analyic lines linked to an expense
            domain = [('so_line', 'in', self.ids), '|', ('amount', '<=', 0.0), ('is_timesheet', '=', True) ,('do_not_invoice','=',False)]
        return super(SaleOrderLine, self)._compute_analytic(domain=domain)
    
    '''
    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state','order_id.start_date','order_id.end_date')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.order_id.state in ['sale', 'done']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    if line.product_id.track_service in ['timesheet','task']:
                        line.qty_to_invoice = sum(line.amount for line in self._get_so_line_analytic_lines_by_date(False, line.order_id.start_date, line.order_id.end_date))
                    else:
                        line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0
    '''
    
    @api.multi
    def _get_invoice_analytic_lines(self,invoiced=False):
        
        domain = [('so_line','=',self.id),('do_not_invoice','=',False)]
        if not invoiced: domain.append(('invoice_line','=',False))
        else: domain.append(('invoice_line','!=',False))
        
        if self.order_id.start_date: domain.append(('date','>=',self.order_id.start_date))
        if self.order_id.end_date: domain.append(('date','<=',self.order_id.end_date))
        return self.env('account_analytic_line').search(domain)
        

            
    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).

        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'sale_line_ids': [(6, 0, [line.id])]})
                invoice_line = self.env['account.invoice.line'].create(vals)
        
                if line.product_id.track_service in ('timesheet','task'):
                    domain = [('so_line','=',line.id),('product_id','=', line.product_id.id),
                              ('account_id','=',line.order_id.project_id.id),('invoice_line','=',False)]
                    if line.order_id.start_date: domain.append(('date','>=',line.order_id.start_date))
                    if line.order_id.end_date: domain.append(('date','<=',line.order_id.end_date))
                    lines_to_update = self.env['account.analytic.line'].search(domain) 
                    lines_to_update.write({'invoice_line':invoice_line.id})
                    
    def reset_analytic_so_line(self, track_service_list = ['task','timesheet'] ):
        for line in self:
            if line.product_id.track_service in track_service_list :
                so_lines = self.env['account.analytic.line'].search([('so_line','=',line.id),('invoice_line','=',False)])
                so_lines.write({'so_line':False, 'product_id':False})
                    
    def set_analytic_so_line(self):

        self.reset_analytic_so_line()     
        for line in self:
            
            if line.product_id.track_service == 'task':
                 
                tasks = self.env['project.task'].search(['sale_line_id','=',line.id]) 
                domain = [('invoice_line','=',False),('product_id','=', False),
                          ('so_line','=',False),('account_id','=',line.order.project_id.id),
                          ('so_line','=',line.id), ('task_id','in',tasks.ids)]
                if line.order_id.start_date: domain.append(('date','>=',line.order_id.start_date))
                if line.order_id.end_date: domain.append(('date','<=',line.order_id.end_date))
                    
                lines_to_update = self.env['account.analytic.line'].search(domain)
                lines_to_update.write({'so_line':line.id,'product_id':line.product_id.id})
                
        for line in self:
            if line.product_id.track_service == 'timesheet':
                
                tasks = self.env['projec.task'].search([('sale_line_id2','=',False),('sale_line_id','=',False),
                                                        ('analytic_account_id','=',line.order_id.project_id.id)])
                tasks.write({'sale_line_id2':line.id}) 
                break
            
        for line in self:
            
            if line.product_id.track_service == 'timesheet':
                
                tasks = self.env['project.task'].search([('sale_line_id2','=',line.id),
                                                        ('analytic_account_id','=',line.order_id.project_id.id)])

                
                domain = [('invoice_line','=',False),('product_id','=', False),
                          ('so_line','=',False),('account_id','=',line.order.project_id.id),
                          ('task_id','in',tasks.ids)]
                if line.order_id.start_date: domain.append(('date','>=',line.order_id.start_date))
                if line.order_id.end_date: domain.append(('date','<=',line.order_id.end_date))
                    
                lines_to_update = self.env['account.analytic.line'].search(domain)
                
                lines_to_update.write({'so_line':line.id,'product_id':line.product_id.id})
                
               
        self._compute_analytic()
        
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'   
    
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    
   
    @api.onchange('start_date','end_date')
    def _onchange_invoiced_dates(self):
    
        for order in self:
            
            order.order_line.set_analytic_so_line()
        
    @api.multi
    def action_confirm(self):
        
        for order in self:
            if order.project_id:
                
                order.order_line.set_analytic_so_line()
                    
        return super(SaleOrder,self).action_confirm()
    
    @api.multi
    def action_cancel(self):
        
        self.order_line.reset_analytic_so_line()
        super(SaleOrder.self).action_cancel()
        
    
    def get_analytic_so_lines_for_project(self, task ):
        so_lines = []
        if task: project = task.project_id
        if project:
            
            res = self.search(['project_id','=',project.analytic_account_id.id])
            for so in res:
                for line in so.order_lines:
                    if line.product_id.track_service in ['task','timesheet']:
                        so_lines.append(line.id)
        return so_lines               