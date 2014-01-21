# -*- coding: utf-8 -*-

from osv import osv, fields

class product_partner_related_fields_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
    
    _columns = {
        "partner_related_ids": fields.one2many("product.partner.related.fields", "product_id", "Related partner information"),
    }
       
product_partner_related_fields_product()
