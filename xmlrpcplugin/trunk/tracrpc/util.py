# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009      ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import datetime
import time
import xmlrpclib

from trac.util.datefmt import utc

### PUBLIC

def to_xmlrpc_datetime(dt):
    """ Convert a datetime.datetime object to a xmlrpclib DateTime object """
    return xmlrpclib.DateTime(dt.utctimetuple())

def from_xmlrpc_datetime(data):
    """Return datetime (in utc) from XMLRPC datetime string (is always utc)"""
    t = list(time.strptime(data.value, "%Y%m%dT%H:%M:%S")[0:6])
    return apply(datetime.datetime, t, {'tzinfo': utc})

### INTERNAL / COMPAT

try:
    # Method only available in Trac 0.11.3 or higher
    from trac.util.text import exception_to_unicode
except ImportError:
    def exception_to_unicode(e, traceback=""):
        from trac.util.text import to_unicode
        message = '%s: %s' % (e.__class__.__name__, to_unicode(e))
        if traceback:
            from trac.util import get_last_traceback
            traceback_only = get_last_traceback().split('\n')[:-2]
            message = '\n%s\n%s' % (to_unicode('\n'.join(traceback_only)),
                                        message)
        return message

try:
    # Constant available from Trac 0.12dev r8612
    from trac.util.text import empty
except ImportError:
    empty = None
