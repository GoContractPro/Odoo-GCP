# -*- coding: utf-'8' "-*-"



from openerp import api, fields, models, _

from authorizenet import constants
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *


_logger = logging.getLogger(__name__)


class PaymentAcquirerAuthorize(models.Model):
    _inherit = 'payment.acquirer'

    @api.multi 
    def set_merchantAuth(self,):
        
        for authorize_aquirer in self:     
            merchantAuth = apicontractsv1.merchantAuthenticationType()
            merchantAuth.name = authorize_aquirer.authorize_login
            merchantAuth.transactionKey = authorize_aquirer.authorize_transaction_key
            return merchantAuth
        
    @api.multi   
    def set_environment(self, controller):
        
        if self.environment == 'prod':
            controller.setenvironment(constants.PRODUCTION)
        elif self.environment == 'test':
            controller.setenvironment(constants.SANDBOX)
        
        return controller
    
    @api.multi
    def getCreateCustomerPaymentProfile(self, creditCard, bankAccount, customer_profile_id):
            
            
        payment = apicontractsv1.paymentType()
        
        if creditCard:
            payment.creditCard = creditCard
        if bankAccount:
            payment.bankAccount = bankAccount
            
        
        profile = apicontractsv1.customerPaymentProfileType()
        profile.payment = payment
        
        createCustomerPaymentProfile = apicontractsv1.createCustomerPaymentProfileRequest()
        createCustomerPaymentProfile.merchantAuthentication = self.set_merchantAuth()
        createCustomerPaymentProfile.paymentProfile = profile
        createCustomerPaymentProfile.customerProfileId = customer_profile_id
        
        return createCustomerPaymentProfile

    @api.multi
    def getCreateCustomerPaymentProfileResponse(self,createCustomerPaymentProfile):
        
        controller = createCustomerPaymentProfileController(createCustomerPaymentProfile)
        self.set_environment(controller)    
        controller.execute()
            
        return controller.getresponse()
    
    @api.multi
    def getCreateCustomerProfile(self, partner):
        
        createCustomerProfile = apicontractsv1.createCustomerProfileRequest()
        createCustomerProfile.merchantAuthentication = self.set_merchantAuth()
        profile = apicontractsv1.customerProfileType
        profile.email = partner.email
        profile.description = partner.name
        profile.merchantCustomerId = str(partner.id).zfill(10)
        
        createCustomerProfile.profile = profile
        return createCustomerProfile
    
    @api.multi
    def getCreateCustomerProfileResponse(self, createCustomerProfile):
        
 
        controller = createCustomerProfileController(createCustomerProfile)
        self.set_environment(controller)
        controller.execute()
        
        return controller.getresponse()
    
    @api.multi
    def getShippingAddressRequest(self,address,profile_id):
        
        
        # Give address details
        officeAddress = apicontractsv1.customerAddressType();
        if address.iscompany
        officeAddress.firstName =  address.name.split(" ",1)[0]
        officeAddress.lastName = address.name.split(" ",1)[1]
        officeAddress.address = address.street
        officeAddress.city = address.city
        officeAddress.state = address.state_id.code
        officeAddress.zip = address.zip
        officeAddress.country = address.country_id.code
        officeAddress.phoneNumber = address.phone_number
        
        # Create shipping address request
        shippingAddressRequest = apicontractsv1.createCustomerShippingAddressRequest();
        shippingAddressRequest.address = officeAddress
        shippingAddressRequest.customerProfileId = profile_id
        shippingAddressRequest.merchantAuthentication = self.set_merchantAuth()

        return shippingAddressRequest
    
    
    @api.multi
    def getCreateShippingAddressResponse(self,shippingAddressRequest ):
    
        controller= createCustomerShippingAddressController(shippingAddressRequest)
        self.set_environment(controller)
        controller.execute()
        
        return createCustomerShippingAddressController.getresponse();

        