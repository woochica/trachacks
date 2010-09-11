# -*- coding: utf-8 -*-
"""
 Unfinished Example Watchlist Provider for Trac Watchlist Plugin
 Copyright (c) 2008-2010  Martin Scharrer <martin@scharrer-online.de>
 This is Free Software under the BSD license.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from  trac.core                 import  *
from  tracwatchlist.api         import  BasicWatchlist, IWatchlistProvider
from  tracwatchlist.translation import  add_domain, _, N_, T_, t_, tag_, gettext


class ExampleWatchlist(Component):
    """Example watchlist provider."""
    implements( IWatchlistProvider )

    def get_realms(self):
      return ('example',)

    def get_realm_label(self, realm, plural=False):
      return plural and 'examples' or 'example'

    def res_exists(self, realm, resid):
      return True

    def res_list_exists(self, realm, reslist):
      return []

    def res_pattern_exists(self, realm, pattern):
      return True

    def has_perm(self, realm, perm):
      return True

    def get_list(self, realm, wl, req):
      db = self.env.get_db_cnx()
      cursor = db.cursor()
      user = req.authname
      examplelist = []
      cursor.execute("""
        SELECT resid
          FROM watchlist
         WHERE wluser=%s AND realm='example'
      """, (user,)
      )
      examples = cursor.fetchall()
      for (name,) in examples:
        examplelist.append({'name':name})
      return examplelist

