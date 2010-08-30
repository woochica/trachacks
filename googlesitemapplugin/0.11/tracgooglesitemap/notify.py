# -*- coding: utf-8 -*-
"""
 Copyright (c) 2010 by Martin Scharrer <martin@scharrer-online.de>
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = ur"$Rev$"[6:-2]
__date__     = ur"$Date$"[7:-2]

from trac.core       import *
from trac.config     import ListOption
from trac.wiki.api   import IWikiChangeListener
from trac.ticket.api import ITicketChangeListener
from urllib          import urlopen,quote_plus


class GoogleSitemapNotifier(Component):
    implements ( IWikiChangeListener, ITicketChangeListener )

    rev = __revision__
    date = __date__

    notifyon = ListOption('googlesitemap','notify_on',
                  default='TICKET_CREATE,TICKET_MODIFY,WIKI_CREATE,WIKI_VERSION_DELETE,WIKI_MODIFY,WIKI_RENAME',
                  doc='Notify Google about a new sitemap on the listed actions. Valid values are: ' \
                      'TICKET_CREATE, TICKET_DELETE, TICKET_MODIFY, WIKI_CREATE, WIKI_DELETE, WIKI_VERSION_DELETE, WIKI_MODIFY, WIKI_RENAME' )

    def notify(self):
        sitemapurl = self.env.abs_href( self.config.get('googlesitemap', 'sitemappath', 'sitemap.xml') )
        #self.env.log.debug('Sitemap URL: ' + sitemapurl)
        url = r'http://www.google.com/webmasters/tools/ping?sitemap=' + quote_plus(sitemapurl)
        #self.env.log.debug('Google URL: ' + url)
        try:
            response = urlopen(url).read()
        except Exception, e:
            self.env.log.warn('Google notification failed: ' + unicode(e))
        #else:
        #    self.env.log.debug('Google notification successful!')


    def ticket_created(self, ticket):
      if 'TICKET_CREATE' in self.notifyon:
        self.notify()

    def ticket_changed(self, ticket, comment, author, old_values):
      if 'TICKET_MODIFY' in self.notifyon:
        self.notify()

    def ticket_deleted(self, ticket):
      if 'TICKET_DELETE' in self.notifyon:
        self.notify()

    def wiki_page_added(self, page):
      if 'WIKI_CREATE' in self.notifyon:
        self.notify()

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
      if 'WIKI_MODIFY' in self.notifyon:
        self.notify()

    def wiki_page_deleted(self, page):
      if 'WIKI_DELETE' in self.notifyon:
        self.notify()

    def wiki_page_version_deleted(self, page):
      if 'WIKI_VERSION_DELETE' in self.notifyon:
        self.notify()

    def wiki_page_renamed(self, page, old_name):
      if 'WIKI_RENAME' in self.notifyon:
        self.notify()


