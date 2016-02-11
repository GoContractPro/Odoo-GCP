# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Verts Services India Pvt. Ltd. (<http://www.verts.co.in>)
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
from openerp.report import report_sxw


class invoice_npg_custom_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(invoice_npg_custom_report, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_order_date':self._get_order_date,
        })
        
    def _get_order_date(self, order_ref):
        """
        Method to fetch the date of SO confirmation.
        @param self : The Object pointer
        @param order_ref : The SO ref e.g. SO0048
        @return the SO confirmation date
        """
        sale_obj = self.pool.get('sale.order')
        sale_ids = sale_obj.search(self.cr, self.uid, [('name', '=', order_ref)])
        if not sale_ids:
            return ' '
        sale_order = sale_obj.browse(self.cr, self.uid, sale_ids[0])
        return sale_order.date_confirm or ' '
report_sxw.report_sxw(
    'report.npg.custom.account.invoice',
    'account.invoice',
    'addons/npg_account_report/report/invoice_npg_custom_report.rml',
    parser=invoice_npg_custom_report
)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: