# -*- coding: utf-8 -*-
import datetime

from openerp import http
from openerp.exceptions import AccessError
from openerp.http import request

from openerp.addons.website_portal_sale.controllers.main import website_account


class website_account(website_account):
    @http.route(['/my/home'], type='http', auth="user", website=True)
    def account(self, **kw):
        """ Add sales documents to main account page """
        response = super(website_account, self).account()
        partner = request.env.user.partner_id

        response.qcontext.update({
            'payment_profiles': partner.payment_profile_ids,
        })
        return response
    
    @http.route(['/my/profile/cim_profile'], type='http', auth="user", website=True)
    def cim_profile(self, **kw):
        acquirers = list(request.env['payment.acquirer'].search([('website_published', '=', True), ('registration_view_template_id', '!=', False)]))
        partner = request.env.user.partner_id
        profile = {}
        values = {
                  'error': {},
                  'profile':profile
                  }
        return request.website.render("payment_authorize_aim_cim.cim_profile", values)
    
    @http.route(['/my/profile/delete_profile/'], type='http', auth="user", website=True)
    def delete_profile(self, profile='', **kw):
#         acquirers = list(request.env['payment.acquirer'].search([('website_published', '=', True), ('registration_view_template_id', '!=', False)]))
        partner = request.env.user.partner_id
        profile = request.env['cust.payment.profile'].search([('name', '=', profile)])
        ret = False
        if profile: 
            partner.delete_customer_payment_profile(profile)
            ret = request.website.render("payment_authorize_aim_cim.delete_profile")
        else:
            ret = request.website.render("payment_authorize_aim_cim.not_delete_profile")
        values = {
                  'error': {},
                  'profile':profile
                  }
        return ret
    
    
    
    
    
    