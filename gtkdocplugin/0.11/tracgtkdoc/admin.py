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

from trac.core import Component, implements
from trac.admin import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider
from trac.perm import IPermissionRequestor

import re

class GtkDocAdmin(Component):
    implements(IAdminPanelProvider, \
               ITemplateProvider, \
               IPermissionRequestor)

    # intern-all
    def _get_values(self, book):
        values = self.config.get('gtkdoc', book)
        values = (values and re.split("[ ]*,[ ]*", values.strip())) or []
        return values

    # IAdminPanelProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('GTKDOC_ADMIN') or \
           req.perm.has_permission('TRAC_ADMIN'):
            yield('general', 'General', 'gtkdoc', 'GTK-Doc')

    def render_admin_panel(self, req, category, page, path_info):
        if req.method == 'POST':
            if req.args.get('add'):
                books = self._get_values('books')
                if req.args.get('name') not in books:
                  books.append(req.args.get('name'))

                default = self.config.get('gtkdoc', 'default')
                if books and not default:
                  default = books[0]

                values = [
                    req.args.get('path'),
                    req.args.get('index'),
                    req.args.get('encoding'),
                    req.args.get('sgml'),
                ]
                values_str = u', '.join(values)

                self.config.set('gtkdoc', 'default', default)
                self.config.set('gtkdoc', 'books', ", ".join(books))
                self.config.set('gtkdoc', req.args.get('name'), values_str)
                self.config.save()

            if req.args.get('remove'):
                books = self._get_values('books')
                default = self.config.get('gtkdoc', 'default')

                sel = req.args.get('sel')
                sel = (isinstance(sel, list) and sel) or (sel and [sel]) or []
                for book in sel:
                    if book == default:
                      default = None
                    self.config.remove('gtkdoc', book)
                    books.remove(book)

                if books and not default:
                  default = books[0]

                self.config.set('gtkdoc', 'default', default)
                self.config.set('gtkdoc', 'books', ", ".join(books))
                self.config.save()

            if req.args.get('apply'):
                self.config.set('gtkdoc', 'title', req.args.get('title'))
                self.config.set('gtkdoc', 'wiki_index', req.args.get('wiki_index'))
                self.config.set('gtkdoc', 'default', req.args.get('default'))
                self.config.save()

        books = []
        books_names = self._get_values('books')
        for book in books_names:
            values = self._get_values(book)
            book_path = values[0]
            book_index = values[1]
            book_encoding = values[2]
            book_sgml = values[3]
            books.append({
                'name': book,
                'path': book_path,
                'index': book_index,
                'encoding': book_encoding,
                'sgml': book_sgml,
            })

        title = self.config.get('gtkdoc', 'title') or 'API Reference'
        wiki_index = self.config.get('gtkdoc', 'wiki_index')
        default = self.config.get('gtkdoc', 'default')

        data = {
            'title': title,
            'wiki_index': wiki_index,
            'default': default,
            'books': books,
        }

        return 'gtkdoc_admin.html', data

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IPermissionRequestor
    def get_permission_actions(self):
        return [('GTKDOC_ADMIN', ['GTKDOC_VIEW'])]
