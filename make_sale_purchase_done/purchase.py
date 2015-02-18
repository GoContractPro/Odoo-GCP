from openerp.osv import osv

class purchase_order(osv.Model):
    _inherit = 'purchase.order'
    
    def is_done_do(self, cr, uid, ids, context=None):
        for rec in self.browse(cr, uid, ids, context=context):
            done_do = []
            for pick in rec.picking_ids:
                if pick.state == 'done':
                    done_do.append(pick.id)
            if done_do:
                return True
            return False
                