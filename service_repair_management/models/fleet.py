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

class fleet_vehicle(osv.osv):
    _inherit = 'fleet.vehicle'
    
    def _vehicle_name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        if not context.get('default_is_service_repair',False):
            for record in self.browse(cr, uid, ids, context=context):
                res[record.id] = record.model_id.brand_id.name + '/' + record.model_id.modelname + ' / ' + record.license_plate
        else:
            for record in self.browse(cr, uid, ids, context=context):
                if not record.unit :
                    raise osv.except_osv(_('Error!'), _('Please fill the Unit value !'))
                if not record.make :
                    raise osv.except_osv(_('Error!'), _('Please fill the Make value !'))
                if not record.model:
                    raise osv.except_osv(_('Error!'), _('Please fill the Model value !'))
                res[record.id] = record.unit + '/' + record.make + ' / ' + record.model
        return res

    _columns={
              'name': fields.function(_vehicle_name_get_fnc, type="char", string='Name', store=True),
               'license_plate': fields.char('License Plate', help='License plate number of the vehicle (ie: plate number for a car)'),
              'unit':fields.char('Unit',size=64),
               'make':fields.char('Make',size=64),
              'model':fields.char('Model',size=64),
              'is_service_repair':fields.boolean('Is Service Repair ?'),
              'model_id': fields.many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle'),
              }
fleet_vehicle()