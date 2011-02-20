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
from trac.config import Option
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
import urllib
import mimetypes

class GtkDocWebUI(Component):
    implements(INavigationContributor, \
               IRequestHandler, \
               ITemplateProvider, \
               IPermissionRequestor, \
               IWikiSyntaxProvider)

    index = Option('gtkdoc', 'index', 'index.html',
      """Default index page to pick in the generated documentation."""
    )

    wiki_index = Option('gtkdoc', 'wiki_index', None,
      """Wiki page to use as the default page for the GtkDoc main page.
      If set, supersedes the `[gtkdoc] index` option."""
    )

    title = Option('gtkdoc', 'title', 'API Reference',
      """Title to use for the main navigation tab."""
    )

    encoding = Option('gtkdoc', 'encoding', 'utf-8',
      """Default encoding used by the generated documentation files."""
    )    

    # intern-all
    def _get_books(self):
        books = self.config.get('gtkdoc', 'books')
        books = (books and re.split("[ ]*,[ ]*", books.strip())) or []            
        return books

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            return 'gtkdoc'

    def get_navigation_items(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            books = self._get_books()
            if books:
                yield('mainnav', 'gtkdoc',
                      tag.a(self.title, href=req.href.gtkdoc(), accesskey='r'))

    # IRequestHandler
    def match_request(self, req):
        if req.perm.has_permission('GTKDOC_VIEW'):
            return re.match(r'^/gtkdoc(?:/|$)([^/]+)?(?:/|$)(.+)?$', req.path_info)

    def _process_url(self, req):
        match = re.match(r'^/gtkdoc(?:/|$)([^/]+)?(?:/|$)(.+)?$', req.path_info)
        if match:
            if not(match.group(1) or match.group(2)):
                book = 'wiki_index'
                page = self.wiki_index
                path = None

                if page:
                    return book, page, path

                book = self.config.get('gtkdoc', 'default')
                if book:
                    redirect_href = os.path.join(req.href.gtkdoc(), book)
                    req.redirect(redirect_href)
                else:
                    raise TracError("Can't read gtkdoc content: %s" % req.path_info)

            books = self._get_books()

            book = match.group(1)
            page = match.group(2) or self.index
            if not book:
                book = self.config.get('gtkdoc', 'default')
                page = self.index
            if book not in books:
                book = self.config.get('gtkdoc', 'default')
                page = match.group(1) or self.index

            if not book or book not in books:
                raise TracError("Can't read gtkdoc content: %s" % req.path_info)

            path = os.path.join(self.config.get('gtkdoc', book), page)
            return book, page, path

        raise TracError("Can't read gtkdoc content: %s" % req.path_info)

    def _process_request(self, req):
        book, page, path = self._process_url(req)

        data = {
            'title': self.title,
        }

        # build wiki_index
        if book == 'wiki_index':
            if page:
                text = ''
                if WikiSystem(self.env).has_page(page):
                    text = WikiPage(self.env, page).text
                else:
                    text = '!GtkDoc index page [wiki:"%s"] does not exist.' % page
                data['wiki_content'] = wiki_to_html(text, self.env, req)
                add_ctxtnav(req, "View %s page" % page, req.href.wiki(page))
                return 'gtkdoc.html', data, 'text/html'

        # build content
        mimetype, encoding = mimetypes.guess_type(path)
        encoding = encoding or \
                   self.encoding or \
                   self.env.config['trac'].get('default_charset')
        content = ''
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

        books = self._get_books()
        if len(books) > 1:
            for book in books:
                url = '%s/%s' % (req.href.gtkdoc(), book)
                add_ctxtnav(req, book, urllib.quote(url))

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
            books = self._get_books()

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
	
            return tag.a(label, title=self.title, href=href_fragment)

        yield ('gtkdoc', gtkdoc_link)
