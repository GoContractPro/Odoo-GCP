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
# from xml.dom.minidom import Document
from openerp.tools.translate import _
# import httplib
import xml2dic
# import time
# import datetime
# from urlparse import urlparse
from PIL import Image
import tempfile
import re

# import netsvc
import base64
import logging
# import tools

# from base64 import b64decode
# import binascii

class logistic_company(osv.osv):
    
    _inherit = "logistic.company"
    
    def _get_company_code(self, cr, user, context=None):
        res = super(logistic_company, self)._get_company_code(cr, user, context=context)
        res.append(('usps', 'USPS'))
        return res
    
    _columns = {
        'ship_company_code' : fields.selection(_get_company_code, 'Ship Company', method=True, required=True, size=64),
        'usps_userid'       : fields.char('User ID', size=128),
        'usps_url_test'     : fields.char('Test Url', size=512),
        'usps_url'          : fields.char('Production URL', size=512),
        'usps_url_secure_test'     : fields.char('Test Url SSL', size=512),
        'usps_url_secure'          : fields.char('Production URL SSL', size=512),
    }

logistic_company()

class stock_packages(osv.osv):
    _inherit = "stock.packages"
    _columns = {
            'usps_confirmation_number': fields.char('USPS Confirm Number', size=64, readonly=True),
     }

stock_packages()

class stock_picking(osv.osv):

    _inherit = "stock.picking"
    
    def _get_company_code(self, cr, user, context=None):
        res = super(stock_picking, self)._get_company_code(cr, user, context=context)
        res.append(('usps', 'USPS'))
        return res
    
    def _get_service_type_usps(self, cr, uid, context=None):
        return [
            ('First Class', 'First Class'),
            ('First Class HFP Commercial', 'First Class HFP Commercial'),
            ('FirstClassMailInternational', 'First Class Mail International'),
            ('Priority', 'Priority'),
            ('Priority Commercial', 'Priority Commercial'),
            ('Priority HFP Commercial', 'Priority HFP Commercial'),
            ('PriorityMailInternational', 'Priority Mail International'),
            ('Express', 'Express'),
            ('Express Commercial', 'Express Commercial'),
            ('Express SH', 'Express SH'),
            ('Express SH Commercial', 'Express SH Commercial'),
            ('Express HFP', 'Express HFP'),
            ('Express HFP Commercial', 'Express HFP Commercial'),
            ('ExpressMailInternational', 'Express Mail International'),
            ('ParcelPost', 'Parcel Post'),
            ('ParcelSelect', 'Parcel Select'),
            ('StandardMail', 'Standard Mail'),
            ('CriticalMail', 'Critical Mail'),
            ('Media', 'Media'),
            ('Library', 'Library'),
            ('All', 'All'),
            ('Online', 'Online'),
        ]
    
    def _get_first_class_mail_type_usps(self, cr, uid, context=None):
        return [
            ('Letter', 'Letter'),
            ('Flat', 'Flat'),
            ('Parcel', 'Parcel'),
            ('Postcard', 'Postcard'),
        ]
    
    def _get_container_usps(self, cr, uid, context=None):
        return [
            ('Variable', 'Variable'),
            ('Card', 'Card'),
            ('Letter', 'Letter'),
            ('Flat', 'Flat'),
            ('Parcel', 'Parcel'),
            ('Large Parcel', 'Large Parcel'),
            ('Irregular Parcel', 'Irregular Parcel'),
            ('Oversized Parcel', 'Oversized Parcel'),
            ('Flat Rate Envelope', 'Flat Rate Envelope'),
            ('Padded Flat Rate Envelope', 'Padded Flat Rate Envelope'),
            ('Legal Flat Rate Envelope', 'Legal Flat Rate Envelope'),
            ('SM Flat Rate Envelope', 'SM Flat Rate Envelope'),
            ('Window Flat Rate Envelope', 'Window Flat Rate Envelope'),
            ('Gift Card Flat Rate Envelope', 'Gift Card Flat Rate Envelope'),
            ('Cardboard Flat Rate Envelope', 'Cardboard Flat Rate Envelope'),
            ('Flat Rate Box', 'Flat Rate Box'),
            ('SM Flat Rate Box', 'SM Flat Rate Box'),
            ('MD Flat Rate Box', 'MD Flat Rate Box'),
            ('LG Flat Rate Box', 'LG Flat Rate Box'),
            ('RegionalRateBoxA', 'RegionalRateBoxA'),
            ('RegionalRateBoxB', 'RegionalRateBoxB'),
            ('Rectangular', 'Rectangular'),
            ('Non-Rectangular', 'Non-Rectangular'),
         ]
    
    def _get_size_usps(self, cr, uid, context=None):
        return [
            ('REGULAR', 'Regular'),
            ('LARGE', 'Large'),
         ]
        
    _columns = {
            'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
            'usps_confirmation_number' : fields.char('Confirmation Number', size=64, readonly=True),
            'usps_service_type' : fields.selection(_get_service_type_usps, 'Service Type', size=100),
            'usps_package_location' : fields.selection([
                    ('Front Door', 'Front Door'),
                    ('Back Door', 'Back Door'),
                    ('Side Door', 'Side Door'),
                    ('Knock on Door/Ring Bell', 'Knock on Door/Ring Bell'),
                    ('Mail Room', 'Mail Room'),
                    ('Office', 'Office'),
                    ('Reception', 'Reception'),
                    ('In/At Mailbox', 'In/At Mailbox'),
                    ('Other', 'Other'),
               ], 'Package Location'),
            'usps_first_class_mail_type' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
            'usps_container' : fields.selection(_get_container_usps, 'Container', size=100),
            'usps_size' : fields.selection(_get_size_usps, 'Size'),
            'usps_length' : fields.float('Length'),
            'usps_width' :  fields.float('Width'),
            'usps_height' :  fields.float('Height'),
            'usps_girth' :  fields.float('Girth'),
            }
    
    _defaults = {
        'usps_service_type'         : 'Priority',
        'usps_package_location'     : 'Front Door',
        'usps_first_class_mail_type': 'Parcel',
        'usps_size'                 : 'REGULAR',
        'usps_container'            : 'Variable',
    }

    def process_ship(self, cr, uid, ids, context=None):
        do = self.browse(cr, uid, type(ids) == type([]) and ids[0] or ids, context=context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if do.ship_company_code != 'usps':
            return super(stock_picking, self).process_ship(cr, uid, ids, context=context)

        if not (do.logis_company and do.logis_company.ship_company_code == 'usps'):
            return super(stock_picking, self).process_ship(cr, uid, ids, context=context)
        userid = do.logis_company.usps_userid
        url = do.logis_company.test_mode and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
        url_prd = do.logis_company.usps_url
        url_prd_secure = do.logis_company.usps_url_secure
        test = do.logis_company.test_mode
        str_error = ''
        ship_message = ''
        error = False
        for package in do.packages_ids:
                    str_error = ''
        # if do.packages_ids:
                    # @Changing to production URL SINCE DelivConfirmCertifyV3.0Request works only with production url and test data
                    url = do.logis_company.usps_url_secure
                    if test:
                        request_xml = """<DelivConfirmCertifyV3.0Request USERID="%(user_id)s">
                                <Option>1</Option>
                                <ImageParameters></ImageParameters>
                                <FromName>Joe Smith</FromName>
                                <FromFirm>ABD Corp.</FromFirm>
                                <FromAddress1>Apt. 3C</FromAddress1>
                                <FromAddress2>6406 Ivy Lane</FromAddress2>
                                <FromCity>Greenbelt</FromCity>
                                <FromState>MD</FromState>
                                <FromZip5>20770</FromZip5>
                                <FromZip4>1234</FromZip4>
                                <ToName>Tom Collins</ToName>
                                <ToFirm>XYZ Corp.</ToFirm>
                                <ToAddress1>Suite 4D</ToAddress1>
                                <ToAddress2>8 Wildwood Drive</ToAddress2>
                                <ToCity>Old Lyme</ToCity>
                                <ToState>CT</ToState>
                                <ToZip5>06371</ToZip5>
                                <ToZip4></ToZip4>
                                <WeightInOunces>1</WeightInOunces>
                                <ServiceType>Priority</ServiceType>
                                <SeparateReceiptPage></SeparateReceiptPage>
                                <POZipCode></POZipCode>
                                <ImageType>TIF</ImageType>
                                <LabelDate></LabelDate>
                                <CustomerRefNo></CustomerRefNo>
                                <AddressServiceRequested></AddressServiceRequested>
                                <SenderName></SenderName>
                                <SenderEMail></SenderEMail>
                                <RecipientName></RecipientName>
                                <RecipientEMail></RecipientEMail>
                                </DelivConfirmCertifyV3.0Request>
                    """ % {   
                            'user_id'      : userid,
                        }
                    if url and request_xml:
                        request_url = url + '?API=DelivConfirmCertifyV3&XML=' + request_xml
                    elif  do.company_id.partner_id.address:
                        from_address = do.company_id.partner_id.address[0]
                        request_xml = """<DeliveryConfirmationV3.0Request USERID="%(user_id)s">
                                            <Option>1</Option>
                                            <ImageParameters />
                                            <FromName>%(from_name)s</FromName>
                                            <FromFirm>%(from_firm)s</FromFirm>
                                            <FromAddress1 />
                                            <FromAddress2>%(from_address2)s</FromAddress2>
                                            <FromCity>%(from_city)s</FromCity>
                                            <FromState>%(from_state)s</FromState>
                                            <FromZip5>%(from_zip5)s</FromZip5>
                                            <FromZip4>%(from_zip4)s</FromZip4>
                                            <ToName>%(to_name)s</ToName>
                                            <ToFirm>%(to_firm)s</ToFirm>
                                            <ToAddress1>%(to_address1)s</ToAddress1>
                                            <ToAddress2>%(to_address2)s</ToAddress2>
                                            <ToCity>%(to_city)s</ToCity>
                                            <ToState>%(to_state)s</ToState>
                                            <ToZip5>%(to_zip5)s</ToZip5>
                                            <ToZip4>%(to_zip4)s</ToZip4>
                                            <WeightInOunces>%(weight)s</WeightInOunces>
                                            <ServiceType>%(service_type)s</ServiceType>
                                            <POZipCode></POZipCode>
                                            <ImageType>TIF</ImageType>
                                            <LabelDate></LabelDate>
                                            <CustomerRefNo></CustomerRefNo>
                                            <AddressServiceRequested>TRUE</AddressServiceRequested>
                                            </DeliveryConfirmationV3.0Request>
                        """ % {   
                            'user_id'       : userid,
                            'from_name'     : from_address.name,
                            'from_firm'     : '',
                            'from_address2' : from_address.street or '',
                            'from_city'     : from_address.city or '',
                            'from_state'    : from_address.state_id and from_address.state_id.code or '',
                            'from_zip5'     : from_address.zip or '',
                            'from_zip4'     : from_address.zip or '',
                            'to_name'       : do.address_id.name ,
                            'to_firm'       : '',
                            'to_address1'   : do.address_id.street,
                            'to_address2'   : do.address_id.street2,
                            'to_city'       : do.address_id.city,
                            'to_state'      : do.address_id.state_id and do.address_id.state_id.code or '',
                            'to_zip5'       : do.address_id.zip or '',
                            'to_zip4'       : do.address_id.zip,
                            'weight'        : package.weight,
                            'service_type'  : do.usps_service_type,
                        }
                        if url and request_xml:
                            request_url = url + '?API=DeliveryConfirmationV3&XML=' + request_xml
                    try :
                        import urllib
                        f = urllib.urlopen(request_url)
                        from xml.dom.minidom import parse, parseString
                        import xml2dic
                        
                        str_response = f.read()
                        xml_response = parseString(str_response)
                        xml_dic = xml2dic.main(str_response)
                        
                        if  'Error' in xml_dic.keys():
                            error = True
                            for item in xml_dic.get('Error'):
                                
                                if item.get('Number'):
                                    if str_error:
                                        str_error = str_error + "\n----------------------"
                                    str_error = str_error + "\nNumber : " + item['Number']
                                if item.get('Description'):
                                    str_error = str_error + "\nDescription : " + item['Description']

                        else:
                            confirmation_number = xml_dic['DelivConfirmCertifyV3.0Response'][0]['DeliveryConfirmationNumber']
                            label_data = xml_dic['DelivConfirmCertifyV3.0Response'][1]['DeliveryConfirmationLabel']
                            # logo = binascii.b2a_base64(str(b64decode(label_data)))
                            # logo = str(b64decode(label_data))
                            
                            logo = base64.decodestring(label_data)

                            import os
                            import tempfile
                            dir_temp = tempfile.gettempdir()
                            
                            f = open(dir_temp + '/usps.tif', 'w+')
                            f.write(logo)
                            f.close()
                            label_image = ''

                            cp = False
                            if os.name == 'posix' or 'nt':
                                try:
                                    os.system("tiffcp -c none " + dir_temp + "/usps.tif " + dir_temp + "/usps_temp.tif")
                                    cp = True
                                except Exception, e:
                                    str_error = "Please install tiffcp."
                            if cp:
                                im = Image.open(dir_temp + '/usps_temp.tif')
                                im.thumbnail(im.size)
                                im.save(dir_temp + '/usps_temp.jpg', "JPEG", quality=100)
                                label_from_file = open(dir_temp + '/usps_temp.jpg', 'rb')
                                label_image = base64.encodestring(label_from_file.read())

                                self.pool.get('stock.packages').write(cr, uid, [package.id], {'logo': label_image, 'tracking_no': confirmation_number, 'usps_confirmation_number': confirmation_number, 'ship_message': 'Shipment has processed'})
                                
                    except Exception, e:
                        str_error = str(e)
            
                    cr.commit()
                    if str_error:
                        self.pool.get('stock.packages').write(cr, uid, do.id, {'ship_message': str_error}, context=context)
                                
        
                
        if not error:
            self.write(cr, uid, do.id, {'ship_state':'ready_pick', 'ship_message': 'Shipment has been processed.'}, context=context)
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
            self.write(cr, uid, do.id, {'ship_message': 'Error occured on processing some of packages, for details please see the status packages.'}, context=context)
            # @todo: raise appropriate error msg
            raise osv.except_osv(_('Error'), _('%s' % ('No package lines are created for shippment process.')))
                
        return True
    
    def process_void(self, cr, uid, ids, context=None):

        do = self.browse(cr, uid, type(ids) == type([]) and ids[0] or ids, context=context)
        if do.ship_company_code != 'usps':
            return super(stock_picking, self).process_void(cr, uid, ids, context=context)

        if not (do.logis_company and do.logis_company.ship_company_code == 'usps'):
            return super(stock_picking, self).process_void(cr, uid, ids, context=context)
        
        userid = do.logis_company.usps_userid
        url = do.logis_company.test_mode and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
        url_prd = do.logis_company.usps_url
        url_prd_secure = do.logis_company.usps_url_secure
        test = do.logis_company.test_mode

        error = False
        str_error = '' 
        
        for pack in do.packages_ids:
            if pack.tracking_no:
                url = test and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
                url_sec = test and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
                if test:
                    request_xml = """<CarrierPickupCancelRequest USERID="%(user_id)s">
                        <FirmName>ABC Corp.</FirmName>
                        <SuiteOrApt>Suite 777</SuiteOrApt>
                        <Address2>1390 Market Street</Address2>
                        <Urbanization></Urbanization>
                        <City>Houston</City>
                        <State>TX</State>
                        <ZIP5>77058</ZIP5>
                        <ZIP4>1234</ZIP4>
                        <ConfirmationNumber>WTC123456789</ConfirmationNumber>
                        </CarrierPickupCancelRequest>
                        """ % {'user_id': do.logis_company.usps_userid}
                else:
                    request_xml = """<CarrierPickupCancelRequest USERID="%(user_id)">
                        <FirmName>ABC Corp.</FirmName>
                        <SuiteOrApt>Suite 777</SuiteOrApt>
                        <Address2>1390 Market Street</Address2>
                        <Urbanization></Urbanization>
                        <City>Houston</City>
                        <State>TX</State>
                        <ZIP5>77058</ZIP5>
                        <ZIP4>1234</ZIP4>
                        <ConfirmationNumber>%(confirmation_number)</ConfirmationNumber>
                        </CarrierPickupCancelRequest>
                        """ % {
                                'user_id': do.logis_company.usps_userid,
                                'confirmation_number' : pack.tracking_no,
                             }
                if url and request_xml:
                    request_url = url + '?API=CarrierPickupCancel&XML=' + request_xml
                try :
                    import urllib
                    f = urllib.urlopen(request_url)
                    from xml.dom.minidom import parse, parseString
                    import xml2dic
                
                    str_response = f.read()
                except Exception:
                    self.pool.get('stock.packages').write(cr, uid, pack.id, {'ship_message': str(Exception)}, context=context)
                    
                    
                xml_response = parseString(str_response)
                xml_dic = xml2dic.main(str_response)
                
                if  'Error' in xml_dic.keys():
                    error = True
                    for item in xml_dic.get('Error'):
                        self.pool.get('stock.packages').write(cr, uid, pack.id, {'ship_message': str_error}, context=context)
                        break
                else:
                    self.pool.get('stock.packages').write(cr, uid, pack.id, {      
                                                                           'negotiated_rates' : 0.00,
                                                                           'shipment_identific_no' :'',
                                                                           'tracking_no': '',
                                                                           'tracking_url': '',
                                                                           'logo' : '',
                                                                           'ship_message' : 'Shipment Cancelled'}, context=context)

        if not error:
            self.write(cr, uid, do.id, {'ship_state'    :'draft', 'ship_message' : 'Shipment has been cancelled.'}, context=context)
        else :
            self.write(cr, uid, do.id, { 'ship_message'  : 'Cancellation of some of shipment has failed, please check the status of pakages.'}, context=context)
        return True
stock_picking()

class stock_picking_out(osv.osv):

    _inherit = "stock.picking.out"

    def _get_company_code(self, cr, user, context=None):
        res = super(stock_picking_out, self)._get_company_code(cr, user, context=context)
        res.append(('usps', 'USPS'))
        return res

    def _get_service_type_usps(self, cr, uid, context=None):
        return [
            ('First Class', 'First Class'),
            ('First Class HFP Commercial', 'First Class HFP Commercial'),
            ('FirstClassMailInternational', 'First Class Mail International'),
            ('Priority', 'Priority'),
            ('Priority Commercial', 'Priority Commercial'),
            ('Priority HFP Commercial', 'Priority HFP Commercial'),
            ('PriorityMailInternational', 'Priority Mail International'),
            ('Express', 'Express'),
            ('Express Commercial', 'Express Commercial'),
            ('Express SH', 'Express SH'),
            ('Express SH Commercial', 'Express SH Commercial'),
            ('Express HFP', 'Express HFP'),
            ('Express HFP Commercial', 'Express HFP Commercial'),
            ('ExpressMailInternational', 'Express Mail International'),
            ('ParcelPost', 'Parcel Post'),
            ('ParcelSelect', 'Parcel Select'),
            ('StandardMail', 'Standard Mail'),
            ('CriticalMail', 'Critical Mail'),
            ('Media', 'Media'),
            ('Library', 'Library'),
            ('All', 'All'),
            ('Online', 'Online'),
        ]
    
    def _get_first_class_mail_type_usps(self, cr, uid, context=None):
        return [
            ('Letter', 'Letter'),
            ('Flat', 'Flat'),
            ('Parcel', 'Parcel'),
            ('Postcard', 'Postcard'),
        ]

    def _get_container_usps(self, cr, uid, context=None):
        return [
            ('Variable', 'Variable'),
            ('Card', 'Card'),
            ('Letter', 'Letter'),
            ('Flat', 'Flat'),
            ('Parcel', 'Parcel'),
            ('Large Parcel', 'Large Parcel'),
            ('Irregular Parcel', 'Irregular Parcel'),
            ('Oversized Parcel', 'Oversized Parcel'),
            ('Flat Rate Envelope', 'Flat Rate Envelope'),
            ('Padded Flat Rate Envelope', 'Padded Flat Rate Envelope'),
            ('Legal Flat Rate Envelope', 'Legal Flat Rate Envelope'),
            ('SM Flat Rate Envelope', 'SM Flat Rate Envelope'),
            ('Window Flat Rate Envelope', 'Window Flat Rate Envelope'),
            ('Gift Card Flat Rate Envelope', 'Gift Card Flat Rate Envelope'),
            ('Cardboard Flat Rate Envelope', 'Cardboard Flat Rate Envelope'),
            ('Flat Rate Box', 'Flat Rate Box'),
            ('SM Flat Rate Box', 'SM Flat Rate Box'),
            ('MD Flat Rate Box', 'MD Flat Rate Box'),
            ('LG Flat Rate Box', 'LG Flat Rate Box'),
            ('RegionalRateBoxA', 'RegionalRateBoxA'),
            ('RegionalRateBoxB', 'RegionalRateBoxB'),
            ('Rectangular', 'Rectangular'),
            ('Non-Rectangular', 'Non-Rectangular'),
         ]
    
    def _get_size_usps(self, cr, uid, context=None):
        return [
            ('REGULAR', 'Regular'),
            ('LARGE', 'Large'),
         ]
    _columns = {
                    'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
                    'usps_confirmation_number' : fields.char('Confirmation Number', size=64, readonly=True),
                    'usps_service_type' : fields.selection(_get_service_type_usps, 'Service Type', size=100),
                    'usps_package_location' : fields.selection([
                            ('Front Door', 'Front Door'),
                            ('Back Door', 'Back Door'),
                            ('Side Door', 'Side Door'),
                            ('Knock on Door/Ring Bell', 'Knock on Door/Ring Bell'),
                            ('Mail Room', 'Mail Room'),
                            ('Office', 'Office'),
                            ('Reception', 'Reception'),
                            ('In/At Mailbox', 'In/At Mailbox'),
                            ('Other', 'Other'),
                       ], 'Package Location'),
                    'usps_first_class_mail_type' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
                    'usps_container' : fields.selection(_get_container_usps, 'Container', size=100),
                    'usps_size' : fields.selection(_get_size_usps, 'Size'),
                    'usps_length' : fields.float('Length'),
                    'usps_width' :  fields.float('Width'),
                    'usps_height' :  fields.float('Height'),
                    'usps_girth' :  fields.float('Girth'),
                }
    _defaults = {
        'usps_service_type'         : 'Priority',
        'usps_package_location'     : 'Front Door',
        'usps_first_class_mail_type': 'Parcel',
        'usps_size'                 : 'REGULAR',
        'usps_container'            : 'Variable',
    }

    def process_ship(self, cr, uid, ids, context=None):
        do = self.browse(cr, uid, type(ids) == type([]) and ids[0] or ids, context=context)
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if do.ship_company_code != 'usps':
            return super(stock_picking_out, self).process_ship(cr, uid, ids, context=context)

        if not (do.logis_company and do.logis_company.ship_company_code == 'usps'):
            return super(stock_picking_out, self).process_ship(cr, uid, ids, context=context)
        userid = do.logis_company.usps_userid
        url = do.logis_company.test_mode and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
        url_prd = do.logis_company.usps_url
        url_prd_secure = do.logis_company.usps_url_secure
        test = do.logis_company.test_mode
        str_error = ''
        ship_message = ''
        error = False
        for package in do.packages_ids:
                    str_error = ''
        # if do.packages_ids:
                    # @Changing to production URL SINCE DelivConfirmCertifyV3.0Request works only with production url and test data
                    url = do.logis_company.usps_url_secure
                    if test:
                        request_xml = """<DelivConfirmCertifyV3.0Request USERID="%(user_id)s">
                                <Option>1</Option>
                                <ImageParameters></ImageParameters>
                                <FromName>Joe Smith</FromName>
                                <FromFirm>ABD Corp.</FromFirm>
                                <FromAddress1>Apt. 3C</FromAddress1>
                                <FromAddress2>6406 Ivy Lane</FromAddress2>
                                <FromCity>Greenbelt</FromCity>
                                <FromState>MD</FromState>
                                <FromZip5>20770</FromZip5>
                                <FromZip4>1234</FromZip4>
                                <ToName>Tom Collins</ToName>
                                <ToFirm>XYZ Corp.</ToFirm>
                                <ToAddress1>Suite 4D</ToAddress1>
                                <ToAddress2>8 Wildwood Drive</ToAddress2>
                                <ToCity>Old Lyme</ToCity>
                                <ToState>CT</ToState>
                                <ToZip5>06371</ToZip5>
                                <ToZip4></ToZip4>
                                <WeightInOunces>1</WeightInOunces>
                                <ServiceType>Priority</ServiceType>
                                <SeparateReceiptPage></SeparateReceiptPage>
                                <POZipCode></POZipCode>
                                <ImageType>TIF</ImageType>
                                <LabelDate></LabelDate>
                                <CustomerRefNo></CustomerRefNo>
                                <AddressServiceRequested></AddressServiceRequested>
                                <SenderName></SenderName>
                                <SenderEMail></SenderEMail>
                                <RecipientName></RecipientName>
                                <RecipientEMail></RecipientEMail>
                                </DelivConfirmCertifyV3.0Request>
                    """ % {   
                            'user_id'      : userid,
                        }
                    if url and request_xml:
                        request_url = url + '?API=DelivConfirmCertifyV3&XML=' + request_xml
                    elif  do.company_id.partner_id:

                        from_address = do.company_id.partner_id

                        request_xml = """<DeliveryConfirmationV3.0Request USERID="%(user_id)s">
                                            <Option>1</Option>
                                            <ImageParameters />
                                            <FromName>%(from_name)s</FromName>
                                            <FromFirm>%(from_firm)s</FromFirm>
                                            <FromAddress1 />
                                            <FromAddress2>%(from_address2)s</FromAddress2>
                                            <FromCity>%(from_city)s</FromCity>
                                            <FromState>%(from_state)s</FromState>
                                            <FromZip5>%(from_zip5)s</FromZip5>
                                            <FromZip4>%(from_zip4)s</FromZip4>
                                            <ToName>%(to_name)s</ToName>
                                            <ToFirm>%(to_firm)s</ToFirm>
                                            <ToAddress1>%(to_address1)s</ToAddress1>
                                            <ToAddress2>%(to_address2)s</ToAddress2>
                                            <ToCity>%(to_city)s</ToCity>
                                            <ToState>%(to_state)s</ToState>
                                            <ToZip5>%(to_zip5)s</ToZip5>
                                            <ToZip4>%(to_zip4)s</ToZip4>
                                            <WeightInOunces>%(weight)s</WeightInOunces>
                                            <ServiceType>%(service_type)s</ServiceType>
                                            <POZipCode></POZipCode>
                                            <ImageType>TIF</ImageType>
                                            <LabelDate></LabelDate>
                                            <CustomerRefNo></CustomerRefNo>
                                            <AddressServiceRequested>TRUE</AddressServiceRequested>
                                            </DeliveryConfirmationV3.0Request>
                        """ % {   
                            'user_id'       : userid,
                            'from_name'     : from_address.name,
                            'from_firm'     : '',
                            'from_address2' : from_address.street or '',
                            'from_city'     : from_address.city or '',
                            'from_state'    : from_address.state_id and from_address.state_id.code or '',
                            'from_zip5'     : from_address.zip or '',
                            'from_zip4'     : from_address.zip or '',
                            'to_name'       : do.partner_id.name ,
                            'to_firm'       : '',
                            'to_address1'   : do.partner_id.street,
                            'to_address2'   : do.partner_id.street2,
                            'to_city'       : do.partner_id.city,
                            'to_state'      : do.partner_id.state_id and do.partner_id.state_id.code or '',
                            'to_zip5'       : do.partner_id.zip or '',
                            'to_zip4'       : do.partner_id.zip,
                            'weight'        : package.weight,
                            'service_type'  : do.usps_service_type,
                        }
                        if url and request_xml:
                            request_url = url + '?API=DeliveryConfirmationV3&XML=' + request_xml
                    try :
                        import urllib
                        f = urllib.urlopen(request_url)
                        from xml.dom.minidom import parse, parseString
                        import xml2dic

                        str_response = f.read()
                        xml_response = parseString(str_response)
                        xml_dic = xml2dic.main(str_response)
                        
                        if  'Error' in xml_dic.keys():
                            error = True
                            for item in xml_dic.get('Error'):
                                
                                if item.get('Number'):
                                    if str_error:
                                        str_error = str_error + "\n----------------------"
                                    str_error = str_error + "\nNumber : " + item['Number']
                                if item.get('Description'):
                                    str_error = str_error + "\nDescription : " + item['Description']

                        else:
                            confirmation_number = xml_dic['DelivConfirmCertifyV3.0Response'][0]['DeliveryConfirmationNumber']
                            label_data = xml_dic['DelivConfirmCertifyV3.0Response'][1]['DeliveryConfirmationLabel']
                            # logo = binascii.b2a_base64(str(b64decode(label_data)))
                            # logo = str(b64decode(label_data))
                            
                            logo = base64.decodestring(label_data)

                            import os
                            import tempfile
                            dir_temp = tempfile.gettempdir()
                            
                            f = open(dir_temp + '/usps.tif', 'w+')
                            f.write(logo)
                            f.close()
                            label_image = ''

                            cp = False
                            if os.name == 'posix' or 'nt':
                                try:
                                    os.system("tiffcp -c none " + dir_temp + "/usps.tif " + dir_temp + "/usps_temp.tif")
                                    cp = True
                                except Exception, e:
                                    str_error = "Please install tiffcp."
                            if cp:
                                im = Image.open(dir_temp + '/usps_temp.tif')
                                im.thumbnail(im.size)
                                im.save(dir_temp + '/usps_temp.jpg', "JPEG", quality=100)
                                label_from_file = open(dir_temp + '/usps_temp.jpg', 'rb')
                                label_image = base64.encodestring(label_from_file.read())

                                self.pool.get('stock.packages').write(cr, uid, [package.id], {'logo': label_image, 'tracking_no': confirmation_number, 'usps_confirmation_number': confirmation_number, 'ship_message': 'Shipment has processed'})
                                
                    except Exception, e:
                        str_error = str(e)

                    cr.commit()
                    if str_error:
                        self.pool.get('stock.packages').write(cr, uid, package.id, {'ship_message': str_error}, context=context)
                    
        if not error:
            self.write(cr, uid, do.id, {'ship_state':'ready_pick', 'ship_message': 'Shipment has been processed.'}, context=context)
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
            self.write(cr, uid, do.id, {'ship_message': 'Error occured on processing some of packages, for details please see the status packages.'}, context=context)
            # @todo: raise appropriate error msg
#             raise osv.except_osv(_('Error'), _('%s' % ('No package lines are created for shippment process.')))

        return True
    
    def process_void(self, cr, uid, ids, context=None):

        do = self.browse(cr, uid, type(ids) == type([]) and ids[0] or ids, context=context)
        if do.ship_company_code != 'usps':
            return super(stock_picking_out, self).process_void(cr, uid, ids, context=context)

        if not (do.logis_company and do.logis_company.ship_company_code == 'usps'):
            return super(stock_picking_out, self).process_void(cr, uid, ids, context=context)
        
        userid = do.logis_company.usps_userid
        url = do.logis_company.test_mode and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
        url_prd = do.logis_company.usps_url
        url_prd_secure = do.logis_company.usps_url_secure
        test = do.logis_company.test_mode

        error = False
        str_error = '' 
        
        for pack in do.packages_ids:
            if pack.tracking_no:
                url = test and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
                url_sec = test and do.logis_company.usps_url_secure_test or do.logis_company.usps_url_secure
                if test:
                    request_xml = """<CarrierPickupCancelRequest USERID="%(user_id)s">
                        <FirmName>ABC Corp.</FirmName>
                        <SuiteOrApt>Suite 777</SuiteOrApt>
                        <Address2>1390 Market Street</Address2>
                        <Urbanization></Urbanization>
                        <City>Houston</City>
                        <State>TX</State>
                        <ZIP5>77058</ZIP5>
                        <ZIP4>1234</ZIP4>
                        <ConfirmationNumber>WTC123456789</ConfirmationNumber>
                        </CarrierPickupCancelRequest>
                        """ % {'user_id': do.logis_company.usps_userid}
                else:
                    request_xml = """<CarrierPickupCancelRequest USERID="%(user_id)">
                        <FirmName>ABC Corp.</FirmName>
                        <SuiteOrApt>Suite 777</SuiteOrApt>
                        <Address2>1390 Market Street</Address2>
                        <Urbanization></Urbanization>
                        <City>Houston</City>
                        <State>TX</State>
                        <ZIP5>77058</ZIP5>
                        <ZIP4>1234</ZIP4>
                        <ConfirmationNumber>%(confirmation_number)</ConfirmationNumber>
                        </CarrierPickupCancelRequest>
                        """ % {
                                'user_id': do.logis_company.usps_userid,
                                'confirmation_number' : pack.tracking_no,
                             }
                request_url = url + '?API=CarrierPickupCancel&XML=' + request_xml
                try :
                    import urllib
                    f = urllib.urlopen(request_url)
                    from xml.dom.minidom import parse, parseString
                    import xml2dic

                    str_response = f.read()
                except Exception:
                    self.pool.get('stock.packages').write(cr, uid, pack.id, {'ship_message': str(Exception)}, context=context)
                    
                    print "Shipment Cancel response :", str_response
                    
                xml_response = parseString(str_response)
                xml_dic = xml2dic.main(str_response)

                if  'Error' in xml_dic.keys():
                    error = True
                    for item in xml_dic.get('Error'):
                        self.pool.get('stock.packages').write(cr, uid, pack.id, {'ship_message': str_error}, context=context)
                        break
                else:
                    self.pool.get('stock.packages').write(cr, uid, pack.id, {      
                                                                           'negotiated_rates' : 0.00,
                                                                           'shipment_identific_no' :'',
                                                                           'tracking_no': '',
                                                                           'tracking_url': '',
                                                                           'logo' : '',
                                                                           'ship_message' : 'Shipment Cancelled'}, context=context)

        if not error:
            self.write(cr, uid, do.id, {'ship_state'    :'draft', 'ship_message' : 'Shipment has been cancelled.'}, context=context)
        else :
            self.write(cr, uid, do.id, { 'ship_message'  : 'Cancellation of some of shipment has failed, please check the status of pakages.'}, context=context)
        return True
stock_picking_out()

class stock_move(osv.osv):
    
    _inherit = "stock.move"

    def created(self, cr, uid, vals, context=None):
        if not context: context = {}
        package_obj = self.pool.get('stock.packages')
        pack_id = None
        package_ids = package_obj.search(cr, uid, [('pick_id', "=", vals.get('picking_id'))])
        if vals.get('picking_id'):
            rec = self.pool.get('stock.picking').browse(cr, uid, vals.get('picking_id'), context)
            if not context.get('copy'):
                if not package_ids:
                    pack_id = package_obj.create(cr, uid , {'package_type': rec.sale_id.usps_packaging_type.id, 'pick_id': vals.get('picking_id')})
        res = super(stock_move, self).create(cr, uid, vals, context)
        if not context.get('copy'):
            context.update({'copy': 1})
            default_vals = {}
            if pack_id:
                default_vals = {'package_id':pack_id, 'picking_id':[]}
            elif package_ids:
                default_vals = {'package_id':package_ids[0], 'picking_id':[]}
            self.copy(cr, uid, res, default_vals , context)
        return res
    
stock_move()

class stock(osv.osv_memory):
    
    _inherit = "stock.invoice.onshipping"
    
    def create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice_ids = []
        res = super(stock, self).create_invoice(cr, uid, ids, context=context)
        invoice_ids += res.values()
        picking_pool = self.pool.get('stock.picking.out')
        invoice_pool = self.pool.get('account.invoice')
        active_picking = picking_pool.browse(cr, uid, context.get('active_id', False), context=context)
        if active_picking:
            invoice_pool.write(cr, uid, invoice_ids, {'shipcharge':active_picking.shipcharge }, context=context)
        return res
stock()
