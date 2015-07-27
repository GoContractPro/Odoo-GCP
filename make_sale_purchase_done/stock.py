# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 NovaPoint Group LLC (<http://www.novapointgroup.com>)
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import netsvc

class Stock_picking(osv.Model):
    _inherit = 'stock.picking'
    
    def action_cancel(self, cr, uid, ids, context=None):
        """ Changes picking state to cancel along with cancelling the relevant procurements
        @return: True
        """
        wf_service = netsvc.LocalService("workflow")
        proc_obj = self.pool.get('procurement.order')
        res = super(Stock_picking, self).action_cancel(cr, uid, ids, context)
        for pick in self.browse(cr, uid, ids, context=context):
            proc_ids = []
            #Find relevant procurements
            if pick.type == 'out':
                for mov in pick.move_lines:
                    proc_ids += proc_obj.search(cr, uid, [('move_id', '=', mov.id)])
    
                for proc in proc_ids:
                    #Some proc are cancelled when run
                    wf_service.trg_validate(uid, 'procurement.order', proc, 'button_check', cr)
                    #Some have a cancel stage possible
                    wf_service.trg_validate(uid, 'procurement.order', proc, 'button_cancel', cr)
    
                if pick.sale_id:
                    #Ignore the shipping exception created due to proc removal
                    wf_service.trg_validate(uid, 'sale.order', pick.sale_id.id, 'ship_corrected', cr)
        return res 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
