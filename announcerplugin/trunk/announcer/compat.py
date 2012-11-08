# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Steffen Hoffmann
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Various classes and functions to provide backwards-compatibility with
previous versions of Python from 2.4 and Trac from 0.11 onwards.
"""

try:
    from trac.util.datefmt  import to_utimestamp
except ImportError:
    # Cheap fallback for Trac 0.11 compatibility.
    from trac.util.datefmt  import to_timestamp
    def to_utimestamp(dt):
        return to_timestamp(dt) * 1000000L

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
