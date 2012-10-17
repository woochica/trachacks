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

from trac.util.text import to_unicode
try:
    # Method only available in Trac 0.11.3 or higher.
    from trac.util.text import exception_to_unicode
except:
    def exception_to_unicode(e, traceback=False):
        """Convert an `Exception` to an `unicode` object.

        In addition to `to_unicode`, this representation of the exception
        also contains the class name and optionally the traceback.
        This replicates the Trac core method for backwards-compatibility.
        """
        message = '%s: %s' % (e.__class__.__name__, to_unicode(e))
        if traceback:
            from trac.util import get_last_traceback
            traceback_only = get_last_traceback().split('\n')[:-2]
            message = '\n%s\n%s' % (to_unicode('\n'.join(traceback_only)),
                                    message)
        return message

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

    Returns a base64 encode UID string.  projurl included to avoid
    Message-ID collisions.  Returns a base64 encode UID string.
    Set project_url in trac.ini for proper results.
    """
    if hasattr(target, 'id'):
        id = str(target.id)
    elif hasattr(target, 'name'):
        id = target.name
    else:
        id = str(target)
    uid = ','.join((projurl, realm, id))
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

