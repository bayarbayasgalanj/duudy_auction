# -*- encoding: utf-8 -*-
##############################################################################
#
#   MANAGEWALL LLC
#
#
##############################################################################

def verbose_format(amount,currency=False):
    if type(amount) !=str :
        amount = str(amount)
    result = u''
    BUTARHAI = True
    i = 0
    #length = len(amount)
    # Форматаас болоод . -ын оронд , орсон байвал засна.
    stramount = amount.replace(',','.')
#    print "stramount ",stramount
    if '.' in amount:
        amount = stramount[:stramount.find('.')]
        subamount = stramount[stramount.find('.')+1:]
        if len(subamount)==1:
            subamount=str(int(subamount)*10)
#         print "subamount ",subamount
    else :
        amount = stramount
        subamount = u''
    length = len(amount)
    if length == 0 or float(amount) == 0:
        return ''
    place = 0
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
                        if len(result)==0:
                            result += u'нэг '
                        else:
                            result += u'нэгэн '
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
                        result += u'ерэн '
                    elif p == 1 :
                        result += u'есөн '
                
                j += 1
            # -------- end while j < len(tmp)
            if place == 3 :
                result += u'тэрбум '
            elif place == 2 :
                result += u'сая '
            elif place == 1 :
                result += u'мянга '
            i = i1
        # ---------- end while i < len(amount)
    except Exception as e  :
        return e
    if len(subamount) > 0 and float(subamount) > 0 :
        result2 = verbose_format(subamount,currency)
        BUTARHAI = False
        if currency and currency.name=='USD':
            result2 = result2.replace(u'доллар', u'цент')
            result += u' доллар %s' % result2
        elif currency and currency.name=='CNY':
            result2 = result2.replace(u'юань', u'мо')
            result += u' юань %s' % result2
        else:
            result2 = result2.replace(u'төгрөг', u'мөнгө')
            result += u' төгрөг %s' % result2
    if BUTARHAI:
        if currency and currency.name=='USD':
            result += u' доллар'
        elif currency and currency.name=='CNY':
            result += u' юань ' 
        else:
            result += u' төгрөг'
            
    num = result
    if u"мянга  төгрөг" in num:
      result = num.replace(u"мянга  төгрөг",u"мянган  төгрөг")
    elif u"мянга  доллар" in num:
      result = num.replace(u"мянга  доллар",u"мянган  доллар")
    elif  u"мянга  юань" in num:
      result = num.replace(u"мянга  юань",u"мянган  юань")
    else:
      result = num

    return result

