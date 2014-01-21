# -*- coding: utf-8 -*-

from osv import osv, fields

class product_partner_related_fields_partner(osv.osv):
    _name = "res.partner"
    _inherit = "res.partner"
    
    _columns = {
        "product_related_ids": fields.one2many("product.partner.related.fields", "partner_id", "Related product information"),
    }
product_partner_related_fields_partner()
