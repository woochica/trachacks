# -*- coding: iso-8859-1 -*-
#
# Copyright (C) 2004-2006 Edgewall Software
# Copyright (C) 2009 Piers O'Hanlon
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# For trac 0.9.3
# To enable this extension you need to add 
#                      'trac.mimeview.manpage', 
# to the following file - to the default_components variable:
#../db_default.py:440
# default_components = ('trac.About', 'trac.attachment', 
#
# Trac 0.11
# This package should now install using easy_setup
# 
# If you don't use setuptools then Add to the following to:
# /usr/lib/python2.5/site-packages/Trac-0.11.egg-info/entry_points.txt, SOURCES.txt
#	trac.mimeview.manpage = trac.mimeview.manpage
# Also one needs full groff install for html conversion 
# aptitude install groff
#
# Author: Piers O'Hanlon <p.ohanlon@cs.ucl.ac.uk>

"""Trac support for nroff man pages
See GNU groff for more info: http://www.gnu.org/software/groff/
"""

from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer, content_to_unicode
from trac.util import escape, NaivePopen, Deuglifier

class ManPageRenderer(Component):
    """Renders nroff man page as HTML."""
    implements(IHTMLPreviewRenderer)

    expand_tabs = False
    #returns_source = True

    def get_quality_ratio(self, mimetype):
        if mimetype in ['application/x-troff-man', 'application/x-troff']:
            return 8
        return 0

    def render(self, req, mimetype, content, filename=None, rev=None):
	#cmdline = '/usr/bin/groff -Tutf8 -a -mandoc '
	cmdline = self.config.get('mimeviewer', 'groff_path')
	if len(cmdline) == 0:
	  cmdline = '/usr/bin/groff'
	self.env.log.debug("groff got command line: %s" % cmdline)
	cmdline += ' -Thtml -P -r -P -l -mandoc '
        self.env.log.debug("groff command line: %s" % cmdline)

        content = content_to_unicode(self.env, content, mimetype)
	cont=content.encode('utf-8')
        np = NaivePopen(cmdline, cont, capturestderr=1)
        if np.errorlevel or np.err:
            err = 'Running (%s) failed: %s, %s.' % (cmdline, np.errorlevel,
                                                    np.err)
            raise Exception, err

        return np.out

