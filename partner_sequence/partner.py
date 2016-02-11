# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 ONESTEiN BV (<http://www.onestein.nl>).
#              (C) 2014 ICTSTUDIO (<http://www.ictstudio.eu>).
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

from openerp.osv import osv, fields
from openerp.tools.translate import _
import logging

_logger = logging.getLogger(__name__)

class res_partner_sequence(osv.osv):
    _name = 'res.partner.sequence'

    _columns = {
        'name': fields.char( 'Sequence Letter',size=1, required=True),
        'sequence_id': fields.many2one('ir.sequence', 'Sequence', required=True)
        }

class res_partner(osv.osv):
    _inherit = 'res.partner'
    
    def _check_ref(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        else:
            context = context.copy()
        context.update({'active_test': False})
        for partner in self.browse(cr, uid, ids, context=context):
            if partner.is_company and partner.ref:
                list_partner_ids = self.search(cr,uid,[('ref','=',partner.ref)])
                if self.search(cr,uid,[('ref','=',partner.ref)]):
                    if len(list_partner_ids)==1 and partner.id == list_partner_ids[0]:
                        return True
                    return False
        return True
    
    _columns = {
        
        #'ref_seq': fields.many2one('res.partner.sequence','Sequence'),
        'ref_seq': fields.char("Reference Sequence",readonly=True),
        'sequence': fields.char("Partner ID",readonly=True),
        'seq_alph':fields.selection([('a','A'),('b','B'),('c','C'),('d','D'),('e','E'),('f','F'),('g','G'),('h','H'),('i','I'),('j','J'),('k','K'),('l','L'),('m','M'),('n','N'),('o','O'),
                                     ('p','P'),('q','Q'),('r','R'),('s','S'),('t','T'),('u','U'),('v','V'),('w','W'),('x','X'),('y','Y'),('z','Z')],'Sequence Prefix'),
        }

    _defaults = {
        'ref': '[Auto]',
        }

    _constraints = [
        (_check_ref, 'A customer number can only be used once', ['ref'])
        ]
    
    def onchange_name(self, cr, uid, ids,name,context=None):
        res={}
        if name :
           if name.upper():
                name=name.lower()
           ref_seq=name[0]
           res['value']={ 'seq_alph':ref_seq}
        return res
    
    def onchange_seq_alph(self, cr, uid, ids,seq_alph,context=None):
        res={}
        if seq_alph:
           if seq_alph.lower():
                seq_alph=seq_alph.upper()
           res['value']={'ref_seq':seq_alph}
        return res
    
    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        else:
            context = context.copy()
        context.update({'active_test': False})
        
        if  not (vals.has_key('sequence') and vals.get('sequence')):
            if vals.has_key('name'):
                name=vals.get('name')
                if name.lower():
                    name=name.upper()
                ref_seq=name[0]
                vals['ref_seq'] = ref_seq
            if vals.has_key('seq_alph') and vals.get('seq_alph'):
                seq_alph=vals.get('seq_alph')
                if seq_alph.lower():
                    seq_alph=seq_alph.upper()
                ref_seq=seq_alph
                vals['ref_seq'] = ref_seq
            if vals.has_key('ref_seq') and vals.get('ref_seq'):
                ref_seq=vals.get('ref_seq')
                vals['sequence'] = self.pool.get('ir.sequence').get_id(cr, uid, ref_seq,'code') or '/'
        
        return super(res_partner, self).create(cr, uid, vals, context)
    
    def write(self, cr, uid,ids, vals, context=None):
        if  not (vals.has_key('sequence') and vals.get('sequence')):
            if vals.has_key('name'):
                name=vals.get('name')
                if name.lower():
                    name=name.upper()
                ref_seq=name[0]
                vals['ref_seq'] = ref_seq
            if vals.has_key('seq_alph'):
                seq_alph=vals.get('seq_alph')
                if seq_alph.lower():
                    seq_alph=seq_alph.upper()
                ref_seq=seq_alph
                vals['ref_seq'] = ref_seq
            if vals.has_key('ref_seq') and vals.get('ref_seq'):
                ref_seq=vals.get('ref_seq')
                vals['sequence'] = self.pool.get('ir.sequence').get(cr, uid, ref_seq) or '/'
        return super(res_partner, self).write(cr, uid,ids,vals,context)
    
res_partner()
    