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
    'name': 'Disassemble the products to sub products based on BoM',
    'version': '1.11',
    'category': 'Generic Modules/Production',
    'description': """
        This module allows you to reverse the manufacturing process in OpenERP.  When a product has a bill of materials that defines it components, with mrp_disassemble, a user can go into the Product page and reverse the manufacturing process to gain the product's components.  It handles all of the stock moves for the user, and completes the manufacturing order without a necessary process.  There is an addition to the recepition of goods into the warehouse that allows users to disassemble all of the products that have been purchased.  Sometimes known as dekitting.

                Use case: company orders a fully assembled bicycle from a supplier. They break the item down and sell the parts individually.
    """,
    'author': 'NovaPoint Group LLC',
    'website': 'http://www.novapointgroup.com/',
    'depends': ['base', 'mrp'],
    'init_xml': [],
    'update_xml': [

       'security/ir.model.access.csv',
       'wizard/product_disassemble_view.xml',
       'mrp_view.xml',
    ],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

