# -*- coding: utf-8 -*-
#
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2010-2012, Steffen Hoffmann
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

"""Filters can remove subscriptions after they are collected.
"""
import re

from trac.core import *
from trac.config import ListOption
from trac.perm import PermissionCache

from announcer.api import IAnnouncementSubscriptionFilter
from announcer.api import _
from announcer.util import get_target_id


class DefaultPermissionFilter(Component):
    """DefaultPermissionFilter simply checks that each subscription
    has ${REALM}_VIEW permissions before allow the subscription notice
    to be sent.
    """
    implements(IAnnouncementSubscriptionFilter)

    exception_realms = ListOption('announcer', 'filter_exception_realms', '',
            """The PermissionFilter will filter an announcements for with the
            user doesn't have ${REALM}_VIEW permission.  If there is some
            realm that doesn't use a permission called ${REALM}_VIEW then
            you should add it to this list and create a custom filter to
            enforce it's permissions.  Be careful because permissions can be
            bypassed using the AnnouncerPlugin.
            """)

    def filter_subscriptions(self, event, subscriptions):
        if event.realm in self.exception_realms:
            return subscriptions

        action = '%s_VIEW' % event.realm.upper()
        for subscription in subscriptions:
            sid, auth = subscription[1:3]
            # PermissionCache already takes care of sid = None
            if not auth:
                sid = 'anonymous'
            perm = PermissionCache(self.env, sid)
            self.log.debug(
                'Checking *_VIEW permission on event for resource %s:%s'
                % (event.realm, resource_id)
            )
            resource_id = get_target_id(event.target)
            if perm.has_permission(action) and action in perm(event.realm,
                                                              resource_id):
                yield subscription
            else:
                self.log.debug(
                    "Filtering %s because of rule: DefaultPermissionFilter"
                    % sid
                )
