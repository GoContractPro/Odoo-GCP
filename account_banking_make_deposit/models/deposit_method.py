# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import api, fields, models, _

class deposit_method(models.Model):
    _name = "deposit.method"
    _description = "Deposit Method"
    
    name = fields.Char(
            'Name', size=64,
            required=True,
            help='Name of the method used for deposit'
        )

