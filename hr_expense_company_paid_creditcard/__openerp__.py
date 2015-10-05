# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group INC (<http://www.novapointgroup.com>)
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
    'name': 'Expense Tracker using Corporate Credit Cards',
    'version': '1.0',
    'category': 'Human Resources',
    'complexity': "easy",
    'category': 'Generic Modules/Others',
    'description': """
Employee expenses paid using Corporate Credit Cards.
====================================================
This module adds additional functionality to address the expenses paid by the Company using Corporate Credit Cards.
Companies provide their employees with credit cards to make purchases for in-house projects or for customer project on-site visits.
    """,
    'author': 'NovaPoint Group Inc.',
    'website': 'www.novapointgroup.com',
    'depends': ['hr', 'account_accountant', 'hr_expense'],
    'init_xml': [],
    'data': [
        "views/hr_expense_view.xml",
        ],
    'demo_xml': [],
    'test': [],
    'qweb' : [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
