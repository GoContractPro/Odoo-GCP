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
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.addons.product._common import rounding
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP

class purchase_order(osv.Model):
    _inherit = 'purchase.order'

    def _set_minimum_planned_date(self, cr, uid, ids, name, value, arg, context=None):
        if not value: return False
        if type(ids) != type([]):
            ids = [ids]
        # Bad hack to make it work for Web-Client 6.0, as web-client 6.0 has an architectural issue with write operation
        # which calls this method when you change sale order line scheduled date, so just considered Line minimum planned date
        # After this fix Expected date of Sale Order will not be set explicitly
        planned_date = self.minimum_planned_date(cr, uid, ids, name, arg, context)
        for po in self.browse(cr, uid, ids, context=context):
            if planned_date and planned_date.get(po.id):
                 value = planned_date[po.id]
            if po.order_line:
                cr.execute("""update purchase_order_line set
                        date_planned=%s
                    where
                        order_id=%s and
                        (date_planned=%s or date_planned<%s)""", (value, po.id, po.minimum_planned_date, value))
            cr.execute("""update purchase_order set
                    minimum_planned_date=%s where id=%s""", (value, po.id))
        return True

    def minimum_planned_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for purchase in self.browse(cr, uid, ids, context=context):
            res[purchase.id] = False
            if purchase.order_line:
                min_date = purchase.order_line[0].date_planned
                for line in purchase.order_line:
                    if line.date_planned < min_date:
                        min_date = line.date_planned
                res[purchase.id] = min_date
        return res

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'promise_date' : fields.date('Promised Date'),
        'incoterm_id': fields.many2one('stock.incoterms', 'Incoterm', help="Incoterm which stands for 'International Commercial terms' implies its a series of sales terms which are used in the commercial transaction."),
        'requester': fields.char('Requester', size=128),
        'active': fields.boolean('Active'),
        'minimum_planned_date':fields.function(minimum_planned_date, fnct_inv=_set_minimum_planned_date, string='Expected Date', type='date', select=True, help="This is computed as the minimum scheduled date of all purchase order lines' products.",
            store={
                'purchase.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'purchase.order.line': (_get_order, ['date_planned'], 10),
            }, method=True,
        ),
        'partner_contact_id':fields.many2one('res.partner', 'Ordering Contact', readonly=True, required=True,
            states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},domain="[('parent_id', '=', partner_id)]"),
    }
    _defaults = {
        'active':True
        }

    def onchange_partner_id(self, cr, uid, ids, part):
        ret_val = super(purchase_order, self).onchange_partner_id(cr, uid, ids, part)
        ret_val['value'].update({'incoterm_id': False})
        if not part:
            return ret_val
        part = self.pool.get('res.partner').browse(cr, uid, part)
        addr = self.pool.get('res.partner').address_get(cr, uid, [part.id], ['contact'])
        ret_val['value'].update({'partner_contact_id': addr['contact']})
        incoterm_id = part.incoterm.id or False
        if incoterm_id:
            ret_val['value'].update({'incoterm_id': incoterm_id})
        return ret_val

class product_category(osv.Model):
    _inherit = 'product.category'
    _columns = {
            'active': fields.boolean('Active')
    }

    _defaults = {
	'active': True
    }

class product_product(osv.Model):
    _inherit = 'product.product'
    _columns = {
            'cust_code': fields.char('Customer Ref #', size=128)
    }

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
            context=None, count=False):
        if context is None:
            context = {}
        prod_code = False
        if args:
            procodes = [x[0] for x in args]
            if 'default_code' in procodes and not context.get('skip_prodcode', False):
                prod_code = True
        prod_supp_info = self.pool.get('product.supplierinfo')
        if context.get('pol', False) and context.get('partner_id', False):
            prod_supp_ids = prod_supp_info.search(cr, uid, [('name', '=', context['partner_id'])], context=context)
            IDS = [x.product_id.id for x in prod_supp_info.browse(cr, uid, prod_supp_ids, context=context)]
            args += [('product_tmpl_id.id', 'in', IDS)]

        if prod_code:
            new_args = args[:]
            for x in new_args:
                if x[0] == 'default_code':
                    dom1 = x
                    dom2 = ('cust_code', x[1], x[2])
                    prod_supp_ids = prod_supp_info.search(cr, uid, [('product_code', x[1], x[2])], context=context)
                    dom3_ids = [rec.product_id.id for rec in prod_supp_info.browse(cr, uid, prod_supp_ids, context=context)]
                    dom3 = ('product_tmpl_id.id', 'in', dom3_ids)
                    ctx = context.copy()
                    if 'pol' in ctx.keys():
                        del ctx['pol']
                    ctx.update({'skip_prodcode':True})
                    new_IDS = self.search(cr, uid, ['|', dom1, '|', dom2, dom3], context=ctx)
                    args[new_args.index(x)] = ('id', 'in', new_IDS)

        return super(product_product, self).search(cr, uid, args, offset, limit,
                order, context=context, count=count)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
