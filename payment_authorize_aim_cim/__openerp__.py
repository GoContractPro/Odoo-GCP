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


{
    'name': 'CreditCard Payment',
    'version': '2.0',
    'category': 'Generic Modules/Others',
    'description': """
    Module for Credit card payment using authorise.net
    """,
    'author': 'Verts Service Pvt Ltd.',
    'website': ' http://www.verts.co.in',
    'depends': ['sale_stock','sale', 'account_voucher', 'stock',
        'website_portal','website_portal_sale',
        'website_payment',],
    'data': [
        'wizard/account_post_voucher.xml',
        'wizard/create_payment_profile_view.xml',
        'wizard/delete_payment_profile_view.xml',
        'wizard/edit_payment_profile_view.xml',
        'wizard/make_transaction_view.xml',
        'views/account_journal_view.xml',
        'views/cim_transaction_view.xml',
        'views/company_view.xml',
        'views/invoice_view.xml',
        'views/partner_view.xml',
        'views/res_partner_bank_view.xml',
        'views/sale_stock_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_view.xml',
        'views/templates.xml',
        'views/account_voucher.xml',
        'security/account_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'test':[
            'test/ccapi_authdotnet.yml',
            'test/account_payment_cim_authdotnet.yml'
            'test/account_payment_creditcard.yml'
            ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
