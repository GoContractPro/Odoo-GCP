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
{
    'name': 'NPG batch payment Inhancement',
    'category': 'Generic Modules/Accounting',
    'description': """ Make the field name 'apply_credit' invisible in the form view,
                         """,
    'author': 'Novapoint Group LLC',
    'website': 'www.novapointgroup.com',
    'depends': ['batch_payment_invoices'],
    'data': ['npg_batch_payment_view.xml',
            ],
    'test': [],
    'installable': True,
    'auto_install': False,
}