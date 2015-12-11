###############################################################################################
#Make sure the copyright information is correct (Copyright (C) 2011 NovaPoint Group LLC 
#(<http://www.novapointgroup.com>) and placed on top of OpenERP certification line and reflects
# Novapoint Group, Inc as the author 
#
#################################################################################################
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp.osv import fields, osv
from openerp.tools.translate import _

class hr_timesheet_invoice_create(osv.osv_memory):
    _inherit='hr.timesheet.invoice.create'
    _columns={
              'is_service_repair':fields.boolean('Is service repair'),
              }
    
    def view_init(self, cr, uid, fields, context=None):
        
        analytic_obj = self.pool.get('account.analytic.line')
        data = context and context.get('active_ids', [])
        if not context.get('default_is_service_repair',False):
            for analytic in analytic_obj.browse(cr, uid, data, context=context):
                if analytic.invoice_id:
                    raise osv.except_osv(_('Warning!'), _("Invoice is already linked to some of the analytic line(s)!"))
    
    def do_create(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, context=context)[0]
        # Create an invoice based on selected timesheet lines
        if not context.get('default_is_service_repair',False):
            invs = self.pool.get('account.analytic.line').invoice_cost_create(cr, uid, context['active_ids'], data, context=context)
        else:
            analytic_lst=[]
            for rec in self.pool.get('project.task').browse(cr,uid,context.get('active_ids'),context=context):
                analytic_lst=[work_line.hr_analytic_timesheet_id.line_id.id for work_line in rec.work_ids]
            invs = self.pool.get('account.analytic.line').invoice_cost_create(cr, uid, analytic_lst, data, context=context)
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        mod_ids = mod_obj.search(cr, uid, [('name', '=', 'action_invoice_tree1')], context=context)
        res_id = mod_obj.read(cr, uid, mod_ids, ['res_id'], context=context)[0]['res_id']
        act_win = act_obj.read(cr, uid, [res_id], context=context)[0]
        act_win['domain'] = [('id','in',invs),('type','=','out_invoice')]
        act_win['name'] = _('Invoices')
        return act_win
            
