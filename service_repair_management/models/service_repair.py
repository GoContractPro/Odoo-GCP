#################################################################################################
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    (Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
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

from openerp.osv import osv,fields
from openerp.tools.translate import _
import time
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import exceptions

class project(osv.osv):
    _inherit = 'project.project'
    _columns={
              'item_tobe_repaired':fields.char('Items to be Repaired',size=128),
              'issue':fields.text('Issue',help="What is wrong"),
              'symptoms':fields.text('Symptoms',help="What are the symptoms or What is the unit doing or not doing"),
              'related_unit':fields.many2one('fleet.vehicle','Related Unit'),
              'need_quote':fields.boolean('Needs Quote'),
              'quote_approver':fields.many2one('res.partner','Quote Approver'),
              'repair_order_project':fields.boolean('Repair Order Project ?'),
              'eval_job':fields.many2one('project.task','Eval Job'),
              'is_service_repair':fields.boolean('Is Service Repair ?'),
              'unit': fields.char('Unit'),
              'make': fields.char('Make'),
            'model': fields.char('Model'),
            'person_dropping_of':fields.many2one('res.partner','Person Dropping Off'),
            'seq_no':fields.char('Service Repair Order'),
            'promise_date':fields.datetime('Promised Date'),
              }
    _defaults={
              'name':'/',
              }
    
    def copy(self, cr, uid, id, default=None, context={}):
        if default is None:
            default = {}
        name = '/'
        if context.get('default_is_service_repair',False):
            name = self.pool.get('ir.sequence').get(cr, uid, 'project.project', context=context) or '/'
        default.update({
            'name': name,
            'eval_job': False,
            'promise_date': False,
            'tasks' : [(6, 0, [])],
#             'analytic_account_id':False
        })
        res = super(project, self).copy(cr, uid, id, default=default, context=context)
        return res
        
    def onchange_partner_id(self, cr, uid, ids, part=False, context=None):
        partner_obj = self.pool.get('res.partner')
        val = {}
        company_id = False
        if not part:
            return {'value': val}
        if 'pricelist_id' in self.fields_get(cr, uid, context=context):
            pricelist = partner_obj.read(cr, uid, part, ['property_product_pricelist'], context=context)
            company_id = partner_obj.read(cr,uid,part,['company_id'],context=context)
            pricelist_id = pricelist.get('property_product_pricelist', False) and pricelist.get('property_product_pricelist')[0] or False
            val['pricelist_id'] = pricelist_id
            val['company_id'] = company_id.get('company_id',False)[0]
            val['related_unit'] = False
        return {'value': val}
 
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        # Prevent double project creation when 'use_tasks' is checked + alias management
        create_context = dict(context, project_creation_in_progress=True,
                              alias_model_name=vals.get('alias_model', 'project.task'),
                              alias_parent_model_name=self._name,partner_id=vals.get('partner_id',False))
        if vals.get('name', '/') == '/' and context.get('default_is_service_repair',False)==True:
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'project.project', context=context) or '/'

        if vals.get('type', False) not in ('template', 'contract'):
            vals['type'] = 'contract'

        project_id = super(project, self).create(cr, uid, vals, context=create_context)
        project_rec = self.browse(cr, uid, project_id, context=context)
        self.pool.get('mail.alias').write(cr, uid, [project_rec.alias_id.id], {'alias_parent_thread_id': project_id, 'alias_defaults': {'project_id': project_id}}, context)
        return project_id
    
    def onchange_related_unit(self, cr, uid, ids, related_unit, context=None):
        dic={}
        if related_unit:
            vehicle_obj = self.pool.get('fleet.vehicle').browse(cr, uid, related_unit, context=context)
            if vehicle_obj.unit:
                dic.update({'unit':vehicle_obj.unit or '' ,
                            'model':vehicle_obj.model or '' ,'make':vehicle_obj.make or ''})
        return {'value': dic}

project()

class sale_order(osv.osv):
    _inherit='sale.order'
    _columns={
              'job_id':fields.many2one('project.task','Task'),
              'requested_date':fields.datetime('Requested Date'),
              'quotation_sent_date':fields.datetime('Quotation Sent Date'),
              }
    
    def action_quotation_send(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_quotation_send(cr, uid, ids, context=context)
        self.write(cr,uid,ids,{'quotation_sent_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return res
    
    def print_quotation(self, cr, uid, ids, context=None):
        res = super(sale_order, self).print_quotation(cr, uid, ids, context=context)
        self.write(cr,uid,ids,{'quotation_sent_date':time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return res
    
    def action_wait(self, cr, uid, ids, context=None):
        res = super(sale_order, self).action_wait(cr, uid, ids, context=context)
        task_pool = self.pool.get('project.task')
        for o in self.browse(cr, uid, ids):
            if o.main_project_id and o.main_project_id.need_quote and not o.quotation_sent_date:
                raise exceptions.Warning(_("Please make sure the quotation is sent to the customer for his approval to proceed further"))
#             for line in o.order_line:
#                 if line.product_id and line.product_id.type == 'service' and line.product_id.auto_create_task:
#                     task_pool.create(cr,uid,{
#                                'name':o.name or '/',
#                                'project_id':o.main_project_id and o.main_project_id.id or False,
#                                'is_service_repair':True
#                                })
        return res
        

sale_order()

class procurement_order(osv.osv):
    _name = "procurement.order"
    _inherit = "procurement.order"
    
    def _create_service_task(self, cr, uid, procurement, context=None):
        task_id = super(procurement_order, self)._create_service_task(cr, uid, procurement, context=context)
        project_task = self.pool.get('project.task')
        project_task.write(cr,uid,task_id,{'project_id': procurement.sale_line_id and procurement.sale_line_id.order_id.main_project_id and procurement.sale_line_id.order_id.main_project_id.id or False, 'is_service_repair':True})
        return task_id
    
procurement_order()

class sale_order_line(osv.osv):
    _inherit='sale.order.line'
    
    def _get_time(self, cr, uid, ids, field_name, arg, context=None):
        so_ids = []
        res ={}
        task_pool = self.pool.get('project.task')
        for rec in self.browse(cr,uid,ids,context=None):
            hours = 0.0
            tasks_ids = task_pool.search(cr,uid,[('sale_line_id','=',rec.id)])
            for task in task_pool.browse(cr,uid,tasks_ids):
                hours += task.effective_hours
            res[rec.id] = hours
        return res
    
    _columns={
              'actual_time':fields.function(_get_time,string="Actual Time",type='float'),
              }
    
sale_order_line()
class task(osv.osv):
    _inherit='project.task'
    
    def _sale_count(self, cr, uid, ids, field_name, arg, context=None):
        so_ids = []
        res ={}
        for rec in self.browse(cr,uid,ids,context=None):
            so_ids = [sale.id for sale in rec.sale_order_ids]
            res[rec.id] = len(so_ids)
        return res
        
    _columns={
              
               'is_service_repair':fields.boolean('Is Service Repair ?'),
               #'sale_order_ids':fields.many2many('sale.order','sale_order_task_rel','task_id','sale_id','Sales Order'),
               'sale_order_ids':fields.one2many('sale.order','job_id','Sales Order'),
               'is_sale':fields.boolean('Is Sale Order'),
               'sale_count': fields.function(_sale_count, string='View Sales', type='integer'), 
               'promise_date':fields.datetime('Promised Date'),
              }
    
    def convert_to_quotation(self,cr,uid,ids,context=None):
        sale_obj = self.pool.get('sale.order')
        so_ids = []
        for rec in self.browse(cr,uid,ids,context=None):
            defaults = sale_obj.onchange_partner_id(cr, uid, [],rec.project_id.partner_id.id , context=context)
            if rec.project_id and rec.project_id.partner_id and rec.project_id.partner_id.id :
                defaults = sale_obj.onchange_partner_id(cr, uid, [],rec.project_id.partner_id.id , context=context)['value']
                defaults.update({
                     'partner_id':rec.partner_id and rec.partner_id.id or False,
                     'main_project_id':rec.project_id and rec.project_id.id or False,
                     'job_id':rec.id,
                     'requested_date':rec.project_id and rec.project_id.promise_date or False
                     })
                ctx = dict(context or {}, mail_create_nolog=True)
                so_ids = sale_obj.create(cr, uid, defaults, context=ctx)
                self.write(cr,uid,rec.id,{'is_sale':True})
            else:
                so_ids += [saleorder.id for saleorder in rec.sale_order_ids]
        return self.open_sale_order( cr, uid, ids, so_ids, context=context)
    
    def open_sale_order(self, cr, uid, ids, so_ids, context=None):
        """ open a view on one of the given so_ids """
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'sale', 'view_order_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'sale', 'view_quotation_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Sale Order'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'sale.order',
            'res_id': so_ids,
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'context': "{'type': 'out_invoice'}",
            'type': 'ir.actions.act_window',
        }
        
    def get_sale_order(self, cr, uid, ids, context=None):
        """ open a view on one of the given so_ids """
        so_ids = []
        for rec in self.browse(cr,uid,ids,context=None):
            so_ids = [sale.id for sale in rec.sale_order_ids]
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'sale', 'view_order_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'sale', 'view_quotation_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Sale Order'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'sale.order',
            'res_id': so_ids,
             'domain':[('id','in',so_ids)],
            'view_id': False,
            'views': [(tree_id, 'tree'),(form_id, 'form')],
            'context': "{'type': 'out_invoice'}",
            'type': 'ir.actions.act_window',
        } 
        
    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(task, self).default_get(cr, uid, fields, context=context)
        if context.get('default_is_service_repair',False)==True:
            res.update({'name': str(context.get('default_name'))+'-'+'Evaluation'})
        return res

task()

class res_partner(osv.osv):
    _inherit='res.partner'
    
    def _unit_count(self, cr, uid, ids, field_name, arg, context=None):
        Task = self.pool['fleet.vehicle']
        return {
            partner_id: Task.search_count(cr,uid, [('driver_id', '=', partner_id)], context=context)
            for partner_id in ids
        }
    _columns={
              'unit_count': fields.function(_unit_count, string='Unit', type='integer'), 
              }
res_partner()






    


