# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Emmanuel Blot <emmanuel.blot@free.fr>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://trac.edgewall.com/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.


from trac.core import *
from trac.wiki import IWikiChangeListener
from trac.ticket import ITicketChangeListener 
from trac.attachment import IAttachmentChangeListener
from socket import AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST, socket
from netgrowl import GrowlRegistrationPacket, GrowlNotificationPacket

__all__ = ['GrowlNotifierSystem']


class GrowlSender(object):
    """Send a growl packet over the network."""

    GROWL_UDP_PORT = 9887
        
    def __init__(self, hosts=[]):
        self.hosts = hosts
        self.socket = socket(AF_INET, SOCK_DGRAM)
        
    def notify(self, growlpacket):
        if not self.hosts:
            self.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.socket.sendto(growlpacket.payload(), 
                               ('<broadcast>', self.GROWL_UDP_PORT))
        else:
            payload = growlpacket.payload()
            for host in self.hosts:
                self.socket.sendto(payload, (host, self.GROWL_UDP_PORT))


class GrowlNotifierSystem(Component):
    """Trac notifier for Growl network clients."""

    implements(IWikiChangeListener, 
               ITicketChangeListener, 
               IAttachmentChangeListener)

    # IAttachmentChangeListener Interface

    def attachment_added(self, attachment):
        """Called when an attachment is added."""
        gnp = GrowlNotificationPacket(notification='attachment',
                                      title='Attachment added',
                                      description=attachment.title)
        self._notify(gnp)

    def attachment_deleted(self, attachment):
        """Called when an attachment is deleted."""
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Attachment deleted',
                                      description=attachment.title)
        self._notify(gnp)


    # ITicketChangeListener Interface

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket created',
                                      description='#%d' % ticket.id)
        self._notify(gnp)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified."""
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket updated',
                                      description='#%d' % ticket.id)
        self._notify(gnp)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket deleted',
                                      description='#%d' % ticket.id)
        self._notify(gnp)


    # IWikiChangeListener Interface

    def wiki_page_added(self, page):
        """Called whenever a new Wiki page is added."""
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Wiki page created',
                                      description=page.name)
        self._notify(gnp)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        """Called when a page has been modified."""
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Wiki page updated',
                                      description=page.name)
        self._notify(gnp)

    def wiki_page_deleted(self, page):
        """Called when a page has been deleted."""
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Wiki page deleted',
                                      description=page.name)
        self._notify(gnp)

    def wiki_page_version_deleted(self, page):
        """Called when a version of a page has been deleted."""
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Wiki page removed',
                                      description= \
                                        'Last version of %s removed' % \
                                            page.name)
        self._notify(gnp)


    # Implementation
    def __init__(self):
        sources = self.config.get('growl', 'sources', 
                                  'wiki, ticket, attachment')
        sources = [s.strip().lower() for s in sources.split(',')]
        hosts = self.config.get('growl', 'hosts', '')
        self.hosts = [h.strip() for h in hosts]
        grp = GrowlRegistrationPacket()
        for n in ('wiki', 'ticket', 'attachment'):
            grp.addNotification(n, n in sources)
        gs = GrowlSender()
        gs.notify(grp)
        
    def _notify(self, gp):
        """Wrapper to notify growl clients"""
        try:
            # we do not want a Growl notification failure to be dispatched
            # to the web client
            gs = GrowlSender(self.hosts)
            gs.notify(gp)
        except IOError, e:
            self.log.error('Grow notification error: %s', e)
