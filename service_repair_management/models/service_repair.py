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
              'related_unit':fields.many2one('fleet.vehicle','Vehicle'),
              'need_quote':fields.boolean('Needs Quote ?'),
              'quote_approver':fields.many2one('res.partner','Quote Approver'),
              'repair_order_project':fields.boolean('Repair Order Project ?'),
              'eval_job':fields.many2one('project.task','Eval Job'),
              'is_service_repair':fields.boolean('Is Service Repair ?'),
              }
project()

class task(osv.osv):
    _inherit='project.task'
    _columns={
               'is_service_repair':fields.boolean('Is Service Repair ?'),
               'unit': fields.related('project_id', 'related_unit', type='many2one', relation='fleet.vehicle', string='Unit', readonly=True),
               'make': fields.related('unit', 'unit', type='char',  string='Make', readonly=True),
               'model': fields.related('unit', 'model', type='char',string='Model', readonly=True),
              }
task()




    


