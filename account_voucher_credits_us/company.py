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

from openerp.osv import osv, fields

class res_company(osv.osv):
    """
    New field to keep the write-off account configuration on company
    This Write-off account will be used on Account voucher.
    """
    _inherit = 'res.company'
    _columns = {
        'def_supp_journal': fields.many2one('account.journal', 'Default Supplier Payment Method', readonly=False),
        'writeoff_account': fields.many2one('account.account', 'Writeoff Account', domain=[('type', '!=', 'view'), ('type', '!=', 'consolidation')],
                                            help="This is the designated write-off gl account that will be used when writing off remaining amounts\
                                             in customer payment."),
        }
    
res_company()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
