# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2010-2012, Steffen Hoffmann
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Filters can remove subscriptions after they are collected.

This is commonly done based on access restrictions for Trac realm and
resource ID, that the event is referring to (alias 'event target').
In some contexts like AccountManagerPlugin account change notifications
(realm 'acct_mgr') an `IAnnouncementSubscriptionFilter` implementation is
essential for meaningful operation
(see announcer.opt.acct_mgr.announce.AccountManagerAnnouncement).

Only subscriptions, that pass all filters, can trigger a distributor to emit a
notification about an event for shipment via one of its associated transports.
"""

from trac.core import Component, implements
from trac.config import ListOption
from trac.perm import PermissionCache

from announcer.api import IAnnouncementSubscriptionFilter
from announcer.api import _, N_
from announcer.util import get_target_id


class DefaultPermissionFilter(Component):
    """Simple view permission enforcement for common Trac realms.

    It checks, that each subscription has ${REALM}_VIEW permission for the
    corresponding event target, before the subscription is allowed to
    propagate to distributors.
    """
    implements(IAnnouncementSubscriptionFilter)

    exception_realms = ListOption(
            'announcer', 'filter_exception_realms', 'acct_mgr', doc=N_(
            """The PermissionFilter will filter announcements, for which the
            user doesn't have ${REALM}_VIEW permission.  If there is some
            realm that doesn't use a permission called ${REALM}_VIEW, then
            you should add it to this list and create a custom filter to
            enforce it's permissions.  Be careful, or permissions could be
            bypassed using the AnnouncerPlugin.
            """))

    def filter_subscriptions(self, event, subscriptions):
        action = '%s_VIEW' % event.realm.upper()

        for subscription in subscriptions:
            if event.realm in self.exception_realms:
                yield subscription
                continue

            sid, auth = subscription[1:3]
            # PermissionCache already takes care of sid = None
            if not auth:
                sid = 'anonymous'
            perm = PermissionCache(self.env, sid)
            resource_id = get_target_id(event.target)
            self.log.debug(
                'Checking *_VIEW permission on event for resource %s:%s'
                % (event.realm, resource_id)
            )
            if perm.has_permission(action) and action in perm(event.realm,
                                                              resource_id):
                yield subscription
            else:
                self.log.debug(
                    "Filtering %s because of %s rule" 
                    % (sid, self.__class__.__name__)
                )
