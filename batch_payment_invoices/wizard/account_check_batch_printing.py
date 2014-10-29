# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tools.translate import _

from openerp.osv import fields, osv

class account_check_write(osv.TransientModel):
    _inherit = 'account.check.write'
    _description = 'Prin Check in Batch'

    _columns = {
            'printed': fields.boolean('Printed'),
            'check_state': fields.selection([('void','Voided'),('print','Printed'),('re_print','Re-Printed'),('clear','Cleared')],'Check Status'),
            'new_no': fields.integer('Update Check Number', help= 'Enter new check number here if you wish to update'),
            'msg': fields.char('Warning', size=128, readonly=True),
            'check_print_choice':fields.selection([('re_print','Re-Print'),('void','Void'),('clear','Clear')],'What would you like to do with this check?'),
    }
    
    def _get_state(self, cr, uid, context=None):
        """
        Function to initialise state
        """
        if context is None:
            context = {}
        state = ''
        if context.get('active_model') != 'account.voucher':
            return state 
        for voucher_id in self.pool.get('account.voucher').browse(cr, uid, context['active_ids'], context=context):
            if voucher_id.state != 'posted':
                raise osv.except_osv(_('Warning!'), _('Payment is not posted. Please Validate Payment First!'))
            if voucher_id.check_status:
                state = voucher_id.check_status
        return state

    def _check_no(self, cr, uid, ids, context=None):
        acc_vou_obj = self.pool.get('account.voucher')
        new_no =self.browse(cr, uid, ids, context=context)[0].new_no
        check_no_id = acc_vou_obj.search(cr, uid, [('chk_seq','=',new_no)])
        if check_no_id:
                raise osv.except_osv(_('Error!'),_("Check No. %s already exists. System can't use the existing check number for this payment.") % (new_no,))
        return True

    _constraints = [
        (_check_no, "Error! Check No. already exists. System can't use the existing check number for this payment", ['new_no'])
    ]
    def _get_msg(self, cr, uid, context=None):
        """
        Function to initialize preprint_msg
        """
        if context is None:
            context = {}
        if not context.get('active_model') == 'account.voucher':
            return ''
        msg1 = 'This Payment has already been paid with check:\n'
        msg2 = 'These Payments have already been paid with checks:\n'
        msg3 = 'Some of these Payments have already been paid with checks:\n'
        chk_nos = []
        voucher_ids = self.pool.get('account.voucher').browse(cr, uid, context.get('active_ids', []), context=context)
        records = []
        if context.get('active_ids'):
            records = (context.get('active_ids'))
        for voucher in voucher_ids:
            if voucher and voucher.chk_seq:
                chk_nos.append(str(voucher.chk_seq))
        msg = ''
        if len(chk_nos) == 1:
            msg = msg1 + str(chk_nos[0])
        elif len(chk_nos) == len(records):
            msg = msg2 + '\n'.join(chk_nos)
        elif not chk_nos:
            msg = msg
        else:
            msg = msg3 + '\n'.join(chk_nos)
        return msg
        
    _defaults = {
            'check_state':_get_state,
            'new_no':lambda self,cr,uid,c: self.pool.get('account.check.write')._get_next_number(cr, uid,context=c),
            'msg': _get_msg, 
            }
    def reprint_check_write(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        voucher_obj = self.pool.get('account.voucher')
        ir_sequence_obj = self.pool.get('ir.sequence')
        dummy, sequence_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_check_writing', 'sequence_check_number')
        voucher_ids = context.get('active_ids', [])
        new_value = self.browse(cr, uid, ids[0], context=context).new_no
        
        check_status = self.browse(cr, uid, ids[0],context=None).check_print_choice
        if check_status == 're_print':
            if new_value:
                ir_sequence_obj.write(cr, uid, sequence_id, {'number_next': (new_value + 1)})
        for check in voucher_obj.browse(cr, uid, voucher_ids, context=context):
            if check_status == 're_print':
                voucher_obj.write(cr, uid, check.id,{'chk_seq':new_value, 'check_status': 're_print'}, context=context)
            elif check_status == 'void':
                voucher_obj.write(cr, uid, check.id,{'check_status': 'void'}, context=context)
            elif check_status == 'clear':
                voucher_obj.write(cr, uid, check.id,{'check_status': 'clear'}, context=context)
        return {
            'type': 'ir.actions.report.xml', 
            'report_name':"account.print.check.top.multi",
            'datas': {
                'model':'account.voucher',
                'ids': voucher_ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
            }

    def print_check_write(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        voucher_obj = self.pool.get('account.voucher')
        ir_sequence_obj = self.pool.get('ir.sequence')
        #update the sequence to number the checks from the value encoded in the wizard
        dummy, sequence_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'account_check_writing', 'sequence_check_number')
        increment = ir_sequence_obj.read(cr, uid, sequence_id, ['number_increment'])['number_increment']
        new_value = self.browse(cr, uid, ids[0], context=context).check_number
        wizard = self.browse(cr, uid, ids[0], context=context)
        ir_sequence_obj.write(cr, uid, sequence_id, {'number_next': new_value})
        #validate the checks so that they get a number
        voucher_ids = context.get('active_ids', [])
        cr.execute("SELECT id FROM account_voucher s  \
                                WHERE s.id in %s \
                                order by partner_id\
                                    ",(tuple(voucher_ids),))
        voucher_ids =  map(lambda x: x[0], cr.fetchall())
        partner_ids = []
        for check in voucher_obj.browse(cr, uid, voucher_ids, context=context):
            if not check.partner_id.id in partner_ids:
                check_mumber = new_value
                new_value += increment
            partner_ids.append(check.partner_id.id)
            if check.number and wizard.check_state == 're_print':
                voucher_obj.write(cr, uid, check.id,{'chk_seq':check_mumber, 'check_status': 're_print'}, context=context)
            elif check.number and wizard.check_state == 'void':
                voucher_obj.write(cr, uid, check.id,{'chk_seq':check_mumber, 'check_status': 'void'}, context=context)
#                raise osv.except_osv(_('Error!'),_("One of the printed check already got a number."))
            elif check.number and wizard.check_state == 'clear':
                voucher_obj.write(cr, uid, check.id,{'chk_seq':check_mumber, 'check_status': 'clear' }, context=context)
#            elif check.number and not wizard.check_state:
#                raise osv.except_osv(_('Error!'),_("One of the printed check already got a number."))
            elif check.number and not wizard.check_state:
                voucher_obj.write(cr, uid, check.id,{'chk_seq':check_mumber, 'check_status': 'print'}, context=context)
            elif not check.number and not wizard.check_state:
                voucher_obj.write(cr, uid, check.id,{'chk_seq':check_mumber, 'check_status': 'print'}, context=context)
#            voucher_obj.button_proforma_voucher(cr, uid, voucher_ids, context=context)
        #update the sequence again (because the assignation using next_val was made during the same transaction of
        #the first update of sequence)
        ir_sequence_obj.write(cr, uid, sequence_id, {'number_next': new_value})
        #print the checks
        check_layout_report = {
            'top' : 'account.print.check.top',
            'middle' : 'account.print.check.middle',
            'bottom' : 'account.print.check.bottom',
        }
#        check_layout = voucher_obj.browse(cr, uid, voucher_ids[0], context=context).company_id.check_layout
#        if not check_layout:
#            check_layout = 'top'
        return {
            'type': 'ir.actions.report.xml', 
            'report_name':"account.print.check.top.multi",
            'datas': {
                'model':'account.voucher',
                'ids': voucher_ids,
                'report_type': 'pdf'
                },
            'nodestroy': True
            }

