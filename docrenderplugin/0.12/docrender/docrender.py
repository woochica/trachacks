# -*- coding: utf-8 -*-
#
# Copyright (C) 2004-2009 Edgewall Software
# Copyright (C) 2004 Daniel Lundin
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.org/wiki/TracLicense.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://trac.edgewall.org/log/.
#
# Author: Boris Savelev <boris.savelev@gmail.com>

"""Trac support for DOC format
"""

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer

class DocRenderer(Component):
    """Renders doc files as HTML."""
    implements(IHTMLPreviewRenderer)

    def get_quality_ratio(self, mimetype):
        if mimetype == "application/msword":
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, rev=None):
        if hasattr(content, 'read'):
            content = content.read()
        from subprocess import Popen, PIPE
        from trac.util.text import to_unicode
        import os
        from tempfile import mkstemp
        temp = mkstemp()
        f = os.fdopen(temp[0], "w")
        filename = temp[1]
        f.write(content)
        f.close()
        cmd = [u"/usr/bin/wvWare",u"--charset=utf8", u"%s" % filename]
        self.log.debug('Trying to render HTML preview for doc file %s' % filename)
        content_export = Popen(cmd, stdout=PIPE).communicate()[0]
        os.unlink(filename)
        return to_unicode(content_export)
