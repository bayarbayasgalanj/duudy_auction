# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import re

def verbose_numeric(amount):
    if type(amount) in (int, float):
        amount = '%.2f' % amount
    res = []
    result = u''
    # Форматаас болоод . -ын оронд , орсон байвал засна.
    amount = amount.replace(',','.')
    subamount = ''
    if '.' in amount:
        stramount = amount
        amount = stramount[:stramount.find('.')]
        subamount = stramount[stramount.find('.')+1:]
    place = 0
    i = 0
    length = len(amount)
    if length == 0 or float(amount) == 0:
        res.append(u'тэг ')
        if len(subamount) > 0 and float(subamount) >0 :
            result2 = verbose_numeric(subamount)
            res.append(result2[0])
        return res
   
    try :
        while i < length :
            c = length - i
            if c % 3 == 0 :
                c -= 3
            else :
                while c % 3 != 0 :
                    c -= 1
            place = c / 3
            i1 = length - c
            tmp = amount[i:i1]
            j = 0
            if tmp == '000' :
                i = i1
                continue
            while j < len(tmp) :
                char = int(tmp[j])
                p = len(tmp) - j
                if char == 1 :
                    if p == 3 :
                        result += u'нэг зуун '
                    elif p == 2 :
                        result += u'арван '
                    elif p == 1 :
                        result += u'нэг '
                elif char == 2 :
                    if p == 3 :
                        result += u'хоёр зуун '
                    elif p == 2 :
                        result += u'хорин '
                    elif p == 1 :
                        result += u'хоёр '
                elif char == 3 :
                    if p == 3 :
                        result += u'гурван зуун '
                    elif p == 2 :
                        result += u'гучин '
                    elif p == 1 :
                        result += u'гурван '
                elif char == 4 :
                    if p == 3 :
                        result += u'дөрвөн зуун '
                    elif p == 2 :
                        result += u'дөчин '
                    elif p == 1 :
                        result += u'дөрвөн '
                elif char == 5 :
                    if p == 3 :
                        result += u'таван зуун '
                    elif p == 2 :
                        result += u'тавин '
                    elif p == 1 :
                        result += u'таван '
                elif char == 6 :
                    if p == 3 :
                        result += u'зургаан зуун ' 
                    elif p == 2 :
                        result += u'жаран '
                    elif p == 1 :
                        result += u'зургаан '
                elif char == 7 :
                    if p == 3 :
                        result += u'долоон зуун '
                    elif p == 2 :
                        result += u'далан '
                    elif p == 1 :
                        result += u'долоон '
                elif char == 8 :
                    if p == 3 :
                        result += u'найман зуун '
                    elif p == 2 :
                        result += u'наян '
                    elif p == 1 :
                        result += u'найман '
                elif char == 9 :
                    if p == 3 :
                        result += u'есөн зуун '
                    elif p == 2 :
                        result += u'ерин '
                    elif p == 1 :
                        result += u'есөн '
                
                j += 1
            # -------- end while j < len(tmp)
            if place == 3 :
                result += u'тэрбум '
            elif place == 2 :
                result += u'сая '
            elif place == 1 :
                if int(amount[i1:-1]) == 0:
                    if int(subamount) == 0:
                        result += u'мянган '
                    else:
                        result += u'мянга '
                else:
                    result += u'мянга '
            i = i1
        res.append(result)
        # ---------- end while i < len(amount)
    except Exception as e:
        return e
    if len(subamount) > 0 and float(subamount) > 0 :
        result2 = verbose_numeric(subamount)
        res.append(result2[0])
#        print 'result2 %s' %result2[0]
#        print 'res %s' %res
#        print 'len %s' %len(res)

    return res

def comma_me(value, decimals=2, separator=","):
    """ transform a number into a number with thousand separators """
    if separator == ".":
        separator = "'"
    if type(value) is int: 
        value = str(('%.'+str(decimals)+'f')%float(value))
    elif  type(value) is float :
        value = str(('%.'+str(decimals)+'f')%value)
    else :
        value = str(value)
    orig = value
    new = re.sub("^(-?\d+)(\d{3})", "\g<1>"+separator+"\g<2>", value)
    """Доорх comment-ийг устгаж болохгүй дараа ашиглагдаж магадгүй"""
#        if '.' in new and int(new[-decimals:]) == 0:
#            new = new[:-(decimals+1)]
#            orig = orig[:-(decimals+1)]
    if orig == new:
        return new
    else:
        return comma_me(new, decimals=decimals, separator=separator)
    
def convert_curr(list, curr, div_curr):
    """Convert currency """
    result = u''
    if list[0]:
        result += u'( %s ' %list[0]
        if len(list) == 1:
            result += u'%s )' %curr
        else:
            result += u'%s ' %curr
    if len(list) == 2:
        result += list[1]
        result += u'%s )' %div_curr
    return result
