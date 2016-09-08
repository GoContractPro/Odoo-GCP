# -*- coding: utf-8 -*-

#See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, exceptions, _
from openerp.exceptions import UserError, RedirectWarning, ValidationError


class res_partner(models.Model):
    _inherit = 'res.partner'
    
#    payment_profile_id =  fields.Many2one('cust.profile', 'Payment Profile', help='Stores customers Authorize.net payment profiles id linked to remote payment saved information', )
    payment_profile_ids = fields.One2many('cust.payment.profile', 'partner_id', string='Profile Accounts', help='Customers Authorize.net payment profiles', )
    payment_cust_profile_ids = fields.One2many('cust.profile', 'partner_id', string='Profile Accounts', help='Customers Authorize.net customer profiles ', )
   
    
    @api.multi
    def get_partner_currency(self):
        currency = self.property_product_pricelist and self.property_product_pricelist.pricelist_id.currency_id.id
                
    
    def get_partner_pricelist_currency(self):
        
        currency_id = self.property_product_pricelist and self.property_product_pricelist.currency_id.id or None  
        if not currency_id:

            raise ValidationError(_('Please select a set price list for this Partner.'))
        return currency_id
    
    
    
    def get_authorize_aquirer(self, currency_id):
        
        res = self.env['payment.acquirer'].search([('provider','=','authorize'),('currency_id','=',currency_id)])
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
            
            createCustomerProfile = authorize_aquirer.getCreateCustomerProfile(partner)
          
            response = authorize_aquirer.getCreateCustomerProfileResponse(createCustomerProfile)
                    
            vals = {"partner_id":partner.id,
                    "name":response.customerProfileId,
                    "acquirer_id":authorize_aquirer.id  
                    }
 
            return self.env['cust.profile'].create(vals)
                    
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
        customer_profile = self.payment_cust_profile_ids.filtered(lambda r: r.acquirer_id == authorize_aquirer)
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
            customer_profile = partner.get_customer_profile_id(authorize_aquirer)
   
            createCustomerPaymentProfile = authorize_aquirer.getCreateCustomerPaymentProfile( creditCard, bankAccount, customer_profile.name)    

            response = authorize_aquirer.getCreateCustomerPaymentProfileResponse(createCustomerPaymentProfile)
            if creditCard:
                account_type = "cc"
                last4number = 'XXXX' + creditCard.cardNumber[-4:]
            if bankAccount:
                account_type = "bank"
                last4number = 'XXXX' + bankAccount.accountNumber[-4:]
                    
            if response and (response.messages.resultCode=="Ok"):
                vals = {'partner_id':partner.id,
                        'name':str(response.customerPaymentProfileId),
                        'description':str(description),
                        'last4number':str(last4number),
                        'account_type':account_type,
                        'cust_profile_id':customer_profile.id
                        }
                self.env['cust.payment.profile'].create(vals)
                print "Successfully created a customer payment profile with id: %s" % response.customerPaymentProfileId
                return
            else:
                raise ValidationError(_("Failed to create customer payment profile %s" % response.messages.message[0].text))
 
 
        
    def read_customer_payment_profile(self, payment_profile_id,currency_id=None):
        res = {}
        for partner in self:
            if not currency_id:
                currency_id = partner.get_partner_pricelist_currency()
              
            authorize_aquirer = partner.get_authorize_aquirer(currency_id)
            customer_profile = partner.get_customer_profile_id(authorize_aquirer)
   
            getCustomerPaymentProfile = authorize_aquirer.getCustomerPaymentProfileInfo(customer_profile.name, payment_profile_id.name)

            response = authorize_aquirer.getCustomerPaymentProfileInfoResponse(getCustomerPaymentProfile)
            
            if response and (response.messages.resultCode=="Ok"):
                print("Successfully retrieved a payment profile with profile id %s and customer id %s" % (getCustomerPaymentProfile.customerProfileId, getCustomerPaymentProfile.customerProfileId))
                if hasattr(response, 'paymentProfile') == True:
                    if hasattr(response.paymentProfile, 'payment') == True:
                        if hasattr(response.paymentProfile.payment, 'creditCard') == True:
                            res['cardNumber'] = response.paymentProfile.payment.creditCard.cardNumber
                            res['expirationDate'] = response.paymentProfile.payment.creditCard.expirationDate
                            if hasattr(response.paymentProfile.payment.creditCard, 'cardCode'):
                                res['cardCode'] = response.paymentProfile.payment.creditCard.cardCode
                                
                        if hasattr(response.paymentProfile.payment, 'bankAccount') == True:
                            res['accountNumber'] = response.paymentProfile.payment.bankAccount.accountNumber
                            res['accountType'] = response.paymentProfile.payment.bankAccount.accountType
                            res['routingNumber'] = response.paymentProfile.payment.bankAccount.routingNumber
                            res['bankName'] = response.paymentProfile.payment.bankAccount.bankName
                            res['echeckType'] = response.paymentProfile.payment.bankAccount.echeckType
            else:
                print("response code: %s" % response.messages.resultCode)
                print("Failed to get payment profile information with id %s" % getCustomerPaymentProfile.customerPaymentProfileId)
        return res

    def update_customer_payment_profile(self, payment_profile_id, values={},currency_id=None):
        for partner in self:
            if not currency_id:
                currency_id = partner.get_partner_pricelist_currency()
              
            authorize_aquirer = partner.get_authorize_aquirer(currency_id)
            customer_profile = partner.get_customer_profile_id(authorize_aquirer)
   
            getCustomerPaymentProfile = authorize_aquirer.updateCustomerPaymentProfile(customer_profile.name, payment_profile_id.name,values)

            response = authorize_aquirer.updateCustomerPaymentProfileResponse(getCustomerPaymentProfile)
            
            if response and (response.messages.resultCode=="Ok"):
                print ("Successfully updated customer payment profile with id %s" % payment_profile_id.name)
                vals = {'partner_id':partner.id,
                        'last4number':'XXXX' + str(values.get('cardNumber') or values.get('acc_number') or '')[-4:],
                        'description':str(values.get('desc','')),
                        }
                payment_profile_id.write(vals)
            else:
                print (response.messages.message[0]['text'].text)
                raise ValidationError(_("Failed to update customer with customer payment profile id %s : %s" % (payment_profile_id.name, response.messages.message[0]['text'].text)))
        return

    def delete_customer_payment_profile(self, payment_profile_id,currency_id=None):
        for partner in self:
            if not currency_id:
                currency_id = partner.get_partner_pricelist_currency()
            authorize_aquirer = partner.get_authorize_aquirer(currency_id)
            customer_profile = partner.get_customer_profile_id(authorize_aquirer)
   
            response = authorize_aquirer.delete_customer_payment_profile(customer_profile.name, payment_profile_id.name)    
            
            if response and (response.messages.resultCode=="Ok"):
                payment_profile_id.unlink()
        return
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
    
 
