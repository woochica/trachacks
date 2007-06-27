# -*- coding: utf-8 -*-
#
# Copyright (C) 2004-2006 Edgewall Software
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
# Author: Daniel Lundin <daniel@edgewall.com>

"""A wiki-processor for interpreting notes mail to wrap header pars inside a box.
The box will have a legend (dates).
"""

import re
from trac.wiki import wiki_to_html
from trac.core import *
from trac.mimeview.api import IHTMLPreviewRenderer


STYLE  = 'margin-top: 2px; color:black; background-color:%s; '\
         'border: solid black 1px'
COLOR  = 'white'

class LotusNotesRenderer(Component):
    """Renders Lotus Notes mail in beautiful HTML format."""
    implements(IHTMLPreviewRenderer)

    def get_quality_ratio(self, mimetype):
        if mimetype == 'text/x-notes':
            return 8
        return 0

    def render(self, req, mimetype, content, filename=None, rev=None):
        content = content.lstrip();
        if (0 == len(content)):
            return ""
        
        html = ""
        match = re.search(r"^(from:?\s+?)?(.*)$\s+?^(sent:?\s*)?(.*)$\s+?^\s*to:?\s+?(.*)$\s+?^(\s*cc:?\s+?(.*)$\s+?)?^\s*subject:?\s+(.*)$", content, re.IGNORECASE | re.MULTILINE)
        if match:
            if (-1 == match.start(1)):
                pre_content = match.string[0:match.start(2)]
            else:
                pre_content = match.string[0:match.start(1)]
            from1 = match.group(2)
            date = match.group(4)
            to = match.group(5)
            if (-1 != match.start(6)) and (-1 != match.start(7)):
                cc = match.group(7)
            else:
                cc = ''
            subject = match.group(8)
            content = match.string[match.end(8):]
        else:
            return wiki_to_html(content, self.env, req, escape_newlines=True)
    
        html = '%s<br />'\
               '<fieldset style="%s">'\
               '<legend style="%s">%s</legend>'\
               'From: %s<br />'\
               'To: %s<br />' % (wiki_to_html(pre_content, self.env, req, escape_newlines=True),
                                 STYLE,
                                 STYLE,
                                 date,
                                 from1.replace("<", "&lt;"),
                                 to.replace("<", "&lt;"))
    
        if (0 < len(cc)):
            html += 'Cc: %s<br />' % cc.replace("<", "&lt;")
    
        html += 'Subject: %s<br />'\
                '</fieldset><br />'\
                '%s<br />' % (subject,
                              self.render(req, mimetype, content))
    
        return html

