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

import time
from openerp.osv import fields,osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class delivery_carrier(osv.osv):
    _inherit = "delivery.carrier"


    def _get_company_code(self, cr, user, context=None):
        return [('grid', 'Price Grid')]
    
    _columns = {
        'name': fields.char('Delivery Type', size=24, required=True),
        'ship_company_code': fields.selection(_get_company_code, 'Method Type', method=True,size=64),
        'ship_income_account_id': fields.property(type='many2one',relation='account.account', string="Shipping Income GL Account",view_load=True,
                                required=True, help='This account represents the g/l account for booking shipping income.'),
        'invoice_ship_act_cost': fields.boolean('Invoice on Actual Costs', help = 'Invoice using actual shipping costs from packages not using quoted ship charges as quoted on Sales Order')
     }


