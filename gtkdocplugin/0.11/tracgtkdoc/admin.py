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

    # IAdminPanelProvider
    def get_admin_panels(self, req):
        if req.perm.has_permission('GTKDOC_ADMIN') or req.perm.has_permission('TRAC_ADMIN'):
            yield('general', 'General', 'gtkdoc', 'GtkDoc')

    def render_admin_panel(self, req, category, page, path_info):
        if req.method == 'POST':
            if req.args.get('add'):
                default = self.config.get('gtkdoc', 'default')
                books = self.config.get('gtkdoc', 'books')
                books = (books and re.split("[ ]*,[ ]*", books.strip())) or []
                if not req.args.get('name') in books:
                  books.append(req.args.get('name'))

                if books and not default:
                  default = books[0]
                self.config.set('gtkdoc', 'default', default)
                self.config.set('gtkdoc', 'books', ", ".join(books))
                self.config.set('gtkdoc', req.args.get('name'), req.args.get('path'))
                self.config.save()

            if req.args.get('remove'):
                default = self.config.get('gtkdoc', 'default')
                books = self.config.get('gtkdoc', 'books')
                books = (books and re.split("[ ]*,[ ]*", books.strip())) or []

                sel = req.args.get('sel')
                sel = (isinstance(sel, list) and sel) or [sel]
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
                self.config.set('gtkdoc', 'default', req.args.get('default'))
                self.config.save()

        default = None
        books = []
        if 'gtkdoc' in self.config:
            default = self.config.get('gtkdoc', 'default')
            books_names = self.config.get('gtkdoc', 'books')
            books_names = (books_names and re.split("[ ]*,[ ]*", books_names.strip())) or []
            for book in books_names:
              path = self.config.get('gtkdoc', book)
              books.append({ 'name': book, 'path': path })

        data = {
            'books': books,
            'default': default
        }

        return 'gtkdoc_admin.html', data

    # ITemplateProvider
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return []

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IPermissionRequestor
    def get_permission_actions(self):
        return [('GTKDOC_ADMIN', ['GTKDOC_VIEW'])]
