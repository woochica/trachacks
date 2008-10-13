# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         utils.py
# Purpose:      The MMV admin Trac plugin utils module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------


"""Automated upgrades for the MMV database tables, and other data stored
in the Trac environment."""

import os
import sys
import time

SECPERDAY = 60 * 60 * 24

def dueday(due):
    """merge due time as WorkDay
    """
    #print due,due[-1:]
    if 'd'==due[-1:]:
        return float(due[:-1])
    elif 'w'==due[-1:]:
        return float(due[:-1])*5
    elif 'm'==due[-1:]:
        return float(due[:-1])*20
    else:
        #usage h
        return float(0.5)

def stripMilestoneName(m):
    # strip milestone name
    mm = []
    for s in m.split("."):
        try:
            s.encode("ascii")
            mm.append(s)
        except:
            break
    return str(".".join(mm))

def formatDateFull(t):
    return t and time.strftime("%Y/%m/%d", time.localtime(t)) or ""

def formatDateCompact(t):
    return time.strftime("%y%m%d", time.localtime(t))

def getDateFromStr(dateStr):
    try:
        timeTuple = time.strptime(dateStr, "%Y/%m/%d")
        timeSec = time.mktime(timeTuple)
        return int(timeSec + 1)
    except:
        return None
