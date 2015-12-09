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
            'person_dropping_of':fields.many2one('res.partner','Person Dropping Off')
              }
    
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
    _columns={
               'is_service_repair':fields.boolean('Is Service Repair ?'),
               'sale_order_ids':fields.many2many('sale.order','sale_order_task_rel','task_id','sale_id','Sales Order'),
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




    


