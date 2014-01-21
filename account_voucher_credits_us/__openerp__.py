# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
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
    "name": "Voucher modifications for US",
    "version": "1.24",
    "author": 'NovaPoint Group LLC',
    "description": """
    This module will add new functionality to better manage credits and how and when they apply to Sales Payments. 
    The result of this development will enable users to designate which credit(s) will apply to each individual invoice, and how much of an individual credit amount to apply.
    """,
    "category": "US Localisation/Account",
    "website": "http://www.novapointgroup.com/",
    "depends": ["account_payment_creditcard"],
    "demo": [],
    "data": [
#         "voucher_view.xml",
        "company_view.xml",
        "wizard/account_post_voucher.xml",
#         "security/ir.model.access.csv"
        ],
    "test": [],
    'auto_install': False,
    "installable": True,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
