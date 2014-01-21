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

class sale_order(osv.osv):
    _inherit = "sale.order"
    
    def _get_company_code(self, cr, user, context=None):
        res = super(sale_order, self)._get_company_code(cr, user, context=context)
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
        
    def action_ship_create(self, cr, uid, ids, context=None):
        pick_obj = self.pool.get('stock.picking')
        result = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
        if result:
            for sale in self.browse(cr, uid, ids, context=None):
                if sale.ship_company_code == 'usps':
                    pick_ids = pick_obj.search(cr, uid, [('sale_id', '=', sale.id), ('type', '=', 'out')], context=context)
                    if pick_ids:
                        vals = {
                                    'ship_company_code'     : 'usps',
                                    'logis_company'         : sale.logis_company and sale.logis_company.id or False,
                                    'usps_service_type'     : sale.usps_service_type,
                                    'usps_package_location' : sale.usps_package_location,
                                    'usps_first_class_mail_type' : sale.usps_first_class_mail_type,
                                    'usps_container'    : sale.usps_container,
                                    'usps_size'         : sale.usps_size,
                                    'usps_length'       : sale.usps_length,
                                    'usps_width'        : sale.usps_width,
                                    'usps_height'       : sale.usps_height,
                                    'usps_girth'        : sale.usps_girth,
                                    'shipcharge'         : sale.shipcharge
                                }
                        pick_obj.write(cr, uid, pick_ids, vals, context=context)
        return result
    
    _columns = {
            'ship_company_code': fields.selection(_get_company_code, 'Ship Company', method=True, size=64),
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
               ], 'Package Location', size=64),
            'usps_first_class_mail_type' : fields.selection(_get_first_class_mail_type_usps, 'First Class Mail Type', size=50),
            'usps_container' : fields.selection(_get_container_usps, 'Container', size=100),
            'usps_size' : fields.selection(_get_size_usps, 'Size'),
            'usps_length' : fields.float('Length'),
            'usps_width' :  fields.float('Width'),
            'usps_height' :  fields.float('Height'),
            'usps_girth' :  fields.float('Girth'),
            'usps_packaging_type': fields.many2one('shipping.package.type', 'Packaging Type')
            }
    
    _defaults = {
        'usps_service_type'         : 'Priority',
        'usps_package_location'     : 'Front Door',
        'usps_first_class_mail_type': 'Parcel',
        'usps_size'                 : 'REGULAR',
        'usps_container'            : 'Variable',

    }
sale_order()
