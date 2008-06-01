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

    SOURCES = [u'wiki', u'ticket', u'attachment']
    
    # default notification
    implements(IWikiChangeListener, 
               ITicketChangeListener, 
               IAttachmentChangeListener)

    # optional support for Bitten notifications
    try:
        from bitten.api import IBuildListener
        from bitten.model import Build
        implements(IBuildListener)
        SOURCES.append(u'bitten')
    except:
        pass
        
    # IAttachmentChangeListener Interface

    def attachment_added(self, attachment):
        """Called when an attachment is added."""
        if 'attachment' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='attachment',
                                      title='Attachment added',
                                      description=attachment.title)
        self._notify(gnp)

    def attachment_deleted(self, attachment):
        """Called when an attachment is deleted."""
        if 'attachment' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Attachment deleted',
                                      description=attachment.title)
        self._notify(gnp)


    # ITicketChangeListener Interface

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        if 'ticket' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket created',
                                      description=self._ticket_repr(ticket))
        self._notify(gnp)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified."""
        if 'ticket' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket updated',
                                      description=self._ticket_repr(ticket))
        self._notify(gnp)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        if 'ticket' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket deleted',
                                      description=self._ticket_repr(ticket))
        self._notify(gnp)


    # IWikiChangeListener Interface

    def wiki_page_added(self, page):
        """Called whenever a new Wiki page is added."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page created',
                                      description=page.name)
        self._notify(gnp)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        """Called when a page has been modified."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page updated',
                                      description=self._wiki_repr(page,
                                                                  comment))
        self._notify(gnp)

    def wiki_page_deleted(self, page):
        """Called when a page has been deleted."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page deleted',
                                      description=self._wiki_repr(page))
        self._notify(gnp)

    def wiki_page_version_deleted(self, page):
        """Called when a version of a page has been deleted."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page suppressed',
                                      description=self._wiki_repr(page))
        self._notify(gnp)


    # IBuildListener Interface

    def build_started(build):
        """Called when a build slave has accepted a build initiation."""
        if 'bitten' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='bitten',
                                      title='Build started',
                                      description=self._bitten_repr(build),
                                      priority=-2)
        self._notify(gnp)
    
    def build_aborted(build):
        """Called when a build slave cancels a build or disconnects."""
        if 'bitten' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='bitten',
                                      title='Build aborted',
                                      description=self._bitten_repr(build))
        self._notify(gnp)
    
    def build_completed(build):
        """Called when a build slave has completed a build, regardless of the
        outcome."""
        if 'bitten' not in self.sources:
            return
        failure = self.status == Build.FAILURE
        status = 'Build %s' % failure and 'failed' or 'successful'
        gnp = GrowlNotificationPacket(notification='bitten',
                                      title=status,
                                      description=self._bitten_repr(build),
                                      sticky=failure,
                                      priority=failure and 2 or 0)
        self._notify(gnp)


    # Implementation
    
    def __init__(self):
        sources = self.config.get('growl', 'sources', ', '.join(self.SOURCES))
        sources = [s.strip().lower() for s in sources.split(',')]
        hosts = self.config.get('growl', 'hosts', '')
        self.hosts = [h.strip() for h in hosts]
        # Asks Growl clients to register Trac application every time Trac
        # is started. A bit suboptimal, but that's the only way to register
        # without an explicit user registration
        grp = GrowlRegistrationPacket()
        for n in self.SOURCES:
            grp.addNotification(n, n in sources)
            self.sources = sources
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

    def _ticket_repr(self, ticket):
        """String representation of a Trac ticket"""
        rep = '%s #%d (%s)' % (ticket['summary'], ticket.id, ticket['status'])
        return rep
        
    def _wiki_repr(self, page, comment=None):
        """String representation of a Trac wiki page"""
        rep = page.name
        if comment:
            rep += '\n%s' % comment
        return rep
        
    def _bitten_repr(self, build):
        """String representation of a Bitten build"""
        rep = '%s (%d) r%d' % (build.config, build.id, build.rev)
        if build.platform:
            rep += ' %s' % build.platform 
        if build.slave:
            rep += ' %s' % build.slave
        return rep
        