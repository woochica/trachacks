# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Boris Savelev
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

"""
    Trac support for DOC, PDF format
"""

from trac.core import *
from trac.config import Option
from trac.mimeview.api import IHTMLPreviewRenderer

class DocRenderer(Component):
    """Renders doc, pdf files as HTML."""
    implements(IHTMLPreviewRenderer)

    socket = Option('attachment', 'ooo_socket', '',
                       'socket url to OOo')

    mimetypes_doc = [
        "application/msword",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    mimetypes_xls = [
        "application/excel",
        "application/vnd.ms-excel",
    ]


    def get_quality_ratio(self, mimetype):
        if mimetype in self.mimetypes_doc:
            self.mime='doc'
            return 8
        elif mimetype in self.mimetypes_xls:
            self.mime='xls'
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
        tmp_filename = temp[1]
        f.write(content)
        f.close()
        content_export = ""
        cmd = []
        mimetype_clean = mimetype.split(';')[0].strip()
        charset = mimetype.split(';')[1].split('=')[1].strip() or 'utf-8'
        cmd = ['/usr/local/bin/ooextract.py', "--connection-string=%s" % self.socket,"--format=%s" % self.mime,"--stdout", u"%s" % tmp_filename]
        if cmd:
            self.log.debug('Trying to render HTML preview for %s file %s using cmd: %s' % (mimetype, filename, " ".join(cmd)))
            content_export = Popen(cmd, stdout=PIPE).communicate()[0]
        else:
            self.log.debug('Empty command! Mimetype is %s' % mimetype)
        os.unlink(tmp_filename)
        return to_unicode(content_export)
