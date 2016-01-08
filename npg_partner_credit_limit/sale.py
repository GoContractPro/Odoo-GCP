# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 NovaPoint Group INC (<http://www.novapointgroup.com>)
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

#-*- coding:utf-8 -*-
from openerp import models, api, _
from openerp.exceptions import Warning


class sale_order(models.Model):
    _inherit = "sale.order"

    @api.one
    def action_wait(self):
        self.check_limit()
        return super(sale_order, self).action_wait()

    @api.one
    def check_limit(self):

        if self.order_policy == 'prepaid':
            return True

        # We sum from all the sale orders that are aproved, the sale order
        # lines that are not yet invoiced
        domain = [('order_id.partner_id', '=', self.partner_id.id),
                  ('invoiced', '=', False),
                  ('order_id.state', 'not in', ['draft', 'cancel', 'sent'])]
        order_lines = self.env['sale.order.line'].search(domain)
        none_invoiced_amount = sum([x.price_subtotal for x in order_lines])

        # We sum from all the invoices that are in draft the total amount
        domain = [
            ('partner_id', '=', self.partner_id.id), ('state', '=', 'draft')]
        draft_invoices = self.env['account.invoice'].search(domain)
        draft_invoices_amount = sum([x.amount_total for x in draft_invoices])

        available_credit = self.partner_id.credit_limit - \
            self.partner_id.credit - \
            none_invoiced_amount - draft_invoices_amount

        if self.amount_total > available_credit:
            msg = "No one can confirm the order as the customer has insufficient credit."
            raise Warning(_(msg))
            return False
        return True