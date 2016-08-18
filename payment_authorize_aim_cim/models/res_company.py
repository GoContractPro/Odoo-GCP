# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.verts.co.in>)
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


from openerp.osv import osv, fields

class res_company(osv.Model):
    _inherit = "res.company"
    _columns = {
        'auth_config_id':fields.many2one('auth.config', 'Auth Configuration'),
        'cc_login': fields.char('CreditCard Login ID', size=64),
        'cc_transaction_key': fields.char('Transaction Key', size=64),
        'cc_testmode': fields.boolean('Test Mode'),
        'cc_journal_id':fields.many2one('account.journal', 'Payment Method', help="The default payment method on payment voucher open using the Pay button from sale order."),

    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
