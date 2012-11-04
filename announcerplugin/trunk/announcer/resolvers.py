# -*- coding: utf-8 -*-
#
# Copyright (c) 2008, Stephen Hansen
# Copyright (c) 2009, Robert Corsaro
# Copyright (c) 2012, Steffen Hoffmann
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from trac.config import Option
from trac.core import Component, implements
from trac.util.compat import sorted

from announcer.api import IAnnouncementAddressResolver
from announcer.api import IAnnouncementPreferenceProvider
from announcer.api import _
from announcer.util.settings import SubscriptionSetting


class DefaultDomainEmailResolver(Component):
    implements(IAnnouncementAddressResolver)

    default_domain = Option('announcer', 'email_default_domain', '',
        """Default host/domain to append to address that do not specify one""")

    def get_address_for_name(self, name, authenticated):
        if self.default_domain:
            return '%s@%s' % (name, self.default_domain)
        return None


class SessionEmailResolver(Component):
    implements(IAnnouncementAddressResolver)

    def get_address_for_name(self, name, authenticated):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value
              FROM session_attribute
             WHERE sid=%s
               AND authenticated=%s
               AND name=%s
        """, (name, int(authenticated), 'email'))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

class SpecifiedEmailResolver(Component):
    implements(IAnnouncementAddressResolver, IAnnouncementPreferenceProvider)

    def get_address_for_name(self, name, authenticated):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute("""
            SELECT value
              FROM session_attribute
             WHERE sid=%s
               AND authenticated=1
               AND name=%s
        """, (name,'announcer_specified_email'))
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

    # IAnnouncementDistributor
    def get_announcement_preference_boxes(self, req):
        if req.authname != "anonymous":
            yield "emailaddress", _("Announcement Email Address")

    def render_announcement_preference_box(self, req, panel):
        cfg = self.config
        sess = req.session
        if req.method == "POST":
            opt = req.args.get('specified_email', '')
            sess['announcer_specified_email'] = opt
        specified = sess.get('announcer_specified_email', '')
        data = dict(specified_email = specified,)
        return "prefs_announcer_emailaddress.html", data

class SpecifiedXmppResolver(Component):
    implements(IAnnouncementAddressResolver, IAnnouncementPreferenceProvider)

    def __init__(self):
        self.setting = SubscriptionSetting(self.env, 'specified_xmpp')

    def get_address_for_name(self, name, authed):
        return self.setting.get_user_setting(name)[1]

    # IAnnouncementDistributor
    def get_announcement_preference_boxes(self, req):
        if req.authname != "anonymous":
            yield "xmppaddress", "Announcement XMPP Address"

    def render_announcement_preference_box(self, req, panel):
        if req.method == "POST":
            self.setting.set_user_setting(req.session,
                    req.args.get('specified_xmpp'))
        specified = self.setting.get_user_setting(req.session.sid)[1] or ''
        data = dict(specified_xmpp = specified,)
        return "prefs_announcer_xmppaddress.html", data
