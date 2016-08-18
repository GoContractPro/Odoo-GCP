# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 NovaPoint Group LLC (<http://www.verts.co.in>)
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
from lxml import etree
import re


def dictlist(node):
    res = {}
    node_tag = re.findall(r'}(\w*)', node.tag)
    node_tag = node_tag[0]
    res[node_tag] = []
    xmltodict(node, res[node_tag])
    reply = {}
    reply[node_tag] = res[node_tag]
    return reply

def xmltodict(node, res):
    rep = {}
    node_tag = re.findall(r'}(\w*)', node.tag)
    node_tag = node_tag[0]
    if len(node):
        #n = 0
        for n in list(node):

            rep[node_tag] = []
            value = xmltodict(n, rep[node_tag])
            if len(n):
                n_tag = re.findall(r'}(\w*)', n.tag)
                n_tag = n_tag[0]
                value = rep[node_tag]
                res.append({n_tag:value})
            else :

                res.append(rep[node_tag][0])

    else:
        value = {}
        value = node.text
        res.append({node_tag:value})

    return

def main(xml_string):
    tree = etree.fromstring(xml_string)
    res = dictlist(tree)
    return res

if __name__ == '__main__' :
    main()
