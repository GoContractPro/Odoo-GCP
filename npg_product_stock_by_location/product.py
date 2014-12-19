# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import time
from openerp import pooler
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
import openerp.addons.decimal_precision as dp
from openerp import netsvc

class product_product(osv.osv):
    _name = 'product.product'
    _inherit = 'product.product'

        
    def get_stock_locations(self, cr, uid, ids, field_names=None, arg=None, context=None):
        result = {}
        if not ids: return result

        context['only_with_stock'] = True

        for id in ids:
            context['product_id'] = id
            location_obj = self.pool.get('stock.location')
            result[id] = location_obj.search(cr, uid, [('usage', '=', 'internal')], context=context)

        return result


    _columns = {
        'stock_locations': fields.function(get_stock_locations, type='one2many', relation='stock.location', string='Stock by Location'),
    }


product_product()

