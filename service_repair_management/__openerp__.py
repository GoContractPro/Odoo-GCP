#################################################################################################
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#    (Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
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
    'name' : 'Service Repair Management.',
    'version' : '1.1',
    'author' : 'Novapoint Group',
    'category' : 'Fleet',
    'description' : """
Service Repair Management.
====================================

    """,
    'website': 'http://www.novapointgroup.com',
    'depends' : ['fleet', 'sale_mrp_project_link', 'mrp_project_link', 'purchase_mrp_project_link', 
                 'mrp_sale_ficticious','project','sale','project_issue','project_timesheet','hr_timesheet_invoice',
                 'sale_order_dates','sale_service'],
    'data': [
             'views/sequence_view.xml',
        'views/service_repair_view.xml',
        'views/fleet_view.xml',
        'views/partner_view.xml',
        'views/menu_view.xml',
        'views/sale_order_view.xml'
    ],
    'qweb' : [
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
