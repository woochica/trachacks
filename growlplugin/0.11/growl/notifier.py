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


from trac.attachment import IAttachmentChangeListener
from trac.config import BoolOption, ListOption
from trac.core import *
from trac.perm import PermissionError
from trac.ticket import ITicketChangeListener 
from trac.wiki import IWikiChangeListener
from socket import AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_BROADCAST, socket
from netgrowl import GrowlRegistrationPacket, GrowlNotificationPacket

__all__ = ['GrowlNotifierSystem']


class GrowlSender(object):
    """Send a growl packet over the network."""

    GROWL_UDP_PORT = 9887
    
    def __init__(self, env):
        self.log = env.log

    def notify(self, hosts, growlpacket):
        s = socket(AF_INET, SOCK_DGRAM)
        payload = growlpacket.payload()
        broadcast = False
        for host in hosts:
            if host != '<broadcast>':
                self.log.info("Growl: send to %s" % host)
                s.sendto(payload, (host, self.GROWL_UDP_PORT))
            else:
                broadcast = True
        if broadcast:
            self.log.info("Growl: broadcast")
            s.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            s.sendto(payload, ('<broadcast>', self.GROWL_UDP_PORT))
        s.close()


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


    # settings
    userprefs_enabled = BoolOption('growl', 'userprefs', 'false',
        doc="""Enable per-user to define Growl notification option.""")

    dest_hosts = ListOption('growl', 'hosts', '',
        doc="""List of hosts to notify (default: broadcast to subnet)""")

    avail_sources = ListOption('growl', 'sources', ','.join(SOURCES),
        doc="""List of event sources (default: all available sources)""")


    # IAttachmentChangeListener Interface

    def attachment_added(self, attachment):
        """Called when an attachment is added."""
        if 'attachment' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='attachment',
                                      title='Attachment added',
                                      description=attachment.title)
        self._notify(self._get_hosts('attachment'), gnp)

    def attachment_deleted(self, attachment):
        """Called when an attachment is deleted."""
        if 'attachment' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Attachment deleted',
                                      description=attachment.title)
        self._notify(self._get_hosts('attachment'), gnp)


    # ITicketChangeListener Interface

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        if 'ticket' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket #%d created' % ticket.id,
                                      description=self._ticket_repr(ticket))
        self._notify(self._get_hosts('ticket'), gnp)

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified."""
        if 'ticket' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket #%d updated' % ticket.id,
                                      description=self._ticket_repr(ticket))
        self._notify(self._get_hosts('ticket'), gnp)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        if 'ticket' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='ticket',
                                      title='Ticket #%d deleted' % ticket.id,
                                      description=self._ticket_repr(ticket))
        self._notify(self._get_hosts('ticket'), gnp)


    # IWikiChangeListener Interface

    def wiki_page_added(self, page):
        """Called whenever a new Wiki page is added."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page created',
                                      description=page.name)
        self._notify(self._get_hosts('wiki'), gnp)

    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        """Called when a page has been modified."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page updated',
                                      description=self._wiki_repr(page,
                                                                  comment))
        self._notify(self._get_hosts('wiki'), gnp)

    def wiki_page_deleted(self, page):
        """Called when a page has been deleted."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page deleted',
                                      description=self._wiki_repr(page))
        self._notify(self._get_hosts('wiki'), gnp)

    def wiki_page_version_deleted(self, page):
        """Called when a version of a page has been deleted."""
        if 'wiki' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='wiki',
                                      title='Page suppressed',
                                      description=self._wiki_repr(page))
        self._notify(self._get_hosts('wiki'), gnp)


    # IBuildListener Interface

    def build_started(build):
        """Called when a build slave has accepted a build initiation."""
        if 'bitten' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='bitten',
                                      title='Build started',
                                      description=self._bitten_repr(build),
                                      priority=-2)
        self._notify(self._get_hosts('bitten'), gnp)
    
    def build_aborted(build):
        """Called when a build slave cancels a build or disconnects."""
        if 'bitten' not in self.sources:
            return
        gnp = GrowlNotificationPacket(notification='bitten',
                                      title='Build aborted',
                                      description=self._bitten_repr(build))
        self._notify(self._get_hosts('bitten'), gnp)
    
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
        self._notify(self._get_hosts('bitten'), gnp)


    # API
    
    def get_available_sources(self):
        return self.sources

    def is_userprefs_enabled(self):
        return self.userprefs_enabled
        
    def register_notifications(self, hosts):
        """Asks Growl clients to register Trac application. A bit suboptimal, 
        but that's the only way to register without an explicit user 
        registration""" 
        grp = GrowlRegistrationPacket()
        for n in self.avail_sources:
            grp.addNotification(n, n in self.sources)
        self._notify(hosts, grp)

    def validate_host(self, admin, host):
        if host == '<broadcast>':
            raise PermissionError("Broadcast: GROWL_ADMIN")
        # TODO: implement host validation
        return True

    # Implementation
    
    def __init__(self):
        self.sources = [s.strip().lower() for s in self.avail_sources]
        self.hosts = filter(None, [h.strip() for h in self.dest_hosts])
        # register project-defined hosts
        self.register_notifications(self.hosts)
        
    def _notify(self, hosts, gp):
        """Wrapper to notify growl clients"""
        try:
            # we do not want a Growl notification failure to be dispatched
            # to the web client
            gs = GrowlSender(self.env)
            gs.notify(hosts, gp)
        except IOError, e:
            self.log.error('Grow notification error: %s', e)

    def _ticket_repr(self, ticket):
        """String representation of a Trac ticket"""
        rep = '%s (%s)' % (ticket['summary'], ticket['status'])
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
    
    def _get_hosts(self, source):
        # get user-specific hosts
        hosts = self._get_users_hosts()
        # add hosts defined in the project config, removing duplicates
        hosts.extend([h for h in self.hosts if h not in hosts])

    def _get_user_hosts(self, source):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("SELECT DISTINCT H.value" \
            "FROM session_attribute src, session_attribute h" \
            "WHERE (S.name=%s AND S.value='1')" \
            "AND H.name='growl.host' AND S.sid=H.sid",
            ('growl.source.%s' % source),)
        hosts = []
        for host in cursor:
            if host:
                hosts.append(host)
        self.log.info("Hosts for %s: %s" % (source, hosts))
        # filter out empty hosts
        return filter(None, hosts)
