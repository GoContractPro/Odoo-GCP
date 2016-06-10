# -*- coding: utf-8 -*-
#See LICENSE file for full copyright and licensing details.

from openerp import api, fields, models, _

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"
    
    analytic_lines = fields.One2many('account.analytic.line','invoice_line', string='Activities')