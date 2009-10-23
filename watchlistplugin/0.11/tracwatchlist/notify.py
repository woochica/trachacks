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
from trac.core import *

from  trac.web.href      import  Href
from  trac.util.text     import  to_unicode
from  trac.wiki.api      import  IWikiChangeListener
from  trac.ticket.api    import  ITicketChangeListener
from  trac.notification  import  NotifyEmail

import operator

class WatchlistNotifier(NotifyEmail):
    template_name = "ticket_notify_email.txt"

    def get_recipients(self, resid):
      debug = self.env.log.debug
      debug("WLN: resid = " + str(resid))
      return (list(resid), list())

class WatchlistListener(Component):
    implements( IWikiChangeListener, ITicketChangeListener )


    def wiki_users(self,page_name):
      db = self.env.get_db_cnx()
      cursor = db.cursor();
      cursor.execute("SELECT wluser FROM watchlist WHERE "
          "realm='wiki' AND resid=%s", (page_name,) )
      return map(operator.itemgetter(0), cursor.fetchall())

    def ticket_users(self,ticket_name):
      db = self.env.get_db_cnx()
      cursor = db.cursor();
      cursor.execute("SELECT wluser FROM watchlist WHERE "
          "realm='ticket' AND resid=%s", (ticket_name,) )
      return map(operator.itemgetter(0), cursor.fetchall())

    def wiki_page_added(self,page):
      pass

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
      debug = self.env.log.debug
      debug("WLN: page = " + str(page))
      debug("WLN: page.name = " + page.name)
      users = self.wiki_users(page.name)
      debug("WLN: page %s changed: Notifing users: %s" % (page.name,
        ', '.join(users)) )
      WatchlistNotifier(self.env).notify(users, "Watched wiki page changed")

    def wiki_page_deleted(self,page):
      pass

    def wiki_page_version_deleted(self,page):
      pass

    def ticket_created(self,ticket):
      pass

    def ticket_changed(self,ticket, comment, author, old_values):
      pass

    def ticket_deleted(self,ticket):
      pass


