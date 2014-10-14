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

class shipping_package_type(osv.osv):
    _name = 'shipping.package.type'
    _columns = {
        'name': fields.char('Package Type', size=32, required=True),
        'code': fields.char('Code', size=16),
        'length': fields.float('Length', help='Indicates the longest length of the box in inches.'),
        'width': fields.float('Width'),
        'height': fields.float('Height'),
        
        'common':fields.boolean("Common?",help="Is Package type allowed for both domestic or international ups shippings"),
        'is_intnl':fields.boolean("International?",help="Package type allowed for International ups shippings or Domestic if unchecked"),
    }

shipping_package_type()

class stock_packages(osv.osv):
    _name = "stock.packages"
    _description = "Packages of Delivery Order"
    _rec_name = "packge_no"

    def _button_visibility(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for package in self.browse(cr, uid, ids, context=context):
            result[package.id] = True
            if package.pick_id.ship_state in ['read_pick','shipped','delivered', 'draft', 'cancelled']:
                result[package.id] = False
        return result

    def _get_decl_val(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for rec in self.browse(cr, uid, ids, context=context):
            sum = 0
            for item in rec.stock_move_ids:
                sum += item.cost or 0.0
            res[rec.id] = sum
        return res
    
    _columns = {
        'packge_no': fields.char('Package Number', size=64, help='The number of the package associated with the delivery.\
                                    Example: 3 packages may be associated with a delivery.'),
        'weight': fields.float('Weight (lbs)', required=1, help='The weight of the individual package'),
        'package_type': fields.many2one('shipping.package.type','Package Type', help='Indicates the type of package'),
        'length': fields.float('Length', help='Indicates the longest length of the box in inches.'),
        'width': fields.float('Width', help='Indicates the width of the package in inches.'),
        'height': fields.float('Height', help='Indicates the height of the package inches.'),
        'ref1': fields.selection([
            ('AJ', 'Accounts Receivable Customer Account'),
            ('AT', 'Appropriation Number'),
            ('BM', 'Bill of Lading Number'),
            ('9V', 'Collect on Delivery (COD) Number'),
            ('ON', 'Dealer Order Number'),
            ('DP', 'Department Number'),
            ('3Q', 'Food and Drug Administration (FDA) Product Code'),
            ('IK', 'Invoice Number'),
            ('MK', 'Manifest Key Number'),
            ('MJ', 'Model Number'),
            ('PM', 'Part Number'),
            ('PC', 'Production Code'),
            ('PO', 'Purchase Order Number'),
            ('RQ', 'Purchase Request Number'),
            ('RZ', 'Return Authorization Number'),
            ('SA', 'Salesperson Number'),
            ('SE', 'Serial Number'),
            ('ST', 'Store Number'),
            ('TN', 'Transaction Reference Number'),
            ('EI', 'Employee ID Number'),
            ('TJ', 'Federal Taxpayer ID No.'),
            ('SY', 'Social Security Number'),
            ], 'Reference Number 1', help='Indicates the type of 1st reference no'),
        'ref2': fields.char('Reference Number 1', size=64, help='A reference number 1 associated with the package.'),
        'ref2_code': fields.selection([
            ('AJ', 'Accounts Receivable Customer Account'),
            ('AT', 'Appropriation Number'),
            ('BM', 'Bill of Lading Number'),
            ('9V', 'Collect on Delivery (COD) Number'),
            ('ON', 'Dealer Order Number'),
            ('DP', 'Department Number'),
            ('3Q', 'Food and Drug Administration (FDA) Product Code'),
            ('IK', 'Invoice Number'),
            ('MK', 'Manifest Key Number'),
            ('MJ', 'Model Number'),
            ('PM', 'Part Number'),
            ('PC', 'Production Code'),
            ('PO', 'Purchase Order Number'),
            ('RQ', 'Purchase Request Number'),
            ('RZ', 'Return Authorization Number'),
            ('SA', 'Salesperson Number'),
            ('SE', 'Serial Number'),
            ('ST', 'Store Number'),
            ('TN', 'Transaction Reference Number'),
            ('EI', 'Employee ID Number'),
            ('TJ', 'Federal Taxpayer ID No.'),
            ('SY', 'Social Security Number'),
            ], 'Reference Number', help='Indicates the type of 2nd reference no'),
        'ref2_number': fields.char('Reference Number 2', size=64, help='A reference number 2 associated with the package.'),
        'pick_id': fields.many2one('stock.picking', 'Delivery Order'),
        'ship_move_id': fields.many2one('shipping.move', 'Delivery Order'),
        'description': fields.text('Description'),
        'logo': fields.binary('Logo'),
        'negotiated_rates': fields.float('NegotiatedRates'),
         'shipment_identific_no': fields.char('ShipmentIdentificationNumber', size=64),
         'tracking_no': fields.char('TrackingNumber', size=64),
        'ship_message': fields.text('Status Message'),
        'tracking_url': fields.char('Tracking URL', size=512),
        'package_type_id': fields.many2one('logistic.company.package.type', 'Package Type'),
        'show_button': fields.function(_button_visibility, method=True, type='boolean', string='Show'),
        #'package_item_ids' : fields.one2many('shipment.package.item','package_id','Package Items'),
        'stock_move_ids' : fields.one2many('stock.move','package_id','Package Items'),
        'decl_val': fields.function(_get_decl_val, method=True, string='Declared Value', type='float', help='The declared value of the package.'),
        
        'is_intnl':fields.boolean("International?",help="Package type allowed for International ups shippings or Domestic if unchecked"),
        
        'eei_file': fields.boolean('EEI Filing'),
        
        # EEI Information
        'product_eei_info_export_information':fields.selection([('lc', 'LC'),('lv', 'LV'),('ss', 'SS'),('ms', 'MS'),('gs', 'GS'),('dp', 'DP'),('hr', 'HR'),('ug', 'UG'),('ic', 'IC'),
                                        ('sc', 'SC'),('dd', 'DD'),('hh', 'HH'),('dp', 'DP'),('hr', 'HR'),('ug', 'UG'),('ic', 'IC'),('sc', 'SC'),('dd', 'DD'),('hh', 'HH'),
                                        ('sr', 'SR'),('te', 'TE'),('tl', 'TL'),('is', 'IS'),('cr', 'CR'),('gp', 'GP'),('rj', 'RJ'),('tp', 'TP'),('ip', 'IP'),('ir', 'IR'),('db', 'DB'),('ch', 'CH'),('rs', 'RS'),('os', 'OS'),],'Export Information'),
      # License
      'product_eei_info_license_number':fields.char("Number",size=256),
      'product_eei_info_license_code':fields.char("Code",size=256),
      'product_eei_info_license_line_value':fields.char("License Line Value",size=256),
      'product_eei_info_license_eccn_number':fields.char("ECCN Number" ,size=256),
      # DDTC Information
      'product_eei_info_license_ddtc_info_itar_exemption_number':fields.char("ITAR Exemption Number" ,size=256),
      'product_eei_info_license_ddtc_info_usml_category_code':fields.char("USML Category Code" ,size=256),
      'product_eei_info_license_ddtc_info_eligible_prty_indicator':fields.char("Eligible Party Indicator" ,size=256),
      'product_eei_info_license_ddtc_info_registration_number':fields.char("Registration Number" ,size=256),
      'product_eei_info_license_ddtc_info_quantity':fields.integer("Quantity"),
      'product_eei_info_license_ddtc_info_code':fields.char("Code",size=256),
      'product_eei_info_license_ddtc_info_description':fields.char("Description",size=256),
      'product_eei_info_license_ddtc_info_significant_mili_equip_ind':fields.char("Significant Military Equipment Indicator",size=256),
      'product_eei_info_license_ddtc_info_acm_number':fields.char("ACM Number",size=256),
      
      #EEI > Product > ScheduleB Tags.
        
        'eei_prod_schedule_number':fields.char("Commodity classification code",size=256),#10Digits code
        'eei_prod_schedule_qty':fields.float("Quantity"),
        #EEI > Product > ScheduleB >UoM Tags.
        'eei_prod_schedule_uom_code':fields.selection([('BBL', 'Barrels'),('CAR', 'Carat'),('CKG', 'Content Kilogram'),('CM2', 'Square Centimeters'),
                                                       ('CTN', 'Content Ton'),('CUR', 'Curie'),('CYK', 'Clean Yield Kilogram'),('DOZ', 'Dozen'),
                                                       ('DPC', 'Dozen Pieces'),('DPR', 'Dozen Pairs'),('FBM', 'Fiber Meter'),('GCN', 'Gross Containers'),
                                                       ('GM', 'Gram'),('GRS', 'Gross'),('HUN', 'Hundred'),('KG', 'Kilogram'),
                                                       ('KM3', '1,000 Cubic Meters'),('KTS', 'Kilogram Total Sugars'),('L', 'Liter'),('M', 'Meter'),
                                                       ('M2', 'Square Meters'),('M3', 'Cubic Meters'),('MC', 'Millicurie'),('NO', 'Number'),
                                                       ('PCS', 'Pieces'),('PFL', 'Proof Liter'),('PK', 'Pack'),('PRS', 'Pairs'),
                                                       ('RBA', 'Running Bales'),('SQ', 'Square'),('T', 'Ton'),('THS', '1,000'),
                                                       ('X', 'No Quantity required')],'UoM Code'),
        'eei_prod_schedule_uom_desc':fields.char("Description",size=256),
        
        #EEI > Product > 
        'eei_prod_exoprt_type':fields.selection([('D', 'Domestic'),('F', 'Foreign'),],'Exoprt Type', help="""
        Code indicating Domestic: Exports that have been produced, manufactured, or grown in the United States or Puerto Rico.
        This includes imported merchandise which has been enhanced in value or changed from the form in which imported by further
        manufacture or processing in the United States or Puerto Rico.
        Foreign: Merchandise that has entered the United States and is being exported again in the same condition as when imported.
        """),
           #EEI > Product >       
        'eei_prod_sed_tot_val':fields.float("SED Total Value", help="This amount will always be USD. This attribute represents the LicenseLineValue for EEI."),
        
    }

    _defaults = {
        'weight': 0.0
    }
    
    
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_packages, self).default_get(cr, uid, fields, context=context)
#         move_ids = context.get('active_ids', [])
        active_model = context.get('active_model')
        eei_file = context.get('eei_file')
        if eei_file :
            res.update(eei_file=eei_file)
        return res


    def print_label(self, cr, uid, ids, context=None):
        if not ids: return []
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'ship.label.print',
            'datas': {
                'model': 'stock.packages',
                'id': ids and ids[0] or False,
                'ids': ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }

    def print_packing_slips(self, cr, uid, ids, context=None):
        if not ids: return []
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'package.packing.slip.print',
            'datas': {
                'model': 'stock.packages',
                'id': ids and ids[0] or False,
                'ids': ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
        }

    def onchange_packge_no(self, cr, uid, ids, packge_no, line_ids, context=None):
        
        """
        Function to generate sequence on packages
        """
        ret = {}
        if packge_no:
            ret['packge_no'] = packge_no
        else:
            if line_ids:
                for line in line_ids:
                        if line and line[2] and line[2]['packge_no'] and packge_no < line[2]['packge_no']:
                            packge_no = line[2]['packge_no']
                packge_no = str(int(packge_no)+1)
            ret['packge_no'] = packge_no
        return {'value': ret}

    def onchange_weight(self, cr, uid, ids, line_ids, tot_order_weight, weight, context=None):
       
        """
        Function to automatically fill package weight
        """
        if line_ids == False:
            line_ids = []
        ret = {}
        if weight:
            ret['weight'] = weight
        else:
            used_weight = 0
            for line in line_ids:
                if line and line[2] and line[2]['weight']:
                    used_weight += line[2]['weight']
            if used_weight < tot_order_weight:
                ret['weight'] = tot_order_weight - used_weight
        return {'value': ret}

    def onchange_stock_package(self, cr, uid, ids, package_type):
        res = {}
        res['value'] = {
                'length': 0,
                'width': 0,
                'height': 0,
        }
        if package_type:
            package_type_obj = self.pool.get('shipping.package.type').browse(cr, uid, package_type)
            res['value'] = {
                'length': package_type_obj.length,
                'width':package_type_obj.width,
                'height': package_type_obj.height,
        }
        return res

stock_packages()

# TODO - Commenting the code for Package Item for future re
#class shipment_package_item(osv.osv):
#    _name = 'shipment.package.item'
#    _description = 'Shipment Package Item'
#    _rec_name = 'product_id'
#
#    def onchange_product_id(self, cr, uid, ids, product_id, qty=0.0):
#        res = {'value':{'cost':0.0}}
#        product_obj = self.pool.get('product.product')
#        if not product_id:
#            return res
#        prod = product_obj.browse(cr, uid, product_id)
#        if not qty:
#            qty = 1
#        res['value'] = {
#            'cost' : (prod.list_price * qty) or 0.0
#        }
#        return res
#
#    _columns = {
#        'product_id': fields.many2one('product.product','Product', required=True),
#        'cost': fields.float('Value', digits_compute=dp.get_precision('Account'), required=True),
#        'package_id': fields.many2one('stock.packages','Package'),
#        'qty': fields.float('Quantity', digits_compute=dp.get_precision('Account')),
#    }
#
#shipment_package_item()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: