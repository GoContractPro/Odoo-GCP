# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
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
from openerp.report import report_sxw

class npg_po(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(npg_po, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_tax': self.get_tax,
            'get_bank_account' : self.get_bank_account,
            'get_inv_address': self.get_inv_address,
            'get_type': self.get_type
        })

    def get_inv_address(self, partner):
        Adrs = self.pool.get('res.partner').address_get(self.cr, self.uid, [partner], adr_pref=['invoice'])
        ADS = [self.pool.get('res.partner').browse(self.cr, self.uid, Adrs['invoice'])]
        return ADS

    def get_tax(self,line):
        return line and 'Y' or ''

    def get_bank_account(self,line):
        if not line:
            return ''
        for acc in line:
            return acc.acc_number or ''

    def get_type(self, state):
        if state == 'draft':
            return 'RFQ'
        elif state == 'approved':
            return 'PURCHASE ORDER'

report_sxw.report_sxw('report.npg.purchase.order', 'purchase.order', 'addons/npg_purchasing/report/purchase_order.rml', parser=npg_po, header="external")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: