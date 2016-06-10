# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.


{
    'name': 'Enhanced Invoicing Project Task ',
    'version': '1.0',
    'category': 'Project Management',
    'description': """
        Enhancement to Sale_service to allow linking additional tasks time sheet entries to Sale Order Lines.
        Allows to invoice tasks created from project to SO lines.
        Adds Date Ranges Invoicing time sheet from Sale Orders .
    """,
    'website': 'https://gocontractpro.com',
    'author': 'Stephen Levenhagen GoContractPro.com',
    'depends': ['project', 'sale', 'sale_service', 'project_timesheet', 'sale_timesheet'],
    'data': ['views/sale_task_invoicing_view.xml',
             'wizard/sale_make_invoice.xml',
             'views/project_task_view.xml',],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'qweb' : [],
    'price' : 100.00,
    'application': True,
}
    