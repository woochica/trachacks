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

from trac.core import *
from trac.search import ISearchSource
from trac.perm import IPermissionRequestor
from trac.util import datefmt

from tracgtkdoc.api import get_books

import os
import re
import pwd

class GtkDocSearch(Component):
    implements(ISearchSource, IPermissionRequestor)

    def __init__(self):
        self._regex = re.compile(r'<ANCHOR id="(.+)" href="(?:[^/]+)/(.+)">')

    # loads an index.sgml from a gtkdoc book into a hash table of id:href
    def _load_index(self, book):
        path = self.config.get('gtkdoc', book)
        full_path = os.path.join(path, 'index.sgml')

        fp = open(full_path)
        stats = os.stat(full_path)
        date = datefmt.to_datetime(stats.st_mtime)
        user = pwd.getpwuid(stats.st_uid)[0]

        ids = {}

        for line in fp.readlines():
            match = self._regex.match(line)
            if match:
                ids[match.group(1).replace('-','_')] = (
                    os.path.join(book, match.group(2).replace('#', '?')),
                    date,
                    user
                )

        fp.close()

        return ids

    # ISearchSource
    def get_search_filters(self, req):
        if req.perm.has_permission('GTKDOC_SEARCH') and len(get_books(self.config)) > 0:
            yield ('api', 'API Reference', True)

    def get_search_results(self, req, terms, filters):
        if not 'api' in filters:
            return

        books = get_books(self.config)
        if not books:
            return

        base_url = req.href.gtkdoc()

        for book in books.keys():
            ids = self._load_index(book)

            for id in ids.keys():
                for term in terms:
                    if term in id:
                        url = '%s/%s' % (base_url, ids[id][0])
                        yield(url, id, ids[id][1], ids[id][2], None)

        # dirty hack to stop exceptions for the time being
        if False:
            yield None

    # IPermissionRequestor
    def get_permission_actions(self):
        return ['GTKDOC_SEARCH']
