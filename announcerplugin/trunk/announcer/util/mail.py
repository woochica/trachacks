# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from base64 import b32encode, b32decode

try:
    from email.header import Header
except:
    from email.Header import Header

from announcer.util import get_target_id

MAXHEADERLEN = 76


def next_decorator(event, message, decorates):
    """
    Helper method for IAnnouncerEmailDecorators.  Call the next decorator
    or return.
    """
    if decorates and len(decorates) > 0:
        next = decorates.pop()
        return next.decorate_message(event, message, decorates)

def set_header(message, key, value, charset=None):
    if not charset:
        charset = message.get_charset() or 'ascii'
    # Don't encode pure ASCII headers.
    try:
        value = Header(value, 'ascii', MAXHEADERLEN-(len(key)+2))
    except:
        value = Header(value, charset, MAXHEADERLEN-(len(key)+2))
    if message.has_key(key):
        message.replace_header(key, value)
    else:
        message[key] = value
    return message

def uid_encode(projurl, realm, target):
    """
    Unique identifier used to track resources in relation to emails.

    Returns a base32 encode UID string.  projurl included to avoid
    Message-ID collisions.  Returns a base32 encode UID string.
    Set project_url in trac.ini for proper results.
    """
    uid = ','.join((projurl, realm, get_target_id(target)))
    return b32encode(uid.encode('utf8'))

def uid_decode(encoded_uid):
    """
    Returns a tuple of projurl, realm, id and change_num.
    """
    uid = b32decode(encoded_uid).decode('utf8')
    return uid.split(',')

def msgid(uid, host='localhost'):
    """
    Formatted id for email headers.
    ie. <UIDUIDUIDUIDUID@localhost>
    """
    return "<%s@%s>"%(uid, host)
