# -*- coding: utf-8 -*-
import werkzeug

from openerp import SUPERUSER_ID
from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
import openerp.addons.website_sale.controllers.main

class website_sale(openerp.addons.website_sale.controllers.main.website_sale):
    
    #------------------------------------------------------
    # Payment
    #------------------------------------------------------

    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
    
        cr, uid, context = request.cr, request.uid, request.context
        payment_obj = request.registry.get('payment.acquirer')
        sale_order_obj = request.registry.get('sale.order')

        order = request.website.sale_get_order(context=context)
        carrier_id = post.get('carrier_id')
        if carrier_id:
            carrier_id = int(carrier_id)
        if order:
            request.registry['sale.order']._check_carrier_quotation(cr, uid, order, force_carrier_id=carrier_id, context=context)
            if carrier_id:
                return request.redirect("/shop/payment")
            
        redirection = self.checkout_redirection(order)
        if redirection:
            return redirection

        shipping_partner_id = False
        if order:
            if order.partner_shipping_id.id:
                shipping_partner_id = order.partner_shipping_id.id
            else:
                shipping_partner_id = order.partner_invoice_id.id
                
        currency_id = order and order.pricelist_id.currency_id.id or False
            
        values = {
            'website_sale_order': order
        }
        values['errors'] = sale_order_obj._get_errors(cr, uid, order, context=context)
        values.update(sale_order_obj._get_website_data(cr, uid, order, context))

        if not values['errors']:
            # find an already existing transaction
            tx = request.website.sale_get_transaction()
            acquirer_domain = ['&','|',('currency_id','=',currency_id),('currency_id','=',False),'&',('website_published', '=', True),('company_id', '=', order.company_id.id)]
            acquirer_ids = payment_obj.search(cr, SUPERUSER_ID, acquirer_domain, context=context)
            values['acquirers'] = list(payment_obj.browse(cr, uid, acquirer_ids, context=context))
            render_ctx = dict(context, submit_class='btn btn-primary', submit_txt=_('Pay Now'))
            for acquirer in values['acquirers']:
                acquirer.button = payment_obj.render(
                    cr, SUPERUSER_ID, acquirer.id,
                    tx and tx.reference or request.env['payment.transaction'].get_next_reference(order.name),
                    order.amount_total,
                    order.pricelist_id.currency_id.id,
                    values={
                        'return_url': '/shop/payment/validate',
                        'partner_id': shipping_partner_id,
                        'billing_partner_id': order.partner_invoice_id.id,
                    },
                    context=render_ctx)

        return request.website.render("website_sale.payment", values)