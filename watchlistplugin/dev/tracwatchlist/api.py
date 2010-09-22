# -*- coding: utf-8 -*-
"""
 Watchlist Plugin for Trac
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

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2].strip('M'))
__date__     = ur"$Date$"[7:-2]

import copy
from  trac.core                  import  *
from  tracwatchlist.translation  import  gettext


class IWatchlistProvider(Interface):
    """Interface for watchlist providers."""
    def get_realms():
        """ Must return list or tuple of realms provided. """
        pass

    def get_realm_label(realm, n_plural=1):
        pass

    def resources_exists(realm, resids):
        """ Returns all existing resources described by `realm` and `resids`.
            If `resids` is a list return all listed resources which exist.
            If `resids` is a string, take it as a pattern and
            list all resources which match it.
            """
        pass

    #def res_list_exists(realm, reslist):
    #    pass

    #def res_pattern_exists(realm, pattern):
    #    pass

    def has_perm(realm, perm):
        pass

    def get_list(realm, wl, req, fields=None):
        """Returns list of watched elements as dictionaries plus an extra dictionary of extra
           template data, which will be available in the template under the name "<realm>data"
           Example: 
                data = [ {'name':'example', 'changetime': <DT Object> }, { ... } ]
                extradict = { 'somethingspecial':42, ... }
                return data, extradict
           """
        pass

    def get_href(realm, resid=None):
        pass

    def get_abs_href(realm, resid=None):
        pass

    def get_fields(realm):
        """ Returns fields (table columns)
          Format: ( {Field:Label, Field:Label, ...}, (DEFAULT list) )
        """
        pass

    def get_sort_key(realm):
        """Returns a sort `key` function for the argument of the same name of 
           `sorted` or `list.sort`. By default this can be `None` for normal 
           sorting.
           Providers with numeric resource ids should return `int` or a similar
           function to enable numeric sorting.
           """
        pass

    def get_sort_cmp(realm):
        """Returns a sort `cmp` function for the argument of the same name of 
           `sorted` or `list.sort`. By default this can be `None` for normal 
           sorting. """
        pass


class BasicWatchlist(Component):
    """Base class for watchlist providers.
    This class provides default implementations of all interface methods.
    Watchlist provider can inherit from it to simply their implementation.
    """
    implements( IWatchlistProvider )
    realms = []
    default_fields = {}
    fields = {}
    sort_key = {}
    sort_cmp = {}

    def get_sort_key(self, realm):
        return self.sort_key.get(realm, None)

    def get_sort_cmp(self, realm):
        return self.sort_cmp.get(realm, None)

    def get_realms(self):
        return self.realms

    def get_realm_label(self, realm, n_plural=1):
        if n_plural == 1:
            return realm.capitalize()
        else:
            return realm.capitalize() + 's'

    def resources_exists(self, realm, resids):
        if isinstance(resids,basestring):
            return False
        else:
            return False

    def has_perm(self, realm, perm):
        if realm not in self.realms:
            return False
        return realm.upper() + '_VIEW' in perm

    def get_list(self, realm, wl, req, fields=None):
        return [], {}

    def get_href(self, realm, resid=None, **kwargs):
        if resid is None:
            return self.env.href.__get_attr__(realm)
        else:
            return self.env.href(realm,resid,**kwargs)

    def get_abs_href(self, realm, resid=None, **kwargs):
        if resid is None:
            return self.env.abs_href.__get_attr__(realm)
        else:
            return self.env.abs_href(realm,resid,**kwargs)

    def get_fields(self, realm):
        # Needed to re-localise after locale changed:
        # See also ticket.api: get_ticket_fields
        fields = copy.deepcopy(self.fields.get(realm,{}))
        col = 'col' # workaround gettext extraction bug
        for col in fields:
            fields[col] = gettext(fields[col])
        return ( fields, self.default_fields.get(realm,[]) )

# EOF
