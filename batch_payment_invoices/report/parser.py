##############################################################################
#
# Copyright (c) 2008-2011 Alistek Ltd (http://www.alistek.com) All Rights Reserved.
#                    General contacts <info@alistek.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from report import report_sxw
from report.report_sxw import rml_parse
import lorem
import random

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'lorem':lorem.do_lorem,
            'random':random,
            'hello_world':self.hello_world,
            '_get_partner':self._get_partner,
            '_get_invoice':self._get_invoice,
        })

    def hello_world(self, name):
        return "Hello, %s!" % name    
    
    #get list partner in invoice selected
    def _get_partner(self, object):
        res_partner = self.pool.get('res.partner')
        result = []
        list_partner = []
        for o in object:
            list_partner.append(o.partner_id.id)
        list_partner = list(set(list_partner))
        for partner in res_partner.browse(self.cr, self.uid, list_partner):
            result.append({'partner_name': partner.name,
                           'partner_id': partner.id,
                           })            
        return result
    
    # get invoice in invoice with supplier
    def _get_invoice(self, object,partner_id):
        res_partner = self.pool.get('res.partner')
        account_invoice = self.pool.get('account.invoice')
        result = []
        list_invoice = []
        for o in object:
            if o.partner_id.id == partner_id:
                list_invoice.append(o.id)
        for invoice in account_invoice.browse(self.cr, self.uid, list_invoice):
            result.append({'internal_number': invoice.internal_number or '',
                           'date_invoice': invoice.date_invoice or '',
                           'number': invoice.number or '',
                           'user_id': invoice.user_id and invoice.user_id.name or '',
                           'date_due': invoice.date_due or '',
                           'origin': invoice.origin or '',
                           'currency_id': invoice.currency_id and invoice.currency_id.name or '',
                           'residual': invoice.residual or '',
                           'state': invoice.state or '',
                           'amount_untaxed': invoice.amount_untaxed or '',
                           'amount_total': invoice.amount_total or '',
                           })                
            
        return result    
