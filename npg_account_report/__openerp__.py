# -*- coding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Verts Services India Pvt. Ltd. (<http://www.verts.co.in>)
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    "name" : "Modifications to Financial and Invoice Report and Wizard Enhancement",
    "version" : "1.0",
    "author" : "Verts Team",
    "description" : """Modifications to Financial Report and Wizard Enhancement""",
    "website"  : "http://www.verts.co.in",
    "depends"  : ["base",'account','sale','sale_stock','purchase'],
    "category" : "Generic Modules",
    "init_xml" : [],
    "demo_xml" : [],
    "data"     : [
                 'wizard/account_financial_report_view.xml',
                 'npg_account_report_view.xml',
                 'security/ir.model.access.csv',
                 'report.xml'
                 ],
    'test': [],    
    'installable': True,
    'active': False,
    'certificate': '',
}
