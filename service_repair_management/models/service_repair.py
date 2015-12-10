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

from openerp.osv import osv,fields
from openerp.tools.translate import _

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
            'company_id':fields.many2one('res.company','Company'),
              }
    _defaults={
              'seq_no':'/',
              }
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
        return {'value': val}
 
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        # Prevent double project creation when 'use_tasks' is checked + alias management
        create_context = dict(context, project_creation_in_progress=True,
                              alias_model_name=vals.get('alias_model', 'project.task'),
                              alias_parent_model_name=self._name)
        if vals.get('seq_no', '/') == '/' and context.get('default_is_service_repair',False)==True:
            vals['seq_no'] = self.pool.get('ir.sequence').get(cr, uid, 'project.project', context=context) or '/'

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
               'sale_order_ids':fields.many2many('sale.order','sale_order_task_rel','task_id','sale_id','Sales Order'),
               'is_sale':fields.boolean('Is Sale Order'),
               'sale_count': fields.function(_sale_count, string='View Sales', type='integer'), 
            'project_id': fields.many2one('project.project', 'Service Repair Order', ondelete='set null', select=True, track_visibility='onchange', change_default=True),
              }
    
#     def action_create_invoice(self,cr,uid,ids,context=None):
#         sale_obj = self.pool.get('sale.order')
#         so_ids = []
#         for rec in self.browse(cr,uid,ids,context=None):
#             defaults = sale_obj.onchange_partner_id(cr, uid, [],rec.project_id.partner_id.id , context=context)
#             if rec.project_id and rec.project_id.partner_id and rec.project_id.partner_id.id :
#                 defaults = sale_obj.onchange_partner_id(cr, uid, [],rec.project_id.partner_id.id , context=context)['value']
#                 defaults.update({
#                      'partner_id':rec.partner_id and rec.partner_id.id or False,
#                      'service_repair_project_id':rec.project_id and rec.project_id.id or False
#                      })
#                 ctx = dict(context or {}, mail_create_nolog=True)
#                 so_ids = sale_obj.create(cr, uid, defaults, context=ctx)
#                 self.write(cr,uid,rec.id,{'is_sale':True,'sale_order_ids':[(4,so_ids)]})
#             else:
#                 so_ids += [saleorder.id for saleorder in rec.sale_order_ids]
#         return self.action_view_invoice( cr, uid, ids, so_ids, context=context)

   
    def convert_to_quotation(self,cr,uid,ids,context=None):
        sale_obj = self.pool.get('sale.order')
        so_ids = []
        for rec in self.browse(cr,uid,ids,context=None):
            defaults = sale_obj.onchange_partner_id(cr, uid, [],rec.project_id.partner_id.id , context=context)
            if rec.project_id and rec.project_id.partner_id and rec.project_id.partner_id.id :
                defaults = sale_obj.onchange_partner_id(cr, uid, [],rec.project_id.partner_id.id , context=context)['value']
                defaults.update({
                     'partner_id':rec.partner_id and rec.partner_id.id or False,
                     'service_repair_project_id':rec.project_id and rec.project_id.id or False
                     })
                ctx = dict(context or {}, mail_create_nolog=True)
                so_ids = sale_obj.create(cr, uid, defaults, context=ctx)
                self.write(cr,uid,rec.id,{'is_sale':True,'sale_order_ids':[(4,so_ids)]})
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
        
#     def action_view_invoice(self, cr, uid, ids, context=None):
#         '''
#         This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
#         '''
#         mod_obj = self.pool.get('ir.model.data')
#         act_obj = self.pool.get('ir.actions.act_window')
# 
#         result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree1')
#         id = result and result[1] or False
#         result = act_obj.read(cr, uid, [id], context=context)[0]
#         #compute the number of invoices to display
#         inv_ids = []
#         for so in self.browse(cr, uid, ids, context=context):
#             inv_ids += [invoice.id for invoice in so.invoice_ids]
#         #choose the view_mode accordingly
#         if len(inv_ids)>1:
#             result['domain'] = "[('id','in',["+','.join(map(str, inv_ids))+"])]"
#         else:
#             res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_form')
#             result['views'] = [(res and res[1] or False, 'form')]
#             result['res_id'] = inv_ids and inv_ids[0] or False
#         return result
        
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

class sale_order(osv.osv):
    _inherit='sale.order'
    _columns={
              'service_repair_project_id':fields.many2one('project.project','Main Project')
              }
sale_order()





    


