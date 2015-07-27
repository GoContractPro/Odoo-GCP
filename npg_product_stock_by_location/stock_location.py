from openerp.osv import osv


class stock_location(osv.osv):
    _name = "stock.location"
    _inherit = "stock.location"

    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        if context is None:
            context = {}

        res_ids = super(stock_location, self).search(cr, uid, args, offset, limit, order, context=context, count=count)
        if context.get('only_with_stock', False) is True:
            loc_obj = self.browse(cr, uid, res_ids, context=context)
            res_ids = [x.id for x in loc_obj if x.stock_real<>0 or x.stock_virtual<>0]

        return res_ids


stock_location()