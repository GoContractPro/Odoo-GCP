# -*- coding: utf-8 -*-

#See LICENSE file for full copyright and licensing details.

from openerp import models, fields, api, exceptions, _
import logging 

_logger = logging.getLogger(__name__)
#try
from authorizenet import apicontractsv1
from authorizenet.apicontrollers import *
'''except:
    
    _logger.info("Authorize.net Python Library  not available. Please install using 'pip install authorizenet'"  )
''' 


class create_payment_profile(models.TransientModel):
    _name = 'create.payment.profile'
    _description = 'Create Payment Profile'

    @api.model
    def _get_partner(self):
       
        part = False
        if self.env.context.get('active_model','') == 'res.partner':
            part = self.env.context.get('active_id', False)
        elif self.env.context.get('active_model','') == 'account.voucher':
            part = self.env['account.voucher'].browse(self.env.context.get('active_id',False)).partner_id.id
        return part
            

    
    cc_number = fields.Char('Credit Card Number', size=16, )
    cc_ed_month = fields.Char('Expiration Date MM', size=2, )
    cc_ed_year = fields.Char('Expiration Date YYYY', size=4 , required=True)
    cc_verify_code = fields.Char('Card Code Verification', size=3)
    partner_id = fields.Many2one('res.partner', 'Customer', default=_get_partner)
    address_id = fields.Many2one('res.partner', 'Address')
    description = fields.Char('Optional Name', size=128)
    cc_card_type = fields.Selection([('Discovery','Discovery'),
                                      ('AMEX','AMEX'),
                                      ('MasterCard','MasterCard'),
                                      ('Visa','Visa')],'Credit Card Type', default='Visa')
    bank_account = fields.Char('Bank Account', size=16, )
    bank_routing = fields.Char('ABA Bank Routing', size=9, )
    bank_name = fields.Char('Bank Name', size=64, )
    bank_account_type = fields.Selection([('personal','Personal Checking'),
                                          ('business','Business Checking'),
                                          ('saving','Personal Savings')],
                                          'Bank Account Type', default='personal')
    account_type = fields.Selection([('cc','Credit Card'),('bank','Banking Account'),],
                                     string='Account Type', default='cc')


    @api.multi
    def create_payment_profile(self):
        
        creditCard=None
        bankAccount=None
        if self.account_type == 'cc': 
            creditCard = apicontractsv1.creditCardType()
            creditCard.cardNumber = self.cc_number
            creditCard.expirationDate = ("%s-%s") % (self.cc_ed_month, self.cc_ed_year)

        if self.account_type == 'bank':
            bankAccount = apicontractsv1.bankAccountType()
            bankAccount.accountType = self.bank_account_type
            bankAccount.accountNumber = self.bank_account
            bankAccount.routingNumber = self.bank_routing
            bankAccount.bankName = self.bank_name
                
        self.partner_id.create_customer_payment_profile(creditCard=creditCard,bankAccount=bankAccount,description=self.description)
    
    
    




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
