# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 NovaPoint Group LLC (<http://www.novapointgroup.com>)
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

# can be used for numbers as large as 999 vigintillion
# (vigintillion --> 10 to the power 60)
# tested with Python24      vegaseat      07dec2006

def int2word(n):
    """
    convert an integer number n into a string of English words
    """
    # break the number into groups of 3 digits using slicing
    # each group representing hundred, thousand, million, billion, ...
    if not n:
        return 'Zero '
    n3 = []
    r1 = ""
    # create numeric string
    ns = str(n)
    for k in range(3, 33, 3):
        r = ns[-k:]
        q = len(ns) - k
        # break if end of ns has been reached
        if q < -2:
            break
        else:
            if  q >= 0:
                n3.append(int(r[:3]))
            elif q >= -1:
                n3.append(int(r[:2]))
            elif q >= -2:
                n3.append(int(r[:1]))
        r1 = r
    nw = ""
    for i, x in enumerate(n3):
        b1 = x % 10
        b2 = (x % 100) // 10
        b3 = (x % 1000) // 100
        if x == 0:
            continue  # skip
        else:
            t = thousands[i]
        if b2 == 0:
            nw = ones[b1] + t + nw
        elif b2 == 1:
            nw = tens[b1] + t + nw
        elif b2 > 1:
            nw = twenties[b2] + ones[b1] + t + nw
        if b3 > 0:
            nw = ones[b3] + "hundred " + nw
    return nw

############# globals ################

ones = ["", "One ", "Two ", "Three ", "Four ", "Five ",
        "Six ", "Seven ", "Eight ", "Nine "]

tens = ["Ten ", "Eleven ", "Twelve ", "Thirteen ", "Fourteen ",
        "Fifteen ", "Sixteen ", "Seventeen ", "Eighteen ", "Nineteen "]

twenties = ["", "", "Twenty ", "Thirty ", "Forty ",
    "Fifty ", "Sixty ", "Seventy ", "Eighty ", "Ninety "]

thousands = ["", "Thousand ", "Million ", "Billion ", "Trillion ",
    "Quadrillion ", "Quintillion ", "Sextillion ", "Septillion ","Octillion ",
    "Nonillion ", "Decillion ", "Undecillion ", "Duodecillion ", "Tredecillion ",
    "Quattuordecillion ", "Sexdecillion ", "Septendecillion ", "Octodecillion ",
    "Novemdecillion ", "Vigintillion "]

def amount_to_words(num):
    # select an integer number n for testing or get it from user input
    res = ""
    if num < 0:
        res = "Negative "
        num = float(str(num)[1:])
    if num == 0: return 'Zero'
    else:
        n = str(num).split('.')
        return res + int2word(int(n[0])) + 'and ' + (len(n) > 1 and int(n[1]) and str((num - int(num)) * 100).split('.')[0] or 'no') + '/100s'
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: