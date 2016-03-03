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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
import time


class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    @api.one
    @api.depends('invoice_line','invoice_line.weight_net')
    
    def _total_weight_net(self):
        """Compute the total net weight of the given Invoice."""

        self.total_weight_net = 0.0
        for line in self.invoice_line:
            if line.product_id:
                self.total_weight_net += line.weight_net or 0.0  
    
    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount','shipcharge')
    def _compute_amount(self):

        
        super(account_invoice,self)._compute_amount()

        self.amount_total += self.shipcharge

    shipcharge =  fields.Float('Shipping Charge', readonly=True)
    shipcost =  fields.Float('Shipping Cost', readonly=True)
    total_weight_net = fields.Float('Net Weight', digits=dp.get_precision('Stock Weight'),
        store=True, readonly=True, compute='_total_weight_net')
    carrier_id = fields.Many2one("delivery.carrier", "Delivery Carrier", help="The Carrier or Logistics Company")
    sale_id = fields.Many2one('sale.order', 'Sale Order', readonly=True, help="Source sales order.")
    picking_id = fields.Many2one('stock.picking', 'Picking Order', readonly=True, help="Source Delivery Picking Order.")
    carrier_contact = fields.Many2one("res.partner", "Carrier Contact", help="Contact Info for Carrier  responsible for Shipping")

    ship_service = fields.Char('Ship Service', size=128, readonly=True)
    ship_income_account_id = fields.Many2one('account.account', 'Shipping Account', readonly=True,
                                          help='This account represents the g/l account for booking shipping income.')
   
   
    def finalize_invoice_move_lines(self,move_lines):
        """
        finalize_invoice_move_lines(cr, uid, invoice, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an invoice, for special cases.
        Args:
            invoice: browsable record of the invoice that is generating the move lines
            move_lines: list of dictionaries with the account.move.lines (as for create())
        Returns:
            The (possibly updated) final move_lines to create for this invoice
        """
        move_lines = super(account_invoice, self).finalize_invoice_move_lines(move_lines)
        for inv in self:
            invoice=inv
            if invoice.type == "out_refund":
                account = invoice.account_id.id
            else:
                account = invoice.ship_income_account_id.id
            if invoice.type in ('out_invoice','out_refund')  and account and invoice.shipcharge:
                lines1 = {
                    'analytic_account_id': False,
                    'tax_code_id': False,
                    'analytic_lines': [],
                    'tax_amount': False,
                    'name': 'Shipping Charge',
                    'ref': '',
                    'currency_id': False,
                    'credit': invoice.shipcharge,
                    'product_id': False,
                    'date_maturity': False,
                    'debit': False,
                    'date': time.strftime("%Y-%m-%d"),
                    'amount_currency': 0,
                    'product_uom_id':  False,
                    'quantity': 1,
                    'partner_id': invoice.partner_id.id,
                    'account_id': account
                }
                move_lines.append((0, 0, lines1))
                has_entry = False
                for move_line in move_lines:
                    journal_entry = move_line[2]
                    if journal_entry['account_id'] == invoice.partner_id.property_account_receivable.id:
                        journal_entry['debit'] += invoice.shipcharge
                        has_entry = True
                        break
                if not has_entry:       # If debit line does not exist create one
                    lines2 = {
                        'analytic_account_id': False,
                        'tax_code_id': False,
                        'analytic_lines': [],
                        'tax_amount': False,
                        'name': '/',
                        'ref': '',
                        'currency_id': False,
                        'credit': False,
                        'product_id': False,
                        'date_maturity': False,
                        'debit': invoice.shipcharge,
                        'date': time.strftime("%Y-%m-%d"),
                        'amount_currency': 0,
                        'product_uom_id': False,
                        'quantity': 1,
                        'partner_id': invoice.partner_id.id,
                        'account_id': invoice.partner_id.property_account_receivable.id
                    }
                    move_lines.append((0, 0, lines2))
        return move_lines
    
    @api.model
    def _amount_shipment_tax(self, shipment_taxes, shipment_charge):
        val = 0.0
        for c in self.env['account.tax'].compute_all(shipment_taxes, shipment_charge, 1)['taxes']:
            val += c.get('amount', 0.0)
        return val
    
class invoice_line(models.Model):
    """Add the net weight to the object "Invoice Line"."""
    _inherit = 'account.invoice.line'
    
       
    def _line_weight_net(self):
        """Compute the net weight of the given Invoice Lines."""
        
        if self.product_id:
            self.weight_net += self.product_id.weight_net * self.quantity 
    

    weight_net = fields.Float(string='Net Weight', help="The net weight in Kg.", digits=dp.get_precision('Stock Weight'),
        store=True, readonly=True, compute='_line_weight_net')

#TODO Taxes currently not calculated for Shipping, Tax ids have not been defined and would need to be added to the Delivery Carrier shipping methods    
class account_invoice_tax_inherit(models.Model):
    _inherit = "account.invoice.tax"

    @api.model
    def compute(self, invoice):
        tax_grouped = super(account_invoice_tax_inherit, self).compute(invoice)
        tax_obj = self.env['account.tax']
        currency = invoice.currency_id.with_context(date=invoice.date_invoice or fields.Date.context_today(invoice))
        company_currency = invoice.company_id.currency_id
        

        tax_ids = [] #invoice.ship_method_id and invoice.ship_method_id.shipment_tax_ids
        if tax_ids:
            for tax in tax_obj.compute_all( tax_ids, invoice.shipcharge, 1)['taxes']:
                val = {}
                val.update({
                    'invoice_id': invoice.id,
                    'name': tax['name'],
                    'amount': tax['amount'],
                    'manual': False,
                    'sequence': tax['sequence'],
                    'base': tax['price_unit'] * 1
                    })
                if invoice.type in ('out_invoice','in_invoice'):
                    val.update({
                        'base_code_id': tax['base_code_id'],
                        'tax_code_id': tax['tax_code_id'],
                        'base_amount': currency.compute( val['base'] * tax['base_sign'],company_currency, round=False),
                        'tax_amount': currency.compute(  val['amount'] * tax['tax_sign'],company_currency, round=False),
                        'account_id': tax['account_collected_id'] or self.account_id.id
                        })
                else:
                    val.update({
                        'base_code_id': tax['ref_base_code_id'],
                        'tax_code_id': tax['ref_tax_code_id'],
                        'base_amount': currency.compute( val['base'] * tax['ref_base_sign'], company_currency,round=False),
                        'tax_amount': currency.compute( val['amount'] * tax['ref_tax_sign'],  company_currency, round=False),
                        'account_id': tax['account_paid_id'] or self.account_id.id
                        })

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

            for t in tax_grouped.values():
                t['base'] = currency.round( t['base'])
                t['amount'] = currency.round(t['amount'])
                t['base_amount'] = currency.round(t['base_amount'])
                t['tax_amount'] = currency.round(t['tax_amount'])
                
        return tax_grouped
    
 

    