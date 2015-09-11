# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.novapointgroup.com>)
#    Copyright (C) 2004-2010 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp.osv import fields, osv
import httplib
from xml.dom.minidom import Document
import xml2dic
from openerp.tools.translate import _

class edit_payment_profile(osv.TransientModel):
    _name = 'edit.payment.profile'
    _description = 'Edit Payment Profile'

    def _get_partner(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('active_id', False)

    def _get_state(self, cr, uid, context=None):
        if context.get('active_model', False) == 'cust.payment.profile':
                return 'preprocessing'
        return 'draft'

    def _get_profile_id(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context['active_model'] == 'cust.payment.profile':
            return context.get('active_id')
        return None

    _columns = {
        'payment_profile_id':fields.many2one('cust.payment.profile', 'Payment Profile', required=True),
        'partner_id':fields.many2one('res.partner', 'Customer', required=True),
        'cc_number':fields.char('Credit Card Number', size=32),
        'cc_ed_month':fields.char('Expiration Date MM', size=32),
        'cc_ed_year':fields.char('Expiration Date YYYY', size=32),
        'cc_code':fields.char('Card Code', size=32),
        'state':fields.selection(
            [('draft', 'Draft'),
             ('done', 'Done'),
             ('processing', 'Processing'),
             ('preprocessing', 'PreProcessing'),
            ], 'State', readonly=True, size=32),
                
        'first_name':fields.char('FirstName', size=256),
        'last_name':fields.char('LastName', size=256),
        'address':fields.char('Address', size=256),
        'city':fields.char('City', size=256),
        'add_state':fields.char('State', size=256),
        'zip':fields.char('Zip', size=256),
        'country':fields.char('Country', size=256),
        'phone_number':fields.char('Phone Number', size=256),
        'fax_number':fields.char('Fax Number', size=256),
        'company':fields.char('Company', size=256),
            
    }

    _defaults = {
        'partner_id': _get_partner,
        'state':_get_state,
#         'payment_profile_id':_get_profile_id
        }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(edit_payment_profile, self).default_get(cr, uid, fields, context=context)
        
        customerPaymentProfileId = False
        if context['active_model'] == 'cust.payment.profile':
            customerPaymentProfileId = context.get('active_id')
        if customerPaymentProfileId:
            customerPaymentProfileId = self.pool.get('cust.payment.profile').browse(cr,uid,customerPaymentProfileId,context).name
        existing_profile = self.get_payment_profile_info(cr, uid, customerPaymentProfileId=customerPaymentProfileId, context=context)

        if 'payment_profile_id' in fields:
            res.update({'payment_profile_id': context.get('active_id')})
        if 'cc_ed_month' in fields:
            res.update({'cc_number': existing_profile.get('cc_number',False)})
        if 'cc_ed_month' in fields:
            res.update({'cc_ed_month': existing_profile.get('cc_ed_month',False)})
        if 'cc_ed_year' in fields:
            res.update({'cc_ed_year': existing_profile.get('cc_ed_year',False)})
        if 'cc_code' in fields:
            res.update({'cc_code': existing_profile.get('cc_code',False)})
        if 'state' in fields:
            res.update({'state': existing_profile.get('state',False)})
        if 'first_name' in fields:
            res.update({'first_name': existing_profile.get('first_name',False)})
        if 'last_name' in fields:
            res.update({'last_name': existing_profile.get('last_name',False)})
        if 'fax_number' in fields:
            res.update({'fax_number': existing_profile.get('fax_number',False)})
        if 'phone_number' in fields:
            res.update({'phone_number': existing_profile.get('phone_number',False)})
        if 'country' in fields:
            res.update({'country': existing_profile.get('country',False)})
        if 'address' in fields:
            res.update({'address': existing_profile.get('address',False)})
        if 'city' in fields:
            res.update({'city': existing_profile.get('city',False)})
        if 'add_state' in fields:
            res.update({'add_state': existing_profile.get('add_state',False)})
        if 'zip' in fields:
            res.update({'zip': existing_profile.get('zip',False)})
        if 'company' in fields:
            res.update({'company': existing_profile.get('company',False)})
            
        return res
    
    def getCustomerPaymentProfileRequest(self, dic):
            profile_dictionary = dic
            KEYS = dic.keys()
            Payment_Profile_Details = {}

            doc1 = Document()
            url_path = dic.get('url_extension')
            url = dic.get('url')
            xsd = dic.get('xsd')

            getCustomerPaymentProfileRequest = doc1.createElement("getCustomerPaymentProfileRequest")
            getCustomerPaymentProfileRequest.setAttribute("xmlns", xsd)
            doc1.appendChild(getCustomerPaymentProfileRequest)

            merchantAuthentication = doc1.createElement("merchantAuthentication")
            getCustomerPaymentProfileRequest.appendChild(merchantAuthentication)

            name = doc1.createElement("name")
            merchantAuthentication.appendChild(name)

            transactionKey = doc1.createElement("transactionKey")
            merchantAuthentication.appendChild(transactionKey)

            ##Create the Request for creating the customer profile
            if 'api_login_id' in KEYS and 'transaction_key' in KEYS:

                ptext1 = doc1.createTextNode(self._clean_string(dic['api_login_id']))
                name.appendChild(ptext1)

                ptext = doc1.createTextNode(self._clean_string(self._clean_string(dic['transaction_key'])))
                transactionKey.appendChild(ptext)

            customerProfileId = doc1.createElement("customerProfileId")
            getCustomerPaymentProfileRequest.appendChild(customerProfileId)
            ptext = doc1.createTextNode(self._clean_string(self._clean_string(dic['customerProfileId'])))
            customerProfileId.appendChild(ptext)

            customerPaymentProfileId = doc1.createElement("customerPaymentProfileId")
            getCustomerPaymentProfileRequest.appendChild(customerPaymentProfileId)
            ptext = doc1.createTextNode(self._clean_string(self._clean_string(dic['customerPaymentProfileId'])))
            customerPaymentProfileId.appendChild(ptext)

            Request_string = xml = doc1.toxml(encoding="utf-8")
            get_transaction_response_xml = self.request_to_server(Request_string, url, url_path)
            get_PaymentProfile_response_dictionary = xml2dic.main(get_transaction_response_xml)

            parent_card_number = self.search_dic(get_PaymentProfile_response_dictionary, 'cardNumber')
            parent_exp_date = self.search_dic(get_PaymentProfile_response_dictionary, 'expirationDate')
            
            first_name = self.search_dic(get_PaymentProfile_response_dictionary, 'firstName')
            last_name = self.search_dic(get_PaymentProfile_response_dictionary, 'lastName')
            company = self.search_dic(get_PaymentProfile_response_dictionary, 'company')
            address = self.search_dic(get_PaymentProfile_response_dictionary, 'address')
            city = self.search_dic(get_PaymentProfile_response_dictionary, 'city')
            add_state = self.search_dic(get_PaymentProfile_response_dictionary, 'state')
            zip = self.search_dic(get_PaymentProfile_response_dictionary, 'zip')
            country = self.search_dic(get_PaymentProfile_response_dictionary, 'country')
            phone_number = self.search_dic(get_PaymentProfile_response_dictionary, 'phoneNumber')
            fax_number = self.search_dic(get_PaymentProfile_response_dictionary, 'faxNumber')
            
            if first_name and first_name.get('firstName'):
                Payment_Profile_Details['first_name'] = first_name['firstName']
            if last_name and last_name.get('lastName'):
                Payment_Profile_Details['last_name'] = last_name['lastName']
            if company and company.get('company'):
                Payment_Profile_Details['company'] = company['company']
            if address and address.get('address'):
                Payment_Profile_Details['address'] = address['address']
            if city and city.get('city'):
                Payment_Profile_Details['city'] = city['city']
            if add_state and add_state.get('state'):
                Payment_Profile_Details['add_state'] = add_state['state']
            if zip and zip.get('zip'):
                Payment_Profile_Details['zip'] = zip['zip']
            if country and country.get('country'):
                Payment_Profile_Details['country'] = country['country']
            if phone_number and phone_number.get('phoneNumber'):
                Payment_Profile_Details['phone_number'] = phone_number['phoneNumber']
            if fax_number and fax_number.get('faxNumber'):
                Payment_Profile_Details['fax_number'] = fax_number['faxNumber']
            
            if parent_card_number and parent_card_number.get('cardNumber'):
                Payment_Profile_Details['cc_number'] = parent_card_number['cardNumber']

            if parent_exp_date and parent_exp_date.get('expirationDate'):
                Payment_Profile_Details['cc_ed_year'] = parent_exp_date['expirationDate']

            if parent_exp_date and parent_exp_date.get('cardCode'):
                Payment_Profile_Details['cardCode'] = parent_exp_date['cardCode']
            return Payment_Profile_Details

    def request_to_server(self, Request_string, url, url_path):
            ''' Sends a POST request to url and returns the response from the server'''

            conn = httplib.HTTPSConnection(url)
            conn.putrequest('POST', url_path)
            conn.putheader('content-type', 'text/xml')
            conn.putheader('content-length', len(Request_string))
            conn.endheaders()
            conn.send(Request_string)
            response = conn.getresponse()
            create_CustomerProfile_response_xml = response.read()
            return create_CustomerProfile_response_xml

    def search_dic(self, dic, key):
        ''' Returns the parent dictionary containing key None on Faliure'''
        if key in dic.keys():
            return dic
        for k in dic.keys():
            if type(dic[k]) == type([]):
                for i in dic[k]:
                    if type(i) == type({}):
                        ret = self.search_dic(i, key)
                        if ret and key in ret.keys():
                           return ret
        return None

    def _clean_string(self, text):
        lis = ['\t', '\n']
        if type(text) != type(''):
            text = str(text)
        for t in lis:
            text = text.replace(t, '')
        return text

    def _setparameter(self, dic, key, value):
        ''' Used to input parameters to corresponding dictionary'''
        if key == None or value == None :
            return
        if type(value) == type(''):
            dic[key] = value.strip()
        else:
            dic[key] = value

    def get_payment_profile_info(self, cr, uid, customerPaymentProfileId='', context=None):
        Param_Dic = {}
        parent_model = context.get('active_model')
        parent_id = context.get('active_id')
#         data = self.browse(cr, uid, ids[0])
        if parent_model == 'res.partner':
            partner = self.pool.get(parent_model).browse(cr, uid, parent_id)
        else:
            parent_model_obj = self.pool.get(parent_model).browse(cr, uid, parent_id)
            partner = parent_model_obj.partner_id

#         customerPaymentProfileId = data.payment_profile_id.name

        Customer_Profile_ID = partner.payment_profile_id.name

        Trans_key = partner.company_id.auth_config_id.transaction_key
        Login_id = partner.company_id.auth_config_id.login_id
        url_extension = partner.company_id.auth_config_id.url_extension
        xsd = partner.company_id.auth_config_id.xsd_link
        if partner.company_id.auth_config_id.test_mode:
            url = partner.company_id.auth_config_id.url_test
        else:
            url = partner.company_id.auth_config_id.url

        if Trans_key and Login_id:
                self._setparameter(Param_Dic, 'api_login_id', Login_id)
                self._setparameter(Param_Dic, 'transaction_key', Trans_key)

                if url:
                    self._setparameter(Param_Dic, 'url', url)
                    self._setparameter(Param_Dic, 'url_extension', url_extension)
                if xsd:
                    self._setparameter(Param_Dic, 'xsd', xsd)

                self._setparameter(Param_Dic, 'customerProfileId', Customer_Profile_ID)
                self._setparameter(Param_Dic, 'customerPaymentProfileId', customerPaymentProfileId)


        existing_profile = self.getCustomerPaymentProfileRequest(Param_Dic)
        existing_profile['state'] = 'processing'
        return existing_profile
#         self.write(cr, uid, ids, existing_profile)
#         return True
#         mod, modid = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_payment_cim_authdotnet', 'edit_payment_profile_form_view')
#         return {
#             'name':_("Edit Payment Profile"),
#             'view_mode': 'form',
#             'view_id': modid,
#             'view_type': 'form',
#             'res_model': 'edit.payment.profile',
#             'type': 'ir.actions.act_window',
#             'target':'new',
#             'nodestroy': True,
#             'domain': '[]',
#             'res_id': ids[0],
#             'context':context,
#         }

    def updateCustomerPaymentProfile(self, dic):
        KEYS = dic.keys()
        doc1 = Document()
        url_path = dic['url_extension']
        url = dic['url']
        xsd = dic['xsd']

        updateCustomerPaymentProfileResponse = doc1.createElement("updateCustomerPaymentProfileRequest")
        updateCustomerPaymentProfileResponse.setAttribute("xmlns", xsd)
        doc1.appendChild(updateCustomerPaymentProfileResponse)

        merchantAuthentication = doc1.createElement("merchantAuthentication")
        updateCustomerPaymentProfileResponse.appendChild(merchantAuthentication)

        name = doc1.createElement("name")
        merchantAuthentication.appendChild(name)

        transactionKey = doc1.createElement("transactionKey")
        merchantAuthentication.appendChild(transactionKey)

        ##Create the Request for creating the customer profile
        if 'api_login_id' in KEYS and 'transaction_key' in KEYS:

            ptext1 = doc1.createTextNode(self._clean_string(dic['api_login_id']))
            name.appendChild(ptext1)

            ptext = doc1.createTextNode(self._clean_string(self._clean_string(dic['transaction_key'])))
            transactionKey.appendChild(ptext)

        if 'customerProfileId' in KEYS:
            customerProfileId = doc1.createElement("customerProfileId")
            updateCustomerPaymentProfileResponse.appendChild(customerProfileId)
            ptext = doc1.createTextNode(self._clean_string(dic['customerProfileId']))
            customerProfileId.appendChild(ptext)

            paymentProfile = doc1.createElement("paymentProfile")
            updateCustomerPaymentProfileResponse.appendChild(paymentProfile)
            if 'customerType' in KEYS:
                    customerType = doc1.createElement("customerType")
                    paymentProfile.appendChild(customerType)

            billTo = doc1.createElement("billTo")
            paymentProfile.appendChild(billTo)
            if 'firstName' in KEYS:
                firstName = doc1.createElement("firstName")
                billTo.appendChild(firstName)
                ptext = doc1.createTextNode(self._clean_string(dic['firstName']))
                firstName.appendChild(ptext)

            if 'lastName' in KEYS:
                lastName = doc1.createElement("lastName")
                billTo.appendChild(lastName)
                ptext = doc1.createTextNode(self._clean_string(dic['lastName']))
                lastName.appendChild(ptext)

            if 'company' in KEYS:
                company = doc1.createElement("company")
                billTo.appendChild(company)
                ptext = doc1.createTextNode(self._clean_string(dic['company']))
                company.appendChild(ptext)

            if 'address' in KEYS:
                address = doc1.createElement("address")
                billTo.appendChild(address)
                ptext = doc1.createTextNode(self._clean_string(dic['address']))
                address.appendChild(ptext)

            if 'city' in KEYS:
                city = doc1.createElement("city")
                billTo.appendChild(city)
                ptext = doc1.createTextNode(self._clean_string(dic['city']))
                city.appendChild(ptext)
                
                ##State code must be given here
            if 'state' in KEYS:
                state = doc1.createElement("state")
                billTo.appendChild(state)
                ptext = doc1.createTextNode(self._clean_string(dic['state']))
                state.appendChild(ptext)


            if 'zip' in KEYS:
                zip = doc1.createElement("zip")
                billTo.appendChild(zip)
                ptext = doc1.createTextNode(self._clean_string(dic['zip']))
                zip.appendChild(ptext)

            if 'country' in KEYS:
                country = doc1.createElement("country")
                billTo.appendChild(country)
                ptext = doc1.createTextNode(self._clean_string(dic['country']))
                country.appendChild(ptext)

            if 'phoneNumber' in KEYS:
                phoneNumber = doc1.createElement("phoneNumber")
                billTo.appendChild(phoneNumber)
                ptext = doc1.createTextNode(self._clean_string(dic['phoneNumber']))
                phoneNumber.appendChild(ptext)

            if 'faxNumber' in KEYS:
                faxNumber = doc1.createElement("faxNumber")
                billTo.appendChild(faxNumber)
                ptext = doc1.createTextNode(self._clean_string(dic['faxNumber']))
                faxNumber.appendChild(ptext)

            payment = doc1.createElement("payment")
            paymentProfile.appendChild(payment)

            if 'cardNumber' in KEYS and 'expirationDate' in  KEYS:
                creditCard = doc1.createElement("creditCard")
                payment.appendChild(creditCard)

                cardNumber = doc1.createElement("cardNumber")
                creditCard.appendChild(cardNumber)
                ptext = doc1.createTextNode(self._clean_string(dic['cardNumber']))
                cardNumber.appendChild(ptext)

                expirationDate = doc1.createElement("expirationDate")
                creditCard.appendChild(expirationDate)
                ptext = doc1.createTextNode(dic['expirationDate'])
                expirationDate.appendChild(ptext)

                if 'cardCode' in KEYS:
                                cardCode = doc1.createElement("cardCode")
                                creditCard.appendChild(cardCode)
                                ptext = doc1.createTextNode(self._clean_string(dic['cardCode']))
                                cardCode .appendChild(ptext)

            customerPaymentProfileId = doc1.createElement("customerPaymentProfileId")
            paymentProfile.appendChild(customerPaymentProfileId)
            ptext = doc1.createTextNode(self._clean_string(dic['customerPaymentProfileId']))
            customerPaymentProfileId .appendChild(ptext)

            if 'validationMode' in KEYS:
                validationMode = doc1.createElement("validationMode")
                updateCustomerPaymentProfileResponse.appendChild(validationMode)
            Request_string = doc1.toxml(encoding="utf-8")
            update_CustomerPaymentProfile_response_xml = self.request_to_server(Request_string, url, url_path)
            update_CustomerPaymentProfile_response_dictionary = xml2dic.main(update_CustomerPaymentProfile_response_xml)
            parent_resultCode = self.search_dic(update_CustomerPaymentProfile_response_dictionary, 'resultCode')
            if parent_resultCode:
                if  parent_resultCode['resultCode'] == 'Ok':
                    return True
                else:
                    ret = {}
                    Error_Code_dic = self.search_dic(update_CustomerPaymentProfile_response_dictionary, 'code')
                    if Error_Code_dic.get('code'):
                        ret['Error_Code'] = Error_Code_dic['code']
                    Error_message_dic = self.search_dic(update_CustomerPaymentProfile_response_dictionary, 'text')
                    if  Error_message_dic.get('text'):
                        ret['Error_Message'] = Error_message_dic['text']
                    return ret
        return

    def update_payment_profile_info(self, cr, uid, ids, context=None):
        Param_Dic = {}
        parent_model = context.get('active_model')
        parent_id = context.get('active_id')
        data = self.browse(cr, uid, ids[0])
        if parent_model == 'res.partner':
            partner = self.pool.get(parent_model).browse(cr, uid, parent_id)
        else:
            parent_model_obj = self.pool.get(parent_model).browse(cr, uid, parent_id)
            partner = parent_model_obj.address_id

        cardNumber = data.cc_number or ''
        expirationDate = ''
        if data.cc_ed_year and data.cc_ed_month:
            expirationDate = data.cc_ed_year + '-' + data.cc_ed_month
        cardCode = data.cc_code or ''

        Trans_key = partner.company_id.auth_config_id.transaction_key
        Login_id = partner.company_id.auth_config_id.login_id
        url_extension = partner.company_id.auth_config_id.url_extension
        xsd = partner.company_id.auth_config_id.xsd_link
        prof_id = partner.payment_profile_id.name
        customerPaymentProfileId = data.payment_profile_id.name

        if partner.company_id.auth_config_id.test_mode:
            url = partner.company_id.auth_config_id.url_test
        else:
            url = partner.company_id.auth_config_id.url

        if Trans_key and Login_id:
            self._setparameter(Param_Dic, 'api_login_id', Login_id)
            self._setparameter(Param_Dic, 'transaction_key', Trans_key)

            if url:
                self._setparameter(Param_Dic, 'url', url)
                self._setparameter(Param_Dic, 'url_extension', url_extension)
            if xsd:
                self._setparameter(Param_Dic, 'xsd', xsd)

            self._setparameter(Param_Dic, 'cardNumber', cardNumber)
            self._setparameter(Param_Dic, 'expirationDate', expirationDate)
            if cardCode:
                self._setparameter(Param_Dic, 'cardCode', cardCode)
            self._setparameter(Param_Dic, 'customerProfileId', prof_id)
            self._setparameter(Param_Dic, 'customerPaymentProfileId', customerPaymentProfileId)
            
#             Update address details

            self._setparameter(Param_Dic, 'firstName', data.first_name or '')
            self._setparameter(Param_Dic, 'lastName', data.last_name or '')
            self._setparameter(Param_Dic, 'company', data.company or '')
            self._setparameter(Param_Dic, 'state', data.add_state or '')
            self._setparameter(Param_Dic, 'address', data.address or '')
            self._setparameter(Param_Dic, 'zip', data.zip or '')
            self._setparameter(Param_Dic, 'city', data.city or '')
            self._setparameter(Param_Dic, 'country', data.country or '')
            self._setparameter(Param_Dic, 'phoneNumber', data.phone_number or '')
            self._setparameter(Param_Dic, 'faxNumber', data.fax_number or '')

            Customer_Payment_Profile_ID = self.updateCustomerPaymentProfile(Param_Dic)
            if not Customer_Payment_Profile_ID or type(Customer_Payment_Profile_ID) == type({}):
                raise osv.except_osv(_('Transaction Error'), _('Error code : ' + Customer_Payment_Profile_ID.get('Error_Message') or '' + '\nError Message :' + Customer_Payment_Profile_ID.get('Error_Message') or ''))

        return{}
