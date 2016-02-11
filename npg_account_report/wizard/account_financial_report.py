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

class npg_accounting_report(osv.osv_memory):
    _inherit = "accounting.report"
 #   _inherit = "account.common.report"
    _description = "Accounting Report"

    _columns = {
        'comp_period': fields.boolean('Compare Period'),
    }

    def onchange_vals(self, cr, uid, ids, enable_filter,comp_period,fiscalyear_id,context={}):
        fiscalyear_id_cmp =False
        filter_by = False
        prd_col = ''
        period_from_cmp = False
        if enable_filter:
            prd_pool = self.pool.get('account.period')
            fiscalyear_id_cmp = fiscalyear_id
            filter_by = comp_period and 'filter_period'
            period_from_cmp = prd_pool.find(cr,uid,context=context)[0]
            prd_col = comp_period and 'Period ' + prd_pool.browse(cr,uid,period_from_cmp).name or ''
        return {'value':{'fiscalyear_id_cmp':fiscalyear_id_cmp,'filter_cmp':filter_by,'period_from_cmp':period_from_cmp,'period_to_cmp':period_from_cmp,'label_filter':prd_col}}
    
    def onchange_startp(self, cr, uid, ids, period_from_cmp,comp_period,context={}):
        prd_col = ''
        period_to_cmp = False
        if period_from_cmp and comp_period:
            period_to_cmp =period_from_cmp
            prd_pool = self.pool.get('account.period')
            prd_col = 'Period ' + prd_pool.browse(cr,uid,period_from_cmp).name
        return {'value':{'period_to_cmp':period_to_cmp,'label_filter':prd_col}}

    def _print_report(self, cr, uid, ids, data, context=None):
        data['form'].update(self.read(cr, uid, ids, ['date_from_cmp',  'debit_credit', 'date_to_cmp',  'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',  'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter','target_move'], context=context)[0])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'npg.account.financial.report',
            'datas': data,
        }

npg_accounting_report()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
