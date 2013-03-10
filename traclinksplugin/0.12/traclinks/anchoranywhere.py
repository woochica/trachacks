#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 MATOBA Akihiro <matobaa+trac-hacks@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

from pkg_resources import ResourceManager
from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script, ITemplateProvider, add_stylesheet


class AnchorAnywhere(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)

    def filter_stream(self, req, method, filename, stream, data):
        add_script(req, 'traclinks/js/anchoranywhere.js')
        add_stylesheet(req, 'traclinks/css/anchoranywhere.css')
        return stream

    # ITemplateProvider methods
    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('traclinks', ResourceManager().resource_filename(__name__, 'htdocs'))]
