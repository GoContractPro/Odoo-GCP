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
    'name': 'Import Data',
    'version': '1.0',
    'category': 'Import',
    'description': """
    This module adds enhanced Tools to create and save Data Maps  to import or update records from csv files.
    """,
    'author': 'NovaPoint Group LLC, Stephen Levenhagen',
    'website': ' http://www.novapointgroup.com',
    'depends': ['npg_warning','account','base_external_dbsource'],
    'data': ['view/import_data_header_view.xml',
#             'view/import_m2o_data_view.xml',
             'view/import_data_view.xml',
             'wizard/wiz_import_dbf_directory.xml',
             'security/security.xml',
             'security/ir.model.access.csv',
             'view/menus.xml',
             'view/ir_cron_view.xml',
            ],
    'demo': [],
    'auto_install': False,
    'installable': True,
    'qweb' : [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: