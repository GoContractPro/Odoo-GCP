# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 GoContractPro LLC (<https://gocontractpro.com>)
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
    'name': ' ',
    'version': '1.0',
    'category': '',
    'complexity': "easy",
    'category': 'Generic Modules/Others',
    'description': """
    
    """,
    'author': 'GoContractPro LLC',
    'website': 'www.gocontractpro.com',
    'depends': ['mail'],
    'init_xml': [],
    'data': [
             "views/mail_reply.xml"
        ],
    'demo_xml': [],
    'test': [],
    'qweb' : ["static/src/xml/thread.xml"],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
