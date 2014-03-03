# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
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
from osv import osv, fields

class hr_employee(osv.osv):
    _name = "hr.employee"
    _description = "Employee"
    _inherit = "hr.employee"
    _columns = {
        'contact_name1': fields.char('Name', size=64),
        'contact_relationship1': fields.char('Relationship', size=32),
        'contact_address1': fields.char('Address', size=256),
        'contact_home_number1': fields.char('Home Number', size=32),
        'contact_cell_number1': fields.char('Cell Number', size=32),
        'contact_work_number1': fields.char('Work Number', size=32),
        'contact_employer1': fields.char('Employer', size=32),
        'contact_name2': fields.char('Name', size=64),
        'contact_relationship2': fields.char('Relationship', size=32),
        'contact_address2': fields.char('Address', size=256),
        'contact_home_number2': fields.char('Home Number', size=32),
        'contact_cell_number2': fields.char('Cell Number', size=32),
        'contact_work_number2': fields.char('Work Number', size=32),
        'contact_employer2': fields.char('Employer', size=32),
        'doctor_name': fields.char('Name', size=64),
        'physician_group': fields.char('Physician Group', size=32),
        'doctor_number': fields.char('Phone Number', size=32),
        'dentist_name': fields.char('Name', size=64),
        'dentist_group': fields.char('Dentist Group', size=32),
        'dentist_number': fields.char('Phone Number', size=32)
}

hr_employee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: