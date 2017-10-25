# -*- coding: utf-8 -*-
#See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, exceptions, _

from openerp.exceptions import UserError
from lxml import etree
from openerp.osv.orm import  setup_modifiers

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    
    invoice_line = fields.Many2one('account.invoice.line', 'Invoice Line',readonly=True)
    locked = fields.Boolean(compute='_check_lock', string="Locked")
    do_not_invoice = fields.Boolean('Activity Not Invoiced')
    
    _defaults = {'account_id': lambda self, cr, uid, ctx=None: ctx.get('default_account_id') if ctx is not None else False,
                 
        }

    def _get_sale_order_line(self, vals=None):
        
        result = super(AccountAnalyticLine, self)._get_sale_order_line(vals)
        if self.is_timesheet and result.get('task_id'):
            task = self.env['project.task'].browse([result.get('task_id')])
            if task.sale_line_id:
                result.update({
                    'so_line': task.sale_line_id.id,
                    'product_id': task.sale_line_id.product_id.id,})
            if task.sale_line_id2:
                result.update({
                    'so_line': task.sale_line_id2.id,
                    'product_id': task.sale_line_id2.product_id.id,})
        return result
    '''      
    def  _check(self, cr, uid, ids, vals = []):
        for att in self.browse(cr, uid, ids):
            if att.invoice_line and ['sheet_id'] != vals.keys():      
                raise UserError(_('You cannot modify invoiced activities!'))
            if att.sheet_id and att.sheet_id.state not in ('draft', 'new') and ['invoice_line'] != vals.keys():
                raise UserError(_('You cannot modify an entry in a confirmed timesheet.'))
        return True
     '''
    @api.multi
    @api.depends('invoice_line','sheet_id.state')
    def _check_lock(self):
        
        for line in self:
            if line.sheet_id and line.sheet_id.state not in ('draft', 'new') or line.invoice_line:
                line.locked = True
            else:
                line.locked = False
        

    