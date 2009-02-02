# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------
# Name:         upgrades.py
# Purpose:      The ticket template Trac plugin upgrade module
#
# Author:       Richard Liao <richard.liao.i@gmail.com>
#
#----------------------------------------------------------------------------


"""Automated upgrades for the tt database tables, and other data stored
in the Trac environment."""

import os
import sys
import time
import base64
from stat import *

ENV = None

def add_tt_table(env, db):
    """Migrate from template files to db."""
    global ENV
    
    ENV = env
    
    cursor = db.cursor()


    # detect existing templates files
    allTmpls = _findAllTmpls()
    allTmpls.sort(_cmp)

    # import into db
    for tt_name in allTmpls:
        tt_text = _loadTemplateText(tt_name)
        modi_time = _getMTime(tt_name)
        
        from tickettemplate.model import TT_Template
        TT_Template.insert(ENV, tt_name, tt_text, modi_time)

    # base64
    # detect existing templates files
    allTmpls = _findAllTmplsBase64()
    allTmpls.sort(_cmpBase64)

    # import into db
    for tt_name in allTmpls:
        tt_text = _loadTemplateTextBase64(tt_name)
        modi_time = _getMTimeBase64(tt_name)
        
        from tickettemplate.model import TT_Template
        tt_name = base64.decodestring(tt_name).decode("utf-8")
        TT_Template.insert(ENV, tt_name, tt_text, modi_time)
    
    
def _cmp(tt_name1, tt_name2):
    modi_time1 = _getMTime(tt_name1)
    modi_time2 = _getMTime(tt_name2)
    
    if modi_time1 < modi_time2:
        return 1
    elif modi_time1 > modi_time2:
        return -1
    else:
        return 0
    
def _cmpBase64(tt_name1, tt_name2):
    modi_time1 = _getMTimeBase64(tt_name1)
    modi_time2 = _getMTimeBase64(tt_name2)
    
    if modi_time1 < modi_time2:
        return 1
    elif modi_time1 > modi_time2:
        return -1
    else:
        return 0


def _getMTime(tt_name):
    tt_file = _getTTFilePath(tt_name)
    mtime = int(os.stat(tt_file)[ST_MTIME])
    return mtime

def _getMTimeBase64(tt_name):
    tt_file = _getTTFilePath(tt_name)
    mtime = int(os.stat(tt_file)[ST_MTIME])
    return mtime


def _findAllTmpls():
    """ find all templates in trac environment
    """
    global ENV
    allTmpls = []
    
    basePath = os.path.join(ENV.path, "templates")
    files = os.listdir(basePath)
    for file in files:
        if file.startswith("description_") and file.endswith(".tmpl"):
            tt_name_base64 = file.split("description_",1)[1].rsplit(".tmpl",1)[0]
            # if tt_name can't decode by base64, then it's normal name
            try:
                base64.decodestring(tt_name_base64).decode("utf-8")
                # skip this file
                continue
            except:
                allTmpls.append(tt_name_base64)
                
    return allTmpls

def _findAllTmplsBase64():
    """ find all templates in trac environment
    """
    global ENV
    
    allTmplsBase64 = []
    
    basePath = os.path.join(ENV.path, "templates")
    files = os.listdir(basePath)
    for file in files:
        if file.startswith("description_") and file.endswith(".tmpl"):
            tt_name_base64 = file.split("description_",1)[1].rsplit(".tmpl",1)[0]
            try:
                base64.decodestring(tt_name_base64).decode("utf-8")
            except:
                continue
                
            allTmplsBase64.append(tt_name_base64)
    return allTmplsBase64
    
def _getTTFilePath(tt_name):
    """ get ticket template file path
    """
    global ENV
    tt_file_name = "description_%s.tmpl" % tt_name
    tt_file = os.path.join(ENV.path, "templates", tt_file_name)
    return tt_file

def _loadTemplateText(tt_name):
    """ load ticket template text from file.
    """
    tt_file = _getTTFilePath(tt_name)

    try:
        fp = open(tt_file,'r')
        tt_text = fp.read()
        fp.close()
    except:
        tt_text = ""
    return tt_text

def _loadTemplateTextBase64(tt_name):
    """ load ticket template text from file.
    """
    tt_file = _getTTFilePath(tt_name)

    try:
        fp = open(tt_file,'r')
        tt_text = fp.read()
        fp.close()
    except:
        tt_text = ""
    return tt_text


def add_tt_custom(env, db):
    """Add table tt_custom."""
    from tickettemplate.model import schema, schema_version, TT_Template
    from trac.db import DatabaseManager

    connector, _ = DatabaseManager(env)._get_connector()
    cursor = db.cursor()

    table = schema[1]
    for stmt in connector.to_sql(table):
        cursor.execute(stmt)
        
def alter_user_username(env, db):
    """Alter table tt_custom field from user to username."""
    # get current custom records
    cursor.execute("SELECT * FROM tt_custom")
    rows = cursor.fetchall()
    
    # refresh tt_custom schema
    cursor.execute("DROP TABLE tt_custom")
    
    add_tt_custom(env, db)
    
    # restore records
    for username, tt_name, tt_text in rows:
        cursor.execute("INSERT INTO tt_custom "
                       "(username,tt_name,tt_text) VALUES (%s,%s,%s)",
                       (username, tt_name, tt_text))
                       
    db.commit()

map = {
    1: [add_tt_table],
    2: [add_tt_custom],
    3: [alter_user_username],
}
