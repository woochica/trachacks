"""
 Wattchlist Plugin for Trac
 Copyright (c) 2008-2009  Martin Scharrer <martin@scharrer-online.de>
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

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

from trac.core import *

class IWatchlistProvider(Interface):
    def get_realms():
      """ Must return list or tuple of realms provided. """
      pass

    def get_realm_label(realm, plural=False):
      pass

    def res_exists(realm, resid):
      """ Returns if resource given by `realm` and `resid` exists. """
      pass

    def res_list_exists(realm, reslist):
      pass

    def res_pattern_exists(realm, pattern):
      pass

    def has_perm(realm, perm):
      pass

    def get_list(realm, wl, req):
      pass



class BasicWatchlist(Component):
    implements( IWatchlistProvider )
    realms = []

    def get_realms(self):
      return self.realms

    def get_realm_label(self, realm, plural=False):
      return realm + plural and 's' or ''

    def res_exists(self, realm, resid):
      return False

    def res_list_exists(self, realm, reslist):
      for res in reslist:
        if self.res_exists(realm, res):
          yield res

    def res_pattern_exists(self, realm, pattern):
      return []

    def has_perm(self, realm, perm):
      return realm.upper() + '_VIEW' in perm

    def get_list(self, realm, wl, req):
      return []

