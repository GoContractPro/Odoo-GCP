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


from osv import fields,osv
from xml.dom.minidom import Document
from tools.translate import _
import httplib
import xml2dic
import time
import datetime
from urlparse import urlparse
from PIL import Image
import tempfile
import re

from mako.template import Template
from mako import exceptions
import netsvc
import base64
import logging
import tools

from base64 import b64decode
import binascii


class logistic_company(osv.osv):
    _inherit="logistic.company"
    def _get_company_code(self, cr, user, context=None):
        res =  super(logistic_company, self)._get_company_code(cr, user, context=context)
        res.append(('fedex', 'Fedex'))
        
        return res
    _columns = {
                    'fedex_account_id' : fields.many2one('fedex.account','FedEx Account'),
                    
                    'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, required=True, size=64),
                    
                    'fedex_key'     : fields.related('fedex_account_id','fedex_key', size=64, type='char', string='FedEx Key'),
                    'fedex_password'     : fields.related('fedex_account_id','fedex_password', size=128, type='char', string='Password'),
                    'fedex_account_number'     : fields.related('fedex_account_id','fedex_account_number', size=64, type='char', string='Account Number'),
                    'fedex_meter_number'     : fields.related('fedex_account_id','fedex_meter_number', size=64, type='char', string='Meter Number'),
                    
#                    'fedex_key'     : fields.char('Fedex Key', size=64),
#                    'fedex_password': fields.char('Password', size=128),
#                    'fedex_account_number'  : fields.char('Account Number', size=64),
#                    'fedex_meter_number'    : fields.char('Meter Number', size=64),
                    
                    #URLS & Ports
#                    
#                    'fedex_url_address_validation' : fields.char('URL Addr Validation', size=256,),
#                    'fedex_port_address_validation' : fields.char('Port Addr Validation', size=8),
#                    
#                    'fedex_url_test_address_validation' :fields.char('Test URL Addr Validation', size=256),
#                    'fedex_port_test_address_validation' :fields.char('Test Port Addr Validation', size=8),
#                    
#                    'fedex_url_close' : fields.char('URL Close', size=256),
#                    'fedex_port_close' : fields.char('Port Close', size=8),
#                    
#                    'fedex_url_test_close' :fields.char('Test URL Close', size=256),
#                    'fedex_port_test_close' :fields.char('Port URL Close', size=8),
#                    
#                    'fedex_url_courier_dispatch' : fields.char('URL Courier Dispatch', size=256),
#                    'fedex_port_courier_dispatch' : fields.char('Port Courier Dispatch', size=8),
#                    
#                    'fedex_url_test_courier_dispatch' :fields.char('Test URL Courier Dispatch', size=256),
#                    'fedex_port_test_courier_dispatch' :fields.char('Test Port Courier Dispatch', size=8),
#                    
#                    'fedex_url_package' : fields.char('URL Package Info', size=256),
#                    'fedex_port_package' : fields.char('Port Package Info', size=8),
#                    
#                    'fedex_url_test_package' :fields.char('Test URL Package Info', size=256),
#                    'fedex_port_test_package' :fields.char('Test Port Package Info', size=8),
#                    
#                    'fedex_url_rate' : fields.char('URL Rate', size=256),
#                    'fedex_port_rate' : fields.char('Port Rate', size=8),
#                    
#                    'fedex_url_test_rate' :fields.char('Test URL Rate', size=256),
#                    'fedex_port_test_rate' :fields.char('Test Port Rate', size=8),
#                    
#                    'fedex_url_return_tag' : fields.char('URL Return Tag', size=256),
#                    'fedex_port_return_tag' : fields.char('Port Return Tag', size=8),
#                    
#                    'fedex_url_test_return_tag' :fields.char('Test URL Return Tag', size=256),
#                    'fedex_port_test_return_tag' :fields.char('Test Port Return Tag', size=8),
#                    
#                    'fedex_url_ship' : fields.char('URL Ship', size=256),
#                    'fedex_port_ship' : fields.char('Port Ship', size=8),
#                    
#                    
#                    'fedex_url_test_ship' :fields.char('Test URL Ship', size=256),
#                    'fedex_port_test_ship' :fields.char('Test Port Ship', size=8),
#                    
#                    'fedex_url_track' : fields.char('URL Track', size=256),
#                    'fedex_port_track' : fields.char('Port Track', size=8),
#                    
#                    'fedex_url_test_track' :fields.char('Test URL Track', size=256),
#                    'fedex_port_test_track' :fields.char('Test Port Track', size=8),
                      
                
                }
    
    def onchange_fedex_account(self, cr, uid, ids, fedex_account_id=False, context={}):
        res = {
                'fedex_key' : '',
                'fedex_password'    : '',
                'fedex_account_number'  : '',
                'fedex_meter_number'    : '',
                'test_mode'    :True
               }
        if fedex_account_id:
            fedex_account = self.pool.get('fedex.account').browse(cr, uid,fedex_account_id, context=context )
            res['fedex_key'] = fedex_account.fedex_key
            res['fedex_password'] = fedex_account.fedex_password
            res['fedex_account_number'] = fedex_account.fedex_account_number
            res['fedex_meter_number'] = fedex_account.fedex_meter_number
            res['test_mode'] = fedex_account.test_mode
        
        return {'value': res}

logistic_company()


class stock_picking(osv.osv):


    _inherit = "stock.picking"
    def _get_company_code(self, cr, user, context=None):
        res =  super(stock_picking, self)._get_company_code(cr, user, context=context)
        res.append(('fedex', 'Fedex'))
        
        return res
    _columns = {
                    'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True,  size=64),
                    'fedex_dropoff_type' : fields.selection([
                            ('REGULAR_PICKUP','REGULAR PICKUP'),
                            ('REQUEST_COURIER','REQUEST COURIER'),
                            ('DROP_BOX','DROP BOX'),
                            ('BUSINESS_SERVICE_CENTER','BUSINESS SERVICE CENTER'),
                            ('STATION','STATION'),
                        ],'Dropoff Type'),
                    'fedex_service_type' : fields.selection([
                            ('EUROPE_FIRST_INTERNATIONAL_PRIORITY','EUROPE_FIRST_INTERNATIONAL_PRIORITY'),
                            ('FEDEX_1_DAY_FREIGHT','FEDEX_1_DAY_FREIGHT'),
                            ('FEDEX_2_DAY','FEDEX_2_DAY'),
                            ('FEDEX_2_DAY_FREIGHT','FEDEX_2_DAY_FREIGHT'),
                            ('FEDEX_3_DAY_FREIGHT','FEDEX_3_DAY_FREIGHT'),
                            ('FEDEX_EXPRESS_SAVER','FEDEX_EXPRESS_SAVER'),
                            ('STANDARD_OVERNIGHT','STANDARD_OVERNIGHT'),
                            ('PRIORITY_OVERNIGHT','PRIORITY_OVERNIGHT'),
                            ('FEDEX_GROUND','FEDEX_GROUND'),
                       ],'Service Type'),
                    'fedex_packaging_type' : fields.selection([
                            ('FEDEX_BOX','FEDEX BOX'),
                            ('FEDEX_PAK','FEDEX PAK'),
                            ('FEDEX_TUBE','FEDEX_TUBE'),
                            ('YOUR_PACKAGING','YOUR_PACKAGING'),
                        ],'Packaging Type', help="What kind of package this will be shipped in"),
                    'fedex_package_detail' : fields.selection([
                            ('INDIVIDUAL_PACKAGES','INDIVIDUAL_PACKAGES'),
                            ('PACKAGE_GROUPS','PACKAGE_GROUPS'),
                            ('PACKAGE_SUMMARY','PACKAGE_SUMMARY'),
                        ],'Package Detail'),
                    'fedex_payment_type' : fields.selection([
                            ('RECIPIENT','RECIPIENT'),
                            ('SENDER','SENDER'),
                            ('THIRD_PARTY','THIRD_PARTY'),
                        ],'Payment Type', help="Who pays for the rate_request?"),
                    'fedex_physical_packaging' : fields.selection([
                            ('BAG','BAG'),
                            ('BARREL','BARREL'),
                            ('BOX','BOX'),
                            ('BUCKET','BUCKET'),
                            ('BUNDLE','BUNDLE'),
                            ('CARTON','CARTON'),
                            ('TANK','TANK'),
                            ('TUBE','TUBE'),
                        ],'Physical Packaging'),

                
                
                }
    _defaults = {
        'fedex_dropoff_type' : 'REGULAR_PICKUP',
        'fedex_service_type' : 'FEDEX_GROUND',
        'fedex_packaging_type' : 'YOUR_PACKAGING',
        'fedex_package_detail' : 'INDIVIDUAL_PACKAGES',
        'fedex_payment_type' : 'SENDER',
        'fedex_physical_packaging' : 'BOX',
    }

    def process_ship(self,cr, uid, ids, context=None):
        
        do = self.browse(cr, uid, type(ids)==type([]) and ids[0] or ids, context=context)
        user = self.pool.get('res.users').browse(cr, uid, uid,  context=context)
        print do.ship_company_code
        if do.ship_company_code != 'fedex':
            return super(stock_picking, self).process_ship(cr, uid, ids, context=context)

        if not (do.logis_company and do.logis_company.ship_company_code=='fedex'):
            return super(stock_picking, self).process_ship(cr, uid, ids, context=context)
        
        from fedex.config import FedexConfig
        config_obj = FedexConfig(key=do.logis_company.fedex_key,
                             password=do.logis_company.fedex_password,
                             account_number=do.logis_company.fedex_account_number,
                             meter_number=do.logis_company.fedex_meter_number,
                             use_test_server=do.logis_company.test_mode)        

        
        from fedex.services.ship_service import FedexProcessShipmentRequest
        
#===============================================================================
#        shipment = FedexProcessShipmentRequest(config_obj)
#        
#        
# 
#        shipment.RequestedShipment.DropoffType = do.fedex_dropoff_type
#        shipment.RequestedShipment.ServiceType = do.fedex_service_type
#        shipment.RequestedShipment.PackagingType = do.fedex_packaging_type
#        shipment.RequestedShipment.PackageDetail= do.fedex_package_detail
#        
#        # Shipper contact info.
#        shipment.RequestedShipment.Shipper.Contact.PersonName = user.name
#        #@todo: check the which module add the company to do and add module dependancy 
#        shipment.RequestedShipment.Shipper.Contact.CompanyName = do.company_id.name
#        shipment.RequestedShipment.Shipper.Contact.PhoneNumber = user.address_id and user.address_id.phone or ''
#        
#        # Shipper address.
#        #@todo: check the address should have value and type is browse object
#        address = do.company_id.partner_id.address and do.company_id.partner_id.address[0] or ''
#        
#        shipment.RequestedShipment.Shipper.Address.StreetLines = [address.street, address.street2]
#        shipment.RequestedShipment.Shipper.Address.City = address.city
#        shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = address.state_id and address.state_id.code or ''
#        
#        #@tod : check which module added zip_id and add module dependancy
#         
#        #shipment.RequestedShipment.Shipper.Address.PostalCode = address.zip        
#        shipment.RequestedShipment.Shipper.Address.PostalCode = address.zip_id and address.zip_id.zipcode
#        shipment.RequestedShipment.Shipper.Address.CountryCode = address.country_id and address.country_id.code or ''
#        shipment.RequestedShipment.Shipper.Address.Residential = True
#        
#                
#        #@todo: Confirm address should have value, else raise error
#        address=do.address_id
#        # Recipient contact info.
#        shipment.RequestedShipment.Recipient.Contact.PersonName = address.partner_id and address.partner_id.name or ''
#        shipment.RequestedShipment.Recipient.Contact.CompanyName = address.partner_id and address.partner_id.name or ''
#        shipment.RequestedShipment.Recipient.Contact.PhoneNumber = address.phone or address.mobile or ''
#        
#        # Recipient address
#        shipment.RequestedShipment.Recipient.Address.StreetLines = [address.street, address.street2]
#        shipment.RequestedShipment.Recipient.Address.City = address.city
#        shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = address.state_id and address.state_id.code or ''
#        
#        #@todo : zip_id and zip : 
#        shipment.RequestedShipment.Recipient.Address.PostalCode = address.zip_id and address.zip_id.zipcode
#        shipment.RequestedShipment.Recipient.Address.CountryCode = address.country_id and address.country_id.code or ''
#        # This is needed to ensure an accurate rate quote with the response.
#        shipment.RequestedShipment.Recipient.Address.Residential = True
#        
#        # Who pays for the shipment?
#        # RECIPIENT, SENDER or THIRD_PARTY
#        shipment.RequestedShipment.ShippingChargesPayment.PaymentType = do.fedex_payment_type
#        
#        # Specifies the label type to be returned.
#        # LABEL_DATA_ONLY or COMMON2D
#        shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'
#        # Specifies which format the label file will be sent to you in.
#        # DPL, EPL2, PDF, PNG, ZPLII
#        shipment.RequestedShipment.LabelSpecification.ImageType = 'PNG'
#        
#        # To use doctab stocks, you must change ImageType above to one of the
#        # label printer formats (ZPLII, EPL2, DPL).
#        # See documentation for paper types, there quite a few.
#        shipment.RequestedShipment.LabelSpecification.LabelStockType = 'PAPER_4X6'
#        
#        # This indicates if the top or bottom of the label comes out of the 
#        # printer first.
#        # BOTTOM_EDGE_OF_TEXT_FIRST or TOP_EDGE_OF_TEXT_FIRST
#        shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = 'BOTTOM_EDGE_OF_TEXT_FIRST'
#        
#        
#===============================================================================
        
        
        if do.packages_ids:
            str_error = ''
            ship_message = ''
            for pack in do.packages_ids:
                #@todo:  If package already have Tracking no then don't process.
                shipment = FedexProcessShipmentRequest(config_obj)
                
                
        
                shipment.RequestedShipment.DropoffType = do.fedex_dropoff_type
                
                #@todo: Depending upon the Service type some of 
                shipment.RequestedShipment.ServiceType = do.fedex_service_type
                shipment.RequestedShipment.PackagingType = do.fedex_packaging_type
                shipment.RequestedShipment.PackageDetail= do.fedex_package_detail
                
                # Shipper contact info.
                shipment.RequestedShipment.Shipper.Contact.PersonName = user.name
                #@todo: check the which module add the company to do and add module dependancy 
                shipment.RequestedShipment.Shipper.Contact.CompanyName = do.company_id.name
                shipment.RequestedShipment.Shipper.Contact.PhoneNumber = user.address_id and user.address_id.phone or ''
                
                # Shipper address.
                #@todo: check the address should have value and type is browse object
                address = do.company_id.partner_id.address and do.company_id.partner_id.address[0] or ''
                
                shipment.RequestedShipment.Shipper.Address.StreetLines = [address.street or '', address.street2 or '']
                shipment.RequestedShipment.Shipper.Address.City = address.city or ''
                shipment.RequestedShipment.Shipper.Address.StateOrProvinceCode = address.state_id and address.state_id.code or ''
                
                #@tod : check which module added zip_id and add module dependancy
                 
                #shipment.RequestedShipment.Shipper.Address.PostalCode = address.zip        
                shipment.RequestedShipment.Shipper.Address.PostalCode = address.zip_id and address.zip_id.zipcode
                shipment.RequestedShipment.Shipper.Address.CountryCode = address.country_id and address.country_id.code or ''
                shipment.RequestedShipment.Shipper.Address.Residential = False
                
                        
                #@todo: Confirm address should have value, else raise error
                address=do.address_id
                # Recipient contact info.
                shipment.RequestedShipment.Recipient.Contact.PersonName = address.name or ''
                shipment.RequestedShipment.Recipient.Contact.CompanyName = address.partner_id and address.partner_id.name or ''
                shipment.RequestedShipment.Recipient.Contact.PhoneNumber = address.phone or address.mobile or ''
                
                # Recipient address
                shipment.RequestedShipment.Recipient.Address.StreetLines = [address.street or '', address.street2 or '']
                shipment.RequestedShipment.Recipient.Address.City = address.city or ''
                shipment.RequestedShipment.Recipient.Address.StateOrProvinceCode = address.state_id and address.state_id.code or ''
                
                #@todo : zip_id and zip : 
                shipment.RequestedShipment.Recipient.Address.PostalCode = address.zip_id and address.zip_id.zipcode or ''
                shipment.RequestedShipment.Recipient.Address.CountryCode = address.country_id and address.country_id.code or ''
                # This is needed to ensure an accurate rate quote with the response.
                shipment.RequestedShipment.Recipient.Address.Residential = False
                
                # Who pays for the shipment?
                # RECIPIENT, SENDER or THIRD_PARTY
                shipment.RequestedShipment.ShippingChargesPayment.PaymentType = do.fedex_payment_type
                
                # Specifies the label type to be returned.
                # LABEL_DATA_ONLY or COMMON2D
                shipment.RequestedShipment.LabelSpecification.LabelFormatType = 'COMMON2D'
                # Specifies which format the label file will be sent to you in.
                # DPL, EPL2, PDF, PNG, ZPLII
                shipment.RequestedShipment.LabelSpecification.ImageType = 'PNG'
                
                # To use doctab stocks, you must change ImageType above to one of the
                # label printer formats (ZPLII, EPL2, DPL).
                # See documentation for paper types, there quite a few.
                shipment.RequestedShipment.LabelSpecification.LabelStockType = 'PAPER_4X8'
                
                # This indicates if the top or bottom of the label comes out of the 
                # printer first.
                # BOTTOM_EDGE_OF_TEXT_FIRST or TOP_EDGE_OF_TEXT_FIRST
                shipment.RequestedShipment.LabelSpecification.LabelPrintingOrientation = 'BOTTOM_EDGE_OF_TEXT_FIRST'
                    
                package_weight = shipment.create_wsdl_object_of_type('Weight')
                
                # Weight, in pounds.
                package_weight.Value = pack.weight
                package_weight.Units = "LB"
                
                package = shipment.create_wsdl_object_of_type('RequestedPackageLineItem')
                package.Weight = package_weight
                
                shipment.add_package(package)
                #Create package
                #Call Print Labels
            
                #print "Shipment SEND VALIDATIOIN REQUEST : ", shipment.send_validation_request()
                #x
                
                try:
                    #print "Shipment : "
                    #print shipment.RequestedShipment
                    shipment.send_request()
        
                    shipment.response.HighestSeverity
                    print "Shipment Response"
                    print shipment.response
                    # Getting the tracking number from the new shipment.
                    tracking_no = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].TrackingIds[0].TrackingNumber
                    # Net shipping costs.
                    
                    
                    ascii_label_data = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].Label.Parts[0].Image
                    logo = binascii.b2a_base64(str(b64decode(ascii_label_data)))
                    
                    
                    #@todo : if payment type is not SENDER ( may if Recipeint or THIRD PARTY ) the  PackageRating will not present in response, so the next line will be error
                    shipping_cost = shipment.response.CompletedShipmentDetail.CompletedPackageDetails[0].PackageRating.PackageRateDetails[0].NetCharge.Amount
                    
                    #@todo: There is a lot of dfferent rates will present in response, need to clarify it.
                    self.pool.get('stock.packages').write(cr, uid, pack.id, {
                                                                                'logo': logo,
                                                                                'negotiated_rates' : shipping_cost,
                                                                                'tracking_no'   : tracking_no, 
                                                                                'ship_message' : shipment.response.HighestSeverity
                                                                              }, context=context)
                    
                    
                except Exception, e:
                    print "ERROR : ", e
                    str_error =  str_error + str(e)
                    
                    #raise osv.except_osv(_('Error'), _('%s' % (e)))
            if str_error:
                #@todo : if some package lines are process successfully and some other failed then now the status will show error.
                # it need cancell all other succeeded shipment and show error msg.
                # or show appropriate msg for each and every packages .
                #@attention: Must cancel other entris or should check the Tracking no befor doing the process, instead of creating new at everytime.
                self.write(cr, uid, do.id, {'ship_message': str_error}, context=context)
            else :
                self.write(cr, uid, do.id, {'ship_state':'ready_pick','ship_message': 'Shipment has been processed.'}, context=context)
                return {
                    'type': 'ir.actions.report.xml',
                    'report_name':'multiple.label.print',
                    'datas': {
                            'model':'stock.picking',
                            'id': ids and ids[0] or False,
                            'ids': ids and ids or [],
                            'report_type': 'pdf'
                        },
                    'nodestroy': True
                    }
        else:
            #@todo: raise appropriate error msg
            raise osv.except_osv(_('Error'), _('%s' % ('No package lines are created for shippment process.')))
                
        return True
    
    def process_void(self,cr, uid, ids, context=None):

        do = self.browse(cr, uid, type(ids)==type([]) and ids[0] or ids, context=context)
        print do.ship_company_code
        if do.ship_company_code != 'fedex':
            return super(stock_picking, self).process_void(cr, uid, ids, context=context)

        if not (do.logis_company and do.logis_company.ship_company_code=='fedex'):
            return super(stock_picking, self).process_void(cr, uid, ids, context=context)
        

        from fedex.config import FedexConfig
        
        config_obj = FedexConfig(key=do.logis_company.fedex_key,
                             password=do.logis_company.fedex_password,
                             account_number=do.logis_company.fedex_account_number,
                             meter_number=do.logis_company.fedex_meter_number,
                             use_test_server=do.logis_company.test_mode)
        
        from fedex.services.ship_service import FedexDeleteShipmentRequest
        
        error = 0
        for pack in do.packages_ids:
            
            #@todo: Must check the company_code saved in stock.packages it should be 'fedex'
            
            if pack.tracking_no:
                
                # This is the object that will be handling our tracking request.
                del_request = FedexDeleteShipmentRequest(config_obj)
                
                # Either delete all packages in a shipment, or delete an individual package.
                # Docs say this isn't required, but the WSDL won't validate without it.
                # DELETE_ALL_PACKAGES, DELETE_ONE_PACKAGE
                
                del_request.DeletionControlType = "DELETE_ALL_PACKAGES"
                
                # The tracking number of the shipment to delete.
                
                del_request.TrackingId.TrackingNumber = pack.tracking_no
                
                # What kind of shipment the tracking number used.
                # Docs say this isn't required, but the WSDL won't validate without it.
                # EXPRESS, GROUND, or USPS
                del_request.TrackingId.TrackingIdType = 'EXPRESS'
                
                # Fires off the request, sets the 'response' attribute on the object.
                del_request.send_request()
                #@todo: check if some packages is possible to delete and others fails.
                print "Response...\n",  del_request.response
                if del_request.response.HighestSeverity=="SUCCESS" or (del_request.response.HighestSeverity=="NOTE" and del_request.response.Notifications[0].Code) :
                    self.pool.get('stock.packages').write(cr, uid, pack.id, {      
                                                                                   'negotiated_rates' : 0.00,
                                                                                   'shipment_identific_no' :'',
                                                                                   'tracking_no': '',
                                                                                   'tracking_url': '',
                                                                                   'logo' : '',
                                                                                   'ship_message' : 'Shipment Cancelled',}, context=context)
                else: 
                    error=1
                # See the response printed out.
                #print del_request.response
        if not error:
            #@todo: check if some packages is possible to delete and others fails.
            self.write(cr, uid, do.id, {'ship_state'    :'draft', 'ship_message' : 'Shipment has been cancelled.'}, context=context)
        else :
            self.write(cr, uid, do.id, { 'ship_message'  : 'Shipment cancellation failed.'}, context=context)
        return True
stock_picking()


