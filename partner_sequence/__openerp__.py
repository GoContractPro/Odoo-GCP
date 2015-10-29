# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Novapoint Group INC (<http://novapointgroup.com>)
#              (C) 2014 ONESTEiN BV (<http://www.onestein.nl>).
#              (C) 2014 ICTSTUDIO (<http://www.ictstudio.eu>).
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
    'name': 'Partner sequence',
    'version': '1.0.1',
    'summary': """Generates unique identifiers for partners""",
    'category': 'Custom',
    'description': """
Partner sequence
===============================================

Adds extra sequence type: Partner and a sequence with code res.partner. As default this sequence will be
used to assign to partners. Sequence will start with first letter of Partner Name
The partner number will be added to the partner name .

(modified from  partner sequence module by INCONESTEiN BV)
""",
    'author': 'Novapoint Group Inc(Stephen Levenhagen, Ruby Chan), ',
    'website': 'http://novapointgroup.com',
    'depends': [
        'base',        
    ],
    'data': [
        'security/ir.model.access.csv',
        'partner_view.xml',
        'partner_sequence.xml',
    ],
    'installable': True,
    'application': True,
}
