# -*- coding: utf-8 -*- 
######################################################################
# 
# OpenERP, Open Source Management Solution 
# Copyright (C) 2011 OpenERP s.a. (<http://openerp.com>). 
# Copyright © 2013 INIT Tech Co., Ltd (http://init.vn). 
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU Affero General Public License as 
# published by the Free Software Foundation, either version 3 of the 
# License, or (at your option) any later version. 
# 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the 
# GNU Affero General Public License for more details. 
# 
# You should have received a copy of the GNU Affero General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>. 
# 
######################################################################

{
    'name': 'Multi Pay Invoices and Check Writing',
    'category': 'Generic Modules/Accounting',
    'description': """ Create a new menu with:
        Name = “Multi Pay Invoices”
        It's position is after Supplier Invoices menu
        When click in this menu
            We will show list of supplier invoices
            We can edit supplier's info in this list view (editable=top)
            Show column “Amount Paid” in this list view; place the column before Status column
        Add new one option (Pay) to More button (we click on More button, to choose some options such as: Delete, Duplicate …)
        When choose some invoices and click on Pay button in More, we like to show a wizard with some following information
        With 2 buttons: Pay and Cancel
        When click on button Pay, we like to: pay for each above invoice.
        And 
        "Module for the Check Writing and Check Printing"
        ===============================================
     """,
    'author': 'Novapoint Group LLC',
    'website': 'www.novapointgroup.com',
    'depends': ['account_check_writing','account_cancel'],
    'data': [
         'security/ir.model.access.csv',
         'security/security.xml',
         'multi_pay_invoices_view.xml',
         'account_voucher_view.xml',
         'wizard/pay_invoices_view.xml',
         'wizard/account_check_batch_printing_view.xml',
         'report/report_sample.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
}