# -*- coding: utf-8 -*-
import datetime

from openerp import http
from openerp.exceptions import AccessError
from openerp.http import request

from openerp.addons.website_portal_sale.controllers.main import website_account
from authorizenet import apicontractsv1
from openerp.tools.translate import _

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
    
#     @http.route(['/my/profile/cim_profile'], type='http', auth="user", website=True)
#     def cim_profile(self, **kw):
#         acquirers = list(request.env['payment.acquirer'].search([('website_published', '=', True), ('registration_view_template_id', '!=', False)]))
#         partner = request.env.user.partner_id
#         profile = {}
#         values = {
#                   'error': {},
#                   'profile':profile
#                   }
#         return request.website.render("payment_authorize_aim_cim.cim_profile", values)
    
    @http.route(['/my/profile/delete_profile/'], type='http', auth="user", website=True)
    def delete_profile(self, profile='', **kw):
#         acquirers = list(request.env['payment.acquirer'].search([('website_published', '=', True), ('registration_view_template_id', '!=', False)]))
        partner = request.env.user.partner_id
        profile = request.env['cust.payment.profile'].search([('name', '=', profile)])
        ret = False
        if profile: 
            partner.delete_customer_payment_profile(profile)
            ret = request.redirect('/my/home')
        else:
            ret = request.website.render("payment_authorize_aim_cim.not_delete_profile")
        values = {
                  'error': {},
                  'profile':profile
                  }
        return ret
    
    def details_form_validate(self, data):
        error = dict()
        error_message = []

        mandatory_billing_fields = ["cc_number", "exp_mm", "exp_yyyy"]

        # Validation
        for field_name in mandatory_billing_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # card validation
        if data.get('cc_number'):
            cc_number = data.get('cc_number')
            err = False
            try:
                int(cc_number)
            except: 
                err = True
            if not len(cc_number) == 16:
                err = True
            if err:
                error["cc_number"] = 'error'
                error_message.append(_('Invalid Card Number! Please enter a valid 16 digits Card Number.'))
                
        # Date validation
        
        if data.get('exp_mm'):
            exp_mm = data.get('exp_mm')
            err = False
            try:
                int(exp_mm)
            except: 
                err = True
            if not err and not (int(exp_mm) > 0 and int(exp_mm) <=12):
                err = True
            if err:
                error["exp_mm"] = 'error'
                error_message.append(_('Invalid Month! Please enter a valid value(01 to 12).'))
                
        if data.get('exp_yyyy'):
            exp_yyyy = data.get('exp_yyyy')
            err = False
            try:
                int(exp_yyyy)
            except: 
                err = True
            if not err  and not (int(exp_yyyy) > 2000 and int(exp_yyyy) <=2100):
                err = True
            if err:
                error["exp_yyyy"] = 'error'
                error_message.append(_('Invalid Year! Please enter a valid year.'))
        
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        return error, error_message

    
    @http.route(['/my/profile/cim_profile'], type='http', auth="user", website=True)
    def cim_profile(self,reference='',redirect=None, **post):
#         acquirers = list(request.env['payment.acquirer'].search([('website_published', '=', True), ('registration_view_template_id', '!=', False)]))
        partner = request.env.user.partner_id
        profile = {'profile_name':False}
        values = {
                  'error': {},
                  'profile':profile,
                  'error_message': [],
                  
                  }
        
        if reference:
            profileobj = request.env['cust.payment.profile'].search([('name', '=', reference)])
            ret = False
            if profileobj:
                values['profile'].update({
                                          'cc_number':profileobj.last4number or '',
                                          'desc':profileobj.description or '',
                                          'profile_name':profileobj.name
                                          })
        if post:
            error, error_message = self.details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values['profile'].update(post)
            if not error:
                month = str(post.get("exp_mm",''))
                if len(month) == 1:
                    month = '0' + month
                try:
                    if post.get('profile_name'):
                        profileobj = request.env['cust.payment.profile'].search([('name', '=', post.get('profile_name',''))])
                        partner.update_customer_payment_profile(profileobj,{
                                                                            'cardNumber' : post.get("cc_number"),
                        'expirationDate' : ("%s-%s") % (month, str(post.get("exp_yyyy",''))), 'desc' : str(post.get("desc",''))
                                                                            })
                    else:
                        creditCard = apicontractsv1.creditCardType()
                        creditCard.cardNumber = post.get("cc_number")
                        creditCard.expirationDate = ("%s-%s") % (month, str(post.get("exp_yyyy",'')))
                        partner.create_customer_payment_profile(creditCard=creditCard,bankAccount=None,description=str(post.get("desc",'')))
                except Exception as e:
                    exp = "Some Error occurred!!"
                    if e.name:
                        exp = e.name 
                    values.update({'error_message': [exp]})
                    return request.website.render("payment_authorize_aim_cim.cim_profile", values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')
            
        return request.website.render("payment_authorize_aim_cim.cim_profile", values)
    
    
    def bank_details_form_validate(self, data):
        error = dict()
        error_message = []

        mandatory_billing_fields = ["bank_name", "acc_number", "bank_routing", "echeckType"]

        # Validation
        for field_name in mandatory_billing_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'

        # Acc validation
#         if data.get('acc_number'):
#             acc_number = data.get('acc_number')
#             try:
#                 int(acc_number)
#             except: 
#                 error["acc_number"] = 'error'
#                 error_message.append(_('Invalid Card Number! Please enter a valid 16 digits Card Number.'))
                
        if data.get('bank_routing'):
            bank_routing = data.get('bank_routing')
            
            err = False
            try:
                int(bank_routing)
            except: 
                err = True
            if not len(bank_routing) == 9:
                err = True
            if err:
                error["bank_routing"] = 'error'
                error_message.append(_('Invalid Routing Number! Please enter a valid 9 digits Routing Number.'))
                
        # Date validation
        
        
        if [err for err in error.values() if err == 'missing']:
            error_message.append(_('Some required fields are empty.'))

        return error, error_message
    
    @http.route(['/my/profile/bank_profile'], type='http', auth="user", website=True)
    def bank_profile(self,reference='',redirect=None, **post):
        partner = request.env.user.partner_id
        profile = {'profile_name':False,'bank_account_type':'checking'}
        values = {
                  'error': {},
                  'profile':profile,
                  'error_message': [],
                  
                  }
        
        if reference:
            profileobj = request.env['cust.payment.profile'].search([('name', '=', reference)])
            ret = False
            if profileobj:
                values['profile'].update({
                                          'acc_number':profileobj.last4number or '',
                                          'desc':profileobj.description or '',
                                          'profile_name':profileobj.name,
#                                           'bank_account_type' : profileobj.bank_account_type
                                          })
        if post:
            error, error_message = self.bank_details_form_validate(post)
            values.update({'error': error, 'error_message': error_message})
            values['profile'].update(post)
            if not error:
                try:
                    if post.get('profile_name'):
                        profileobj = request.env['cust.payment.profile'].search([('name', '=', post.get('profile_name',''))])
                        partner.update_customer_payment_profile(profileobj,{
                                            'bank_account_type' : post.get("bank_account_type"),
                                            'acc_number' : post.get("acc_number"), 
                                            'desc' : str(post.get("desc",'')),
                                            'bank_routing' : post.get("bank_routing"),
                                            'bank_name' : post.get("bank_name"),
                                            'partner_name' : partner.name,
                                            'echeckType' : post.get("echeckType"),
                                             'update_bank' : True   })
                    else:
                        bankAccount = apicontractsv1.bankAccountType()
                        bankAccount.accountType = post.get("bank_account_type") or 'checking'#self.bank_account_type
                        bankAccount.accountNumber = post.get("acc_number")
                        bankAccount.routingNumber = post.get("bank_routing")
                        bankAccount.bankName = post.get("bank_name")
                        bankAccount.echeckType = post.get("echeckType")
                        bankAccount.nameOnAccount = partner.name
                        partner.create_customer_payment_profile(creditCard=None,bankAccount=bankAccount,description=str(post.get("desc",'')))
                except Exception as e:
                    exp = "Some Error occurred!!"
                    if e.name:
                        exp = e.name 
                    values.update({'error_message': [exp]})
                    return request.website.render("payment_authorize_aim_cim.bank_profile", values)
                if redirect:
                    return request.redirect(redirect)
                return request.redirect('/my/home')
            
        return request.website.render("payment_authorize_aim_cim.bank_profile", values)
    
