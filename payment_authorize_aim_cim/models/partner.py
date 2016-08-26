# -*- coding: utf-8 -*-

#See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, exceptions, _

from openerp.exceptions import UserError, RedirectWarning, ValidationError

import imp
import logging 

#_logger = logging.getLogger(__name__)

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *
    
#_logger.info("Authorize.net Python Library  not available. Please install using 'pip install authorizenet'"  )
    

class res_partner(models.Model):
    _inherit = 'res.partner'
    
#    payment_profile_id =  fields.Many2one('cust.profile', 'Payment Profile', help='Stores customers Authorize.net payment profiles id linked to remote payment saved information', )
    payment_profile_ids = fields.One2many('cust.payment.profile', 'partner_id', string='Profile Accounts', help='Customers Authorize.net payment profiles', )
    payment_cust_profile_ids = fields.One2many('cust.profile', 'partner_id', string='Profile Accounts', help='Customers Authorize.net customer profiles ', )
   
    
    @api.multi
    def get_partner_currency(self):
        currency = self.property_product_pricelist and self.property_product_pricelist.pricelist_id.currency_id.id
                
    
    def get_partner_pricelist_currency(self):
        
        currency_id = self.price_list and self.price_list.currency_id.id or None  
        if not currency_id:

            raise ValidationError(_('Please select a set price list for this Partner.'))
        return currency_id
    
    
    
    def get_authorize_aquirer(self, currency_id):
        
        res = self.env['payment.acquirer'].search([('provider','=','authorize'),('currency','=',currency_id)])
        for aquirer in res:
            return aquirer
        
        #No Aquirer
        currency = self.env['res.currency'].browse(currency_id)
        if currency and currency.name  in ['USD','CAD']:
            raise ValidationError(_('Please Configure an Authorize.net payment Gateway for (%s)') % currency.name )
        else:
            raise ValidationError(_('Authorize.net payments require to be US or Canadian Currency. Partner should have price list with either USD or Canadian Dollars.'))


##############################################################             
#CRUD section for Customer Profile on AutHorize.net data store   
    
    @api.multi
    def create_customer_profile(self, authorize_aquirer):
    
        for partner in self:
            
            createCustomerProfile = authorize_aquirer.getcreateCustomerProfile(partner)
          
            response = authorize_aquirer.getCreateCustomerProfileResponse(createCustomerProfile)
        
            if (response.messages.resultCode=="Ok"):
                vals = {"partner_id":partner.id,
                        "name":response.cust_profile_id,  
                        }
 
                return self.env['cust.profile'].create(vals)
                
            else:
                raise ValidationError(_("Failed to create customer payment profile %s" % response.messages.message[0]['text'].text))
    
    @api.multi
    def read_customer_profile(self):
        #TODO add create supporting code in authorize.py
        pass
    @api.multi    
    def update_customer_profile(self):
        #TODO add create supporting code in authorize.py
        pass
    @api.multi
    def delete_customer_profile(self):
        #TODO add create supporting code in authorize.py
        pass 
    
       
########################################################################    
# CRUD section for Customer Payments Profiles on AutHorize.net data store     
    
    
    @api.multi
    def get_customer_profile_id(self,authorize_aquirer):
    # find exisiting profile Id saved in Odoo for partner or create new
        customer_profile = self.payment_cust_profile_ids.filtered(lambda r: r.aquirer_id == authorize_aquirer.id)
        if customer_profile:
            return customer_profile
        else:
            return  self.create_customer_profile(authorize_aquirer)
            
        
    @api.multi
    def create_customer_payment_profile(self, creditCard, bankAccount, description, currency_id=None):
        
        
        for partner in self:
            
            if not currency_id:
                currency_id = partner.get_partner_pricelist_currency()
              
            authorize_aquirer = partner.get_authorize_aquirer(currency_id)
            customer_profile_id = partner.get_customer_profile_id(authorize_aquirer)
   
            createCustomerPaymentProfile = authorize_aquirer.getCreateCustomerPaymentProfile( creditCard, bankAccount, customer_profile_id)    

            response = authorize_aquirer.getCreateCustomerPaymentProfileControllerResponse(createCustomerPaymentProfile)
            if creditCard:
                account_type = "cc"
                last4number = creditCard.cardNumber[-4:]
            if bankAccount:
                account_type = "bank"
                last4number = bankAccount.accountNumber[-4:]
                    
            if  (response.messages.resultCode=="Ok"):
                vals = {'partner_id':partner.id,
                        'name':response.payment_id,
                        'description':description,
                        'last4number':last4number,
                        'account_type':account_type
                        }
                self.env['cust.payment.profile'].create(vals)
                print "Successfully created a customer payment profile with id: %s" % response.customerPaymentProfileId
                return
            else:
                raise ValidationError(_("Failed to create customer payment profile %s" % response.messages.message[0].text))
 
 
        
    def read_customer_payment_profile(self):
        #TODO add create supporting code in authorize.py
        pass

    def update_customer_payment_profile(self):
        #TODO add create supporting code in authorize.py
        pass

    def delete_customer_payment_profile(self):
        #TODO add create supporting code in authorize.py
        pass
 
##########################################################################################    
# CRUD section for Customer Payments Profiles  Billing address on AutHorize.net data store    
# Each above payment profile should have a coresponding billing address matching payees Account address
    
    def create_customer_payment_profile_billing_address(self):
    # TODO add create supporting code in authorize.py
        pass      
    def read_customer_payment_profile_billing_address(self):
    # TODO add create supporting code in authorize.py
        pass
       
    def update_customer_payment_profile_billing_address(self):
    # TODO add create supporting code in authorize.py
        pass
    def delete_customer_payment_profile_billing_address(self):
    # TODO add create supporting code in authorize.py
        pass
    
##########################################################################################    
# CRUD section for Customer shipping address on AutHorize.net data store    
            
    # Each payment profile should have a coresponding billing address matching payees Account address
    def create_customer_profile_shipping_address(self):
    # TODO add create supporting code in authorize.py
        pass      
    def read_customer_profile_shipping_address(self):
    # TODO add create supporting code in authorize.py
        pass
       
    def update_customer_profile_shipping_address(self):
    # TODO add create supporting code in authorize.py
        pass
    def delete_customer_profile_shipping_address(self):
    # TODO add create supporting code in authorize.py
        pass
    
 
