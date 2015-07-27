# -*- coding: utf-8 -*-
{
    'name': 'NPG Product Stock Value by Location',
    'version': '1.0',
    'category': '',
    "sequence": 14,
    'complexity': "easy",
    'category': 'Hidden',
    'description': """
        Adds functionality to display stock level by location on Products
        Extends Stock Location functionality
        
    """,
    'author': 'NovaPoint Group Inc',
    'website': 'www.novapointgroup.com',
    'depends': ['stock','stock_location'],
    'init_xml': [],
    'data': [
        "views/stock_location.xml"
    ],
    'demo_xml': [],
    'test': [
    ],
    'qweb' : [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
