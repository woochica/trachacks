# -*- coding: utf-8 -*-
#
# Copyright (c) 2008, Stephen Hansen
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2010,2012, Steffen Hoffmann
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

# TODO: Test all anonymous subscribers
# TODO: Subscriptions admin page

import re

from trac.config import BoolOption, Option, ListOption
from trac.core import Component, implements

from announcer.api import IAnnouncementDefaultSubscriber
from announcer.api import IAnnouncementSubscriber
from announcer.api import _
from announcer.model import Subscription

"""Subscribers should return a list of subscribers based on event rules.
The subscriber interface is very simple and flexible.  Subscriptions have
an 'adverb' attached, 'always' or 'never'.  A subscription can also stop a
subscriber from recieving a notification, if it's adverb is 'never' and it
is the highest priority matching subscription.

One thing, that remains to be done, is to allow admin to control defaults for
users, that never login and setup their subscriptions.  Some of these
should look to see, if the user has any subscriptions in the subscription
table, and if not, then use the default setting from trac.ini.

There should also be a screen in the admin section of the site, that let's the
admin setup rules for users.  It should be possible to copy rules from one
user to another.

We must also support unauthenticated users in the form of email addresses.
An email address can be used in place of an sid in many places in Trac.
Here's what I can think of:

 * Cc: field
 * Custom Cc: field (see opt.subscribers.TicketCustomFieldSubscriber)
 * Component owner (see opt.subscribers.TicketComponentOwnerSubscriber)
 * Ticket owner
 * Ticket reporter

The final thing to consider is unauthenticated users, who have entered an email
address in the preferences panel.  To me this is the least important case and
will probably be lowest priority.

"""

__all__ = ['CarbonCopySubscriber', 'TicketOwnerSubscriber',
           'TicketReporterSubscriber', 'TicketUpdaterSubscriber']


class CarbonCopySubscriber(Component):
    """Carbon copy subscriber for cc ticket field."""

    implements(IAnnouncementDefaultSubscriber,
               IAnnouncementSubscriber)

    default_on = BoolOption("announcer", "always_notify_cc", 'true',
        """The always_notify_cc will notify users in the cc field by default
        when a ticket is modified.
        """)

    default_distributor = ListOption("announcer",
        "always_notify_cc_distributor", "email",
        doc="""Comma-separated list of distributors to send the message to
        by default.  ex. email, xmpp
        """)

    # IAnnouncementSubscriber methods

    def matches(self, event):
        if event.realm != 'ticket':
            return
        if event.category not in ('created', 'changed', 'attachment added'):
            return

        klass = self.__class__.__name__
        cc = event.target['cc'] or ''
        sids = set()
        for chunk in re.split('\s|,', cc):
            chunk = chunk.strip()

            if not chunk or chunk.startswith('@'):
                continue

            if re.match(r'^[^@]+@.+', chunk):
                sid, auth, addr = None, 0, chunk
            else:
                sid, auth, addr = chunk, 1, None

            # Default subscription
            for s in self.default_subscriptions():
                yield (s[0], s[1], sid, auth, addr, None, s[2], s[3])
            if sid:
                sids.add((sid,auth))

        for s in Subscription.find_by_sids_and_class(self.env, sids, klass):
            yield s.subscription_tuple()

    def description(self):
        return _("notify me when I'm listed in the CC field of a ticket "
                 "that is modified")

    def requires_authentication(self):
        return True

    # IAnnouncementDefaultSubscriber method
    def default_subscriptions(self):
        if self.default_on:
            for d in self.default_distributor:
                yield (self.__class__.__name__, d, 101, 'always')


class TicketOwnerSubscriber(Component):
    """Allows ticket owners to subscribe to their tickets."""

    implements(IAnnouncementDefaultSubscriber,
               IAnnouncementSubscriber)

    default_on = BoolOption("announcer", "always_notify_owner", 'true',
        """The always_notify_owner option mimics the option of the same name
        in the notification section, except users can override it in their
        preferences.
        """)

    default_distributor = ListOption("announcer",
        "always_notify_owner_distributor", "email",
        doc="""Comma-separated list of distributors to send the message to
        by default.  ex. email, xmpp
        """)

    # IAnnouncementSubscriber methods

    def matches(self, event):
        if event.realm != "ticket":
            return
        if event.category not in ('created', 'changed', 'attachment added'):
            return
        ticket = event.target

        if (not ticket['owner'] or ticket['owner'] == 'anonymous') and \
                not 'owner' in event.changes:
            return

        sid = sid_old = None
        if ticket['owner'] and ticket['owner'] != 'anonymous':
            if re.match(r'^[^@]+@.+', ticket['owner']):
                sid, auth, addr = None, 0, ticket['owner']
            else:
                sid, auth, addr = ticket['owner'], 1, None
        if 'owner' in event.changes:
            previous_owner = event.changes['owner']
            if re.match(r'^[^@]+@.+', previous_owner):
                sid_old, auth_old, addr_old = None, 0, previous_owner
            else:
                sid_old, auth_old, addr_old = previous_owner, 1, None

        # Default subscription
        for s in self.default_subscriptions():
            if sid:
                yield (s[0], s[1], sid, auth, addr, None, s[2], s[3])
            if sid_old:
                yield (s[0], s[1], sid_old, auth_old, addr_old, None, s[2],
                       s[3])
        if sid:
            klass = self.__class__.__name__
            for s in Subscription.find_by_sids_and_class(self.env,
                    ((sid, auth),), klass):
                yield s.subscription_tuple()
        if sid_old:
            klass = self.__class__.__name__
            for s in Subscription.find_by_sids_and_class(self.env,
                    ((sid_old, auth_old),), klass):
                yield s.subscription_tuple()

    def description(self):
        return _("notify me when a ticket that I own is created or modified")

    def requires_authentication(self):
        return True

    # IAnnouncementDefaultSubscriber method
    def default_subscriptions(self):
        if self.default_on:
            for d in self.default_distributor:
                yield (self.__class__.__name__, d, 101, 'always')


class TicketReporterSubscriber(Component):
    """Allows the users to subscribe to tickets that they report."""

    implements(IAnnouncementDefaultSubscriber,
               IAnnouncementSubscriber)

    default_on = BoolOption("announcer", "always_notify_reporter", 'true',
        """The always_notify_reporter will notify the ticket reporter when a
        ticket is modified by default.
        """)

    default_distributor = ListOption("announcer",
        "always_notify_reporter_distributor", "email",
        doc="""Comma-separated list of distributors to send the message to
        by default.  ex. email, xmpp
        """)

    # IAnnouncementSubscriber methods

    def matches(self, event):
        if event.realm != "ticket":
            return
        if event.category not in ('created', 'changed', 'attachment added'):
            return

        ticket = event.target
        if not ticket['reporter'] or ticket['reporter'] == 'anonymous':
            return

        if re.match(r'^[^@]+@.+', ticket['reporter']):
            sid, auth, addr = None, 0, ticket['reporter']
        else:
            sid, auth, addr = ticket['reporter'], 1, None

        # Default subscription
        for s in self.default_subscriptions():
            yield (s[0], s[1], sid, auth, addr, None, s[2], s[3])

        if sid:
            klass = self.__class__.__name__
            for s in Subscription.find_by_sids_and_class(self.env,
                    ((sid,auth),), klass):
                yield s.subscription_tuple()

    def description(self):
        return _("notify me when a ticket that I reported is modified")

    def requires_authentication(self):
        return True

    # IAnnouncementDefaultSubscriber method
    def default_subscriptions(self):
        if self.default_on:
            for d in self.default_distributor:
                yield (self.__class__.__name__, d, 101, 'always')


class TicketUpdaterSubscriber(Component):
    """Allows updaters to subscribe to their own updates."""

    implements(IAnnouncementDefaultSubscriber,
               IAnnouncementSubscriber)

    default_on = BoolOption("announcer", "never_notify_updater", 'false',
        """The never_notify_updater stops users from recieving announcements
        when they update tickets.
        """)

    default_distributor = ListOption("announcer",
        "never_notify_updater_distributor", "email",
        doc="""Comma-separated list of distributors to send the message to
        by default.  ex. email, xmpp
        """)

    # IAnnouncementSubscriber methods

    def matches(self, event):
        if event.realm != "ticket":
            return
        if event.category not in ('created', 'changed', 'attachment added'):
            return
        if not event.author or event.author == 'anonymous':
            return

        if re.match(r'^[^@]+@.+', event.author):
            sid, auth, addr = None, 0, event.author
        else:
            sid, auth, addr = event.author, 1, None

        # Default subscription
        for s in self.default_subscriptions():
            yield (s[0], s[1], sid, auth, addr, None, s[2], s[3])

        if sid:
            klass = self.__class__.__name__
            for s in Subscription.find_by_sids_and_class(self.env,
                    ((sid,auth),), klass):
                yield s.subscription_tuple()

    def description(self):
        return _("notify me when I update a ticket")

    def requires_authentication(self):
        return True

    # IAnnouncementDefaultSubscriber method
    def default_subscriptions(self):
        if self.default_on:
            for d in self.default_distributor:
                yield (self.__class__.__name__, d, 100, 'never')
