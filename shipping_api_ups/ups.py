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

class ups_account_shipping(osv.osv):
    
    _name = "ups.account.shipping"

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'ups_account_id': fields.many2one('ups.account', 'UPS Account', required=True),
        'accesslicensenumber': fields.related('ups_account_id', 'accesslicensenumber', type='char', size=64, string='AccessLicenseNumber', required=True),
        'userid': fields.related('ups_account_id', 'userid', type='char', size=64, string='UserId', required=True),
        'password': fields.related('ups_account_id', 'password', type='char', size=64, string='Password', required=True),
        'active': fields.related('ups_account_id', 'ups_active', string='Active', type='boolean'),
        'acc_no': fields.related('ups_account_id', 'acc_no', type='char', size=64, string='Account Number', required=True),
        'atten_name': fields.char('AttentionName', size=64, required=True, select=1),
        'tax_id_no': fields.char('Tax Identification Number', size=64 , select=1, help="Shipper's Tax Identification Number."),
        'logistic_company_id': fields.many2one('logistic.company', 'Parent Logistic Company'),
        'delivery_mthd_id': fields.many2one('delivery.method', 'Parent Delivery Method'),
#         'ups_shipping_service_ids': fields.one2many('ups.shipping.service.type', 'ups_account_id', 'Shipping Service'),
        'ups_shipping_service_ids':fields.many2many('ups.shipping.service.type', 'shipping_service_rel', 'ups_account_id', 'service_id', 'Shipping Service'),
        'address': fields.property(
           'res.partner',
           type='many2one',
           relation='res.partner',
           string="Shipper Address",
           view_load=True),
        'trademark': fields.char('Trademark', size=1024, select=1),
        'company_id': fields.many2one('res.company', 'Company'),
    }
    _defaults = {
        'active': True
    }
    
    def onchange_ups_account(self, cr, uid, ids, ups_account_id=False, context=None):
        res = {
            'accesslicensenumber': '',
            'userid': '',
            'password': '',
            'active': True,
            'acc_no': ''
            }
        
        if ups_account_id:
            ups_account = self.pool.get('ups.account').browse(cr, uid, ups_account_id, context=context)
            res = {
                'accesslicensenumber': ups_account.accesslicensenumber,
                'userid': ups_account.userid,
                'password': ups_account.password,
                'active': ups_account.ups_active,
                'acc_no': ups_account.acc_no
                }
        return {'value': res}

ups_account_shipping()

class ups_account_shipping_service(osv.osv):
    
    _name = "ups.shipping.service.type"
    _rec_name = "description"
    
    _columns = {
        'description': fields.char('Description', size=32, required=True, select=1),
        'category': fields.char('Category', size=32, select=1),
        'shipping_service_code': fields.char('Shipping Service Code', size=8, select=1),
        'rating_service_code': fields.char('Rating Service Code', size=8, select=1),
        'ups_account_id': fields.many2one('ups.account.shipping', 'Parent Shipping Account'),
        
        'common':fields.boolean("Common?",help="Is Service Applicable for both domestic or international ups shippings"),
        'is_intnl':fields.boolean("International?",help="Service Applicable for International ups shippings or Domestic if unchecked"),
        }
    
ups_account_shipping_service()

class delivery_method(osv.osv):
    _inherit = "delivery.method"
    
    def _get_company_code(self, cr, user, context=None):
        res =  super(delivery_method, self)._get_company_code(cr, user, context=context)
        res.append(('ups', 'UPS'))
        return res
    
    _columns={
                'ship_company_code': fields.selection(_get_company_code, 'Logistic Company', method=True, required=True, size=64),
                'ship_req_web': fields.char('Ship Request Website', size=256 ),
                'ship_req_port': fields.integer('Ship Request Port'),
                'ship_req_test_web': fields.char('Test Ship Request Website', size=256 ),
                'ship_req_test_port': fields.integer('Test Ship Request Port'),
                'ship_accpt_web': fields.char('Ship Accept Website', size=256 ),
                'ship_accpt_port': fields.integer('Ship Accept Port' ),
                'ship_accpt_test_web': fields.char('Test Ship Accept Website', size=256),
                'ship_accpt_test_port': fields.integer('Test Ship Accept Port'),
                'ship_void_web': fields.char('Ship Void Website', size=256),
                'ship_void_port': fields.integer('Ship Void Port'),
                'ship_void_test_web': fields.char('Test Ship Void Website', size=256),
                'ship_void_test_port': fields.integer('Test Ship Void Port'),
                'ship_rate_web': fields.char('Ship Rate Website', size=256 ),
                'ship_rate_port': fields.integer('Ship Rate Port'),
                'ship_rate_test_web': fields.char('Test Ship Rate Website', size=256 ),
                'ship_rate_test_port': fields.integer('Test Ship Rate Port'),
                'ship_tracking_url': fields.char('Tracking URL', size=256),
               'ups_shipping_account_ids': fields.one2many('ups.account.shipping', 'delivery_mthd_id', 'Shipping Account'),
               'test_mode': fields.boolean('Test Mode'),
               'url': fields.char('Website',size=256 , select=1),
               'company_id': fields.many2one('res.company', 'Company'),
               'ship_account_id': fields.property(
               'account.account',
               type='many2one',
               relation='account.account',
               string="Cost Account",
               view_load=True),
            'note': fields.text('Notes'),
              }
    _defaults = {
        'ship_req_web': "https://onlinetools.ups.com/webservices/shipconfirm",
        'ship_req_port': 443,
        'ship_req_test_web': "https://wwwcie.ups.com/ups.app/xml/ShipConfirm",
        'ship_req_test_port': 443,
        'ship_accpt_web': "https://onlinetools.ups.com/ups.app/ShipAccept",
        'ship_accpt_port': 443,
        'ship_accpt_test_web': "https://wwwcie.ups.com/ups.app/xml/ShipAccept",
        'ship_accpt_test_port': 443,
        'ship_void_web': "https://onlinetools.ups.com/xml/ups.app/void",
        'ship_void_port': 443,
        'ship_void_test_web': "https://wwwcie.ups.com/ups.app/xml/Void",
        'ship_void_test_port': 443,
        'ship_rate_web': "https://onlinetools.ups.com/ups.app/xml/Rate",
        'ship_rate_port': 443,
        'ship_rate_test_web': "https://wwwcie.ups.com/ups.app/xml/Rate",
        'ship_rate_test_port': 443,
        'ship_tracking_url': "https://wwwapps.ups.com/WebTracking/processInputRequest?sort_by=status&tracknums_displayed=1&TypeOfInquiryNumber=T&loc=en_US&InquiryNumber1=%s&track.x=0&track.y=0",
                 }
    
    def onchange_shipping_number(self, cr, uid, ids, shipping_no, url, context=None):
        ret = {}
        if url:
            b = url[url.rindex('/'): len(url)]
            b = b.strip('/')
            if re.match("^[0-9]*$", b):
                url = url[0:url.rindex('/')]
            url += ('/' + shipping_no)
            ret['url'] = url
        return{'value': ret}
        
delivery_method()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
