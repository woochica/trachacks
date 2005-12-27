# vim: ts=4 expandtab
#
# Copyright (C) 2005 Jason Parks <jparks@jparks.net>. All rights reserved.
#

from __future__ import generators

import os
import time
import posixpath
import re

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider


class DoxygenPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    def get_active_navigation_item(self, req):
        return 'doxygen'
    def get_navigation_items(self, req):
        yield 'mainnav', 'doxygen', '<a href="%s">Doxygen</a>' % (self.env.href.doxygen())

    def match_request(self, req):
        if req.path_info == '/doxygen':
            req.args['path'] = ''.join([self.config.get('doxygen', 'path'), '/main.html'])
            return True
        else:
            path = ''.join([self.config.get('doxygen', 'path'), req.path_info])
            req.args['path'] = path
#            self.log.debug('1 - doc = %s : %d' % (path, os.path.exists(path)))
            return os.path.exists(path)

    def process_request(self, req):
        req.hdf['doxygen.path'] = req.args['path']
        return 'doxygen.cs', 'text/html'

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
    
