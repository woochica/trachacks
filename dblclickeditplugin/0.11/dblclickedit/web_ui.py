#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2009 Yijun Yu
#

import re

from trac.core import *
from trac.web.api import IRequestFilter
from trac.web.chrome import add_script, ITemplateProvider

from genshi.filters.transform import Transformer

class WikiDblclickEditModule(Component):
    implements(IRequestFilter, ITemplateProvider)
    
    # ITemplateProvider
    def get_templates_dirs(self):
        return []
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('dblclickedit',resource_filename(__name__, 'htdocs'))]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
	# do nothing special here
	return handler

    def post_process_request(self, req, template, data, content_type):
        if not 'action' in req.args:
            add_script(req, 'dblclickedit/js/dblclickedit.js')
        return template, data, content_type
