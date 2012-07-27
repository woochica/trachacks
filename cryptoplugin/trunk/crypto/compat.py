#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Steffen Hoffmann <hoff.st@web.de>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

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
