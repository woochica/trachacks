# -*- Mode: Python -*-
# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

# Copyright (C) 2007 Thomas Vander Stichele <thomas at apestaart dot org>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer
#    in this position and unchanged.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from trac.core import Component, implements
from trac.web import api, chrome

import time

class TracKeywordsComponent(Component):
    """
    This component allows you to add from a configured list
    of keywords to the Keywords entry field.

    To use it, enable the component in trac's configuration, then
    add the line:
        <xi:include "keywords.html" />
    which will insert a field set.

    The recommended place to put this is right after
    the "properties" field set.

    The list of keywords can be configured in a [keywords] section in the
    trac configuration file.  Syntax is:

        keyword = description

    The description will show up as a tooltip when you hover over the keyword.
    """
    
    implements(api.IRequestFilter)
    implements(chrome.ITemplateProvider)
    
    def __init__(self):
        self.keywords = self._get_keywords()

    ### IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('ticket.html', 'wiki.html'):
            data['keywords'] = self.keywords
        return template, data, content_type

    ### ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return []

    def get_templates_dirs(self): 
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    ### Internal methods
    
    def _get_keywords(self):
        if not 'keywords' in self.env.config.sections():

            # return a default set of keywords to show the plug-in works
            return [
                ('patch', 'has a patch attached'),
                ('easy',  'easy to fix, good for beginners'),
            ]

        res = []
        section = self.env.config['keywords']
        for keyword in section:
            res.append((keyword, section.get(keyword)))

        return res
