# -*- coding: utf-8 -*-


from osv import osv, fields


class product_partner_related_fields(osv.osv):
    _name = "product.partner.related.fields"
    
    _columns = {
        "name": fields.char("Field name", size=30, required=True),
        "value": fields.char("Field value", size=255, required=True),
        "product_id": fields.many2one("product.product",
                                      "Product",
                                      required=True,
                                      ),
        "partner_id": fields.many2one("res.partner",
                                      "Partner",
                                      required=True,
                                      ),
                         
    }

product_partner_related_fields()
