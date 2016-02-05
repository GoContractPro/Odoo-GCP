# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# from openerp.osv import orm, fields
from openerp import fields, models


class account_move_line(models.Model):

    """Account move line."""

    _inherit = 'account.move.line'
    draft_assigned = fields.Boolean(
            string='Draft Assigned',
            help=(
                "This field is checked when the move line is assigned "
                "to a draft deposit ticket. The deposit ticket is not "
                "still completely processed"
            ),
        )
    deposit_id= fields.Many2one(
            'deposit.ticket',
            string='Deposit Ticket'
        )
  
