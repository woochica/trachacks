#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, ITemplateProvider
from pkg_resources import ResourceManager


class Checkbox(Component):
    """at query when
    double-click a checkbox clears neighbor checkboxes and check it.
    double-click a label at left of checkboxes flips checked or not. """

    implements(ITemplateProvider, ITemplateStreamFilter)

    #ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if(filename == 'query.html'):
            add_script(req, 'querystatushelper/js/enabler.js')
        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        return [('querystatushelper', ResourceManager().resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
