# -*- coding: utf-8 -*-


{
    'name': 'Payment Authorize.net Extended',
    'version': '1.0',
    'category': '',
    'complexity': "Medium",
    'category': 'Payment',
    'description': """
        
        Extends functionality to Authorize.net payment  
    """,
    'author': 'GoContractPro LLC, Stephen Levenhagen',
    'website': 'gocontractpro.com',
    'depends': ["website_sale_delivery","payment_authorize"],
    'init_xml': [],
    'data': ['views/payment_aquirer.xml'],
    'demo_xml': [],
    'test': [
    ],
    'qweb' : [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
