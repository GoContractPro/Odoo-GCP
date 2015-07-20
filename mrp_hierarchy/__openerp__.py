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
    'name': 'Manufacturing Sequence Module',
    'version': '1.0',
    'category': '',
    "sequence": 14,
    'complexity': "easy",
    'category': 'Generic Modules/Others',
    'description': """
Establish Tiered Naming convention for Mfg Orders.
==================================================

This module will help the manufacturing team to easily identify
all the associated sub-assembly manufacturing orders for a particular
order by creating parent-child relationship between orders and
modifying the naming convention.
""",
    'author': 'Novapoint Group Inc.',
    'website': 'http://novapointgroup.com/',
    'depends': ["base","mrp"],
    'init_xml': [],
    'data': [
        "mrp_hierarchy_view.xml",
        "npg_mrp_mo_seq_view.xml",
    ],
    'demo_xml': [],
    'test': [
    ],
    'qweb' : [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: