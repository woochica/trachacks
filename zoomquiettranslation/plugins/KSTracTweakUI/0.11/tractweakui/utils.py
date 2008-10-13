# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         utils.py
# Purpose:      The KssopReport Trac plugin utils model module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------

import sys, os
import re
import time
import calendar
import urllib

from trac.web.chrome import *

calendar.setfirstweekday(calendar.MONDAY)

SECPERDAY = 60 * 60 * 24
SECPERWEEK = 60 * 60 * 24 * 7

def queryDb(sqlString, env):
    """ execute sql query
        return:
            rows
    """
    db = env.get_db_cnx()
    cursor = db.cursor()
    cursor.execute(sqlString)
    rows = cursor.fetchall()
    return rows

def encode_url(path, params):
    params_encoded = {}
    for k, v in params.items():
        if isinstance(v, unicode):
            v = v.encode("utf=8")
        params_encoded[k] = v
        
    return path + "?" + urllib.urlencode(params_encoded)

#----------------------------------------------------------------------------
def getDateFromStr(dateStr):
    """ convert 2008-01-01 to int
    """
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y%m%d",
        "%y-%m-%d",
        "%y/%m/%d",
        "%y.%m.%d",
        "%y%m%d",
        "%m/%d/%Y",
    ]
    
    timeTuple = None
    for format in formats:
        try:
            timeTuple = time.strptime(dateStr, format)
            return int(time.mktime(timeTuple))
        except:
            continue
    if not timeTuple:
        return None

def formatDateFull(t):
    """ convert int to 2008-01-01
    """
    try:
        t = int(float(t))
    except:
        return ""
    return time.strftime("%Y-%m-%d", time.localtime(t))

def formatTimeFull(t):
    try:
        t = int(t)
    except:
        return ""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t))

def formatDateCompact(t):
    return time.strftime("%y%m%d", time.localtime(t))


def formatWeek(t):
    return time.strftime("%Y-%W-%w", time.localtime(t))

