# This file is part of TracGtkDoc.
# Copyright (C) 2011 Luis Saavedra <luis94855510@gmail.com>
#
# TracGtkDoc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# TracGtkDoc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with TracGtkDoc.  If not, see <http://www.gnu.org/licenses/>.
#
# $Author$
# $Date$
# $Revision$

from genshi.builder import tag

from trac.core import Component, implements
from trac.config import Option
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, \
                            ITemplateProvider, \
                            add_stylesheet, \
                            add_script, \
                            add_ctxtnav
from trac.perm import IPermissionRequestor

import os
import re
import urllib

class GtkDocWebUI(Component):
    implements(INavigationContributor, \
               IRequestHandler, \
               ITemplateProvider, \
               IPermissionRequestor)

    index = Option('gtkdoc', 'index', 'index.html',
      """Default index page to pick in the generated documentation."""
    )

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            return 'gtkdoc'

    def get_navigation_items(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            books = self.config.get('gtkdoc', 'books')
            books = (books and re.split("[ ]*,[ ]*", books.strip())) or []
            if books:
                book = self.config.get('gtkdoc', 'default')
                path = req.href.gtkdoc()
                href_real = (book and os.path.join(path, book)) or path
                yield('mainnav', 'gtkdoc',
                      tag.a('API Reference', href=href_real, accesskey='r'))

    # IRequestHandler
    def match_request(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            return re.match(r'^/gtkdoc(-raw)?(?:/|$)([^/]+)?(?:/|$)(.+)?$', req.path_info)

    def _process_url(self, req):
        match = re.match(r'^/gtkdoc(-raw)?(?:/|$)([^/]+)?(?:/|$)(.+)?$', req.path_info)
        if match:
            book = match.group(2)
            page = match.group(3) or self.index
            
            if not book and self.config.get('gtkdoc', 'default'):
                book = self.config.get('gtkdoc', 'default')

            return book, page

        book = None
        page = self.index
        if self.config.get('gtkdoc', 'default'):
            book = self.config.get('gtkdoc', 'default')
            
        return book, page

    def _process_raw(self, req):
        book, page = self._process_url(req)
        self.log.debug("book is %r", book)
        self.log.debug("page is %r", page)
        self.log.debug("path_info is %r", req.path_info)
        self.log.debug("query_string is %r", req.query_string)

        path = self.config.get('gtkdoc', book)
        real_path = page and os.path.join(path, page) or path

        self.log.debug("real_path is %r", real_path)
        req.send_file(real_path)

    def _process_wrapper(self, req):
        book, page = self._process_url(req)
        self.log.debug("book is %r", book)
        self.log.debug("page is %r", page)
        self.log.debug("path_info is %r", req.path_info)
        self.log.debug("query_string is %r", req.query_string)

        # build the url and raw url
        url = req.href.gtkdoc()
        raw_url = '%s-raw' % url
        if book:
            url += '/%s' % book
            raw_url += '/%s' % book
            if page:
                url += '/%s' % page
                raw_url += '/%s' % page

        self.log.debug("url is %r", url)
        self.log.debug("raw_url is %r", raw_url)

        data = {
            'book': book,
            'page': page,
            'url' :  url,
            'raw_url': raw_url,
            'query': req.query_string
        }

        add_stylesheet(req, 'tracgtkdoc/css/gtkdoc.css')
        add_script(req, 'tracgtkdoc/js/jquery-1.4.3.min.js')
        add_script(req, 'tracgtkdoc/js/jquery.iframe-auto-height.plugin.js')

        books = self.config.get('gtkdoc', 'books')
        books = (books and re.split("[ ]*,[ ]*", books.strip())) or []
        for book in books:
          url = '%s/%s' % (req.href.gtkdoc(), book)
          add_ctxtnav(req, book, urllib.quote(url))

        return 'gtkdoc_wrapper.html', data, None

    def process_request(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            if re.match(r'/gtkdoc-raw.*', req.path_info):
                return self._process_raw(req)
            else:
                return self._process_wrapper(req)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracgtkdoc', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IPermissionRequestor
    def get_permission_actions(self):
        return [('GTKDOC_VIEW', ['GTKDOC_SEARCH'])]
