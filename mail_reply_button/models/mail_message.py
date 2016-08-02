# -*- coding: utf-8 -*-
from openerp import api, fields, models

class MailMessage(models.Model):

    _inherit = 'mail.message'

    reply_parent_id = fields.Integer('Reply Parent ID' , default=0)
    
    @api.multi
    def message_format(self):
        """ Get the message values in the format for web client. Since message values can be broadcasted,
            computed fields MUST NOT BE READ and broadcasted.
            :returns list(dict).
             Example :
                {
                    'body': HTML content of the message
                    'model': u'res.partner',
                    'record_name': u'Agrolait',
                    'attachment_ids': [
                        {
                            'file_type_icon': u'webimage',
                            'id': 45,
                            'name': u'sample.png',
                            'filename': u'sample.png'
                        }
                    ],
                    'needaction_partner_ids': [], # list of partner ids
                    'res_id': 7,
                    'tracking_value_ids': [
                        {
                            'old_value': "",
                            'changed_field': "Customer",
                            'id': 2965,
                            'new_value': "Axelor"
                        }
                    ],
                    'author_id': (3, u'Administrator'),
                    'email_from': 'sacha@pokemon.com' # email address or False
                    'subtype_id': (1, u'Discussions'),
                    'channel_ids': [], # list of channel ids
                    'date': '2015-06-30 08:22:33',
                    'partner_ids': [[7, "Sacha Du Bourg-Palette"]], # list of partner name_get
                    'message_type': u'comment',
                    'id': 59,
                    'subject': False
                    'is_note': True # only if the subtype is internal
                }
        """
        message_values = self.read([
            'id', 'body', 'date', 'reply_parent_id','author_id', 'email_from',  # base message fields
            'message_type', 'subtype_id', 'subject',  # message specific
            'model', 'res_id', 'record_name',  # document related
            'channel_ids', 'partner_ids',  # recipients
            'needaction_partner_ids',  # list of partner ids for whom the message is a needaction
            'starred_partner_ids',  # list of partner ids for whom the message is starred
        ])
        
        message_tree = dict((m.id, m) for m in self)
        self._message_read_dict_postprocess(message_values, message_tree)

        # add subtype data (is_note flag, subtype_description). Do it as sudo
        # because portal / public may have to look for internal subtypes
        subtypes = self.env['mail.message.subtype'].sudo().search(
            [('id', 'in', [msg['subtype_id'][0] for msg in message_values if msg['subtype_id']])]).read(['internal', 'description'])
        subtypes_dict = dict((subtype['id'], subtype) for subtype in subtypes)
        for message in message_values:
            message['is_note'] = message['subtype_id'] and subtypes_dict[message['subtype_id'][0]]['internal']
            message['subtype_description'] = message['subtype_id'] and subtypes_dict[message['subtype_id'][0]]['description']
        return message_values
