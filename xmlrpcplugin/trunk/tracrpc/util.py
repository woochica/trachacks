# -*- coding: utf-8 -*-
"""
License: BSD

(c) 2005-2008 ::: Alec Thomas (alec@swapoff.org)
(c) 2009-2013 ::: www.CodeResort.com - BV Network AS (simon-code@bvnetwork.no)
"""

import sys

# Supported Python versions:
PY24 = sys.version_info[:2] == (2, 4)
PY25 = sys.version_info[:2] == (2, 5)
PY26 = sys.version_info[:2] == (2, 6)
PY27 = sys.version_info[:2] == (2, 7)

from trac.util.compat import any

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

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

def accepts_mimetype(req, mimetype):
    if isinstance(mimetype, basestring):
      mimetype = (mimetype,)
    accept = req.get_header('Accept')
    if accept is None :
        # Don't make judgements if no MIME type expected and method is GET
        return req.method == 'GET'
    else :
        accept = accept.split(',')
        return any(x.strip().startswith(y) for x in accept for y in mimetype)

def prepare_docs(text, indent=4):
    r"""Remove leading whitespace"""
    return text and ''.join(l[indent:] for l in text.splitlines(True)) or ''

from trac.util.datefmt import to_datetime, utc
try:
    # Micro-second support added to 0.12dev r9210
    from trac.util.datefmt import to_utimestamp, from_utimestamp
except ImportError:
    from trac.util.datefmt import to_timestamp
    to_utimestamp = to_timestamp
    from_utimestamp = lambda x: to_datetime(x, utc)
