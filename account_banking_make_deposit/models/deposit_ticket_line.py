# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from openerp import api, fields, models, _
from openerp.exceptions import UserError

class deposit_ticket_line(models.Model):
    _name = "deposit.ticket.line"
    _description = "Deposit Ticket Line"
    
    name = fields.Char(
            'Name',
            size=64,
            required=True,
            help="Derived from the related Journal Item."
        )
    ref = fields.Char(
            'Reference',
            help="Derived from related Journal Item."
        )
    partner_id = fields.Many2one(
            'res.partner',
            string='Partner',
            help="Derived from related Journal Item."
        )
    amount = fields.Float(
            string='Amount',
            help="Derived from the 'debit' amount from related Journal Item."
        )
    date = fields.Date(
            string='Date',
            required=True,
            help="Derived from related Journal Item."
        )
    deposit_id = fields.Many2one(
            'deposit.ticket',
            string='Deposit Ticket',
            required=True,
            ondelete='cascade'
        )
    company_id = fields.Many2one('res.company',
            string='Company',
            related='deposit_id.company_id',
            readonly=True,
            help="Derived from related Journal Item."
        )
    move_line_id = fields.Many2one(
            'account.move.line',
            string='Journal Item',
            help="Related Journal Item."
        )
  
    @api.multi
    def create(self, vals):
        # Any Line cannot be manually added. Use the wizard to add lines.
        
        if not vals.get('move_line_id', False):
            
            raise UserError(
                _(
                    'You cannot add any new deposit ticket line '
                    'manually as of this revision! '
                    'Please use the button \"Add Deposit '
                    'Items\" to add deposit ticket line!'
                )
            )
        return super(deposit_ticket_line, self).create(vals)

    @api.multi
    def unlink(self):
        """
        Set the 'draft_assigned' field to False for related account move
        lines to allow to be entered for another deposit.
        """
        account_move_line_obj = self.env['account.move.line']
        move_line_ids = [
            line.move_line_id.id
            for line in self
        ]
        account_move_line_obj.write(move_line_ids, {'draft_assigned': False})
        return super(deposit_ticket_line, self).unlink()
