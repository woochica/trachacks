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
from genshi.core import Markup

from trac.core import Component, implements, TracError
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor, \
                            ITemplateProvider, \
                            add_ctxtnav
from trac.util.text import to_unicode
from trac.perm import IPermissionRequestor
from trac.wiki.api import IWikiSyntaxProvider, WikiSystem
from trac.wiki.model import WikiPage
from trac.wiki.formatter import wiki_to_html

import os
import re
import urllib2
import mimetypes

class GtkDocWebUI(Component):
    implements(INavigationContributor, \
               IRequestHandler, \
               ITemplateProvider, \
               IPermissionRequestor, \
               IWikiSyntaxProvider)

    # intern-all
    def _get_values(self, book):
        values = self.config.get('gtkdoc', book)
        values = (values and re.split("[ ]*,[ ]*", values.strip())) or []
        return values

    def _get_title(self):
        title = self.config.get('gtkdoc', 'title') or 'API Reference'
        return title

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            return 'gtkdoc'

    def get_navigation_items(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            books = self._get_values('books')
            if books:
                yield('mainnav', 'gtkdoc',
                      tag.a(self._get_title(), href=req.href.gtkdoc(), accesskey='r'))

    # IRequestHandler
    def match_request(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            return re.match(r'^/gtkdoc(?:/|$)([^/]+)?(?:/|$)(.+)?$', req.path_info)

    def _process_url(self, req):
        match = re.match(r'^/gtkdoc(?:/|$)([^/]+)?(?:/|$)(.+)?$', req.path_info)
        if match:
            if not(match.group(1) or match.group(2)):
                book = 'wiki_index'
                page = self.config.get('gtkdoc', book)

                if page:
                    return book, page

                book = self.config.get('gtkdoc', 'default')
                if book:
                    redirect_href = os.path.join(req.href.gtkdoc(), book)
                    req.redirect(redirect_href)
                else:
                    raise TracError("Can't read gtkdoc content: %s" % req.path_info)

            books = self._get_values('books')

            book = None
            page = None
            if match.group(1) not in books:
                book = self.config.get('gtkdoc', 'default')
                page = match.group(1)
                if match.group(2):
                    if page:
                        page = os.path.join(page, match.group(2))
                    else:
                        page = match.group(2)
            else:
                book = match.group(1)
                page = match.group(2)

            if not book:
                raise TracError("Can't read gtkdoc content: %s" % req.path_info)

            return book, page

        raise TracError("Can't read gtkdoc content: %s" % req.path_info)

    def _process_request(self, req):
        book, page = self._process_url(req)

        data = {
            'title': self._get_title(),
        }

        # build wiki_index
        if book == 'wiki_index':
            if page:
                text = ''
                if WikiSystem(self.env).has_page(page):
                    text = WikiPage(self.env, page).text
                else:
                    text = 'GTK-Doc index page [wiki:"%s"] does not exist.' % page
                data['wiki_content'] = wiki_to_html(text, self.env, req)
                add_ctxtnav(req, "View %s page" % page, req.href.wiki(page))
                return 'gtkdoc.html', data, 'text/html'
            else:
                raise TracError("Can't read gtkdoc content: %s" % req.path_info)

        # build content
        values = self._get_values(book)
        book_path = values[0]
        book_index = values[1]
        book_encoding = values[2]

        page = page or book_index
        path = os.path.join(book_path, page)

        mimetype, encoding = mimetypes.guess_type(path)
        encoding = encoding or \
                   book_encoding or \
                   self.env.config['trac'].get('default_charset')

        # Genshi can't include an unparsed file
        # data = {'content': path}
        if (mimetype == 'text/html'):
            try:
                content = Markup(to_unicode(file(path).read(), encoding))
            except (IOError, OSError), e:
                self.log.debug("Can't read gtkdoc content: %s" % e)
                raise TracError("Can't read gtkdoc content: %s" % req.path_info)
            data['content'] = content
        else:
            if mimetype:
                req.send_file(path, mimetype)
            else:
                raise TracError("Can't read gtkdoc content mimetype: %s" % req.path_info)

        books = self._get_values('books')
        if len(books) > 1:
            for book in books:
                url = '%s/%s' % (req.href.gtkdoc(), book)
                add_ctxtnav(req, book, urllib2.quote(url))

        return 'gtkdoc.html', data, 'text/html'

    def process_request(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            return self._process_request(req)

    # ITemplateProvider
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IPermissionRequestor
    def get_permission_actions(self):
        return [('GTKDOC_VIEW', ['GTKDOC_SEARCH'])]

    # IWikiSyntaxProvider
    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        def gtkdoc_link(formatter, ns, params, label):
            match = re.match(r'^(?:/|$)?([^/]+)?(?:/|$)(.+)?$', params)
            books = self._get_values('books')

            href_fragment = formatter.href.gtkdoc()
            if match:
                if match.group(1) not in books:
                    book = self.config.get('gtkdoc', 'default')
                    if book:
                        href_fragment = os.path.join(href_fragment, book)
                if match.group(1):
                    href_fragment = os.path.join(href_fragment, match.group(1))
                if match.group(2):
                    href_fragment = os.path.join(href_fragment, match.group(2))
	
            return tag.a(label, title=self._get_title(), href=href_fragment)

        yield ('gtkdoc', gtkdoc_link)
