#-*- coding: utf-8 -*-
#
# Copyright (c) 2010, Robert Corsaro
# Copyright (c) 2010,2012, Steffen Hoffmann
# 
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from genshi.template import NewTextTemplate, TemplateLoader

from trac.config import BoolOption, ListOption
from trac.core import Component, implements
from trac.perm import PermissionCache
from trac.web.chrome import Chrome

from announcer.api import AnnouncementEvent, AnnouncementSystem
from announcer.api import IAnnouncementDefaultSubscriber 
from announcer.api import IAnnouncementFormatter, IAnnouncementSubscriber
from announcer.api import IAnnouncementSubscriptionFilter
from announcer.api import _
from announcer.distributors.mail import IAnnouncementEmailDecorator
from announcer.model import Subscription
from announcer.util.mail import set_header, next_decorator

from acct_mgr.api import IAccountChangeListener


class AccountChangeEvent(AnnouncementEvent):
    def __init__(self, category, username, password=None, token=None):
        AnnouncementEvent.__init__(self, 'acct_mgr', category, None)
        self.username = username
        self.password = password
        self.token = token


class AccountManagerAnnouncement(Component):
    """Send announcements on account changes."""

    implements(
        IAccountChangeListener, # from AccountManagerPlugin
        IAnnouncementEmailDecorator,
        IAnnouncementFormatter,
        IAnnouncementDefaultSubscriber,
        IAnnouncementSubscriber,
        IAnnouncementSubscriptionFilter
    )

    categories = ('created', 'change', 'delete', 'reset', 'verify', 'approve')

    default_on = BoolOption("announcer", "always_notify_user_admins", True,
        """Sent user account notification to admin users per default, so they
        may opt-out individually instead of requiring everyone to opt-in.
        """)
    default_distributor = ListOption("announcer",
        "always_notify_user_admins_distributor", "email",
        doc="""Comma-separated list of distributors to send the message to
        by default.  ex. email, xmpp
        """)

    # IAccountChangeListener methods

    def user_created(self, username, password):
        self._notify('created', username, password)

    def user_password_changed(self, username, password):
        self._notify('change', username, password)

    def user_deleted(self, username):
        self._notify('delete', username)

    def user_password_reset(self, username, email, password):
        """User password has been reset.

        Note, that this is no longer final, and the old password could still
        be recovered before first successful login with the new password.
        """
        self._notify('reset', username, password)

    def user_email_verification_requested(self, username, token):
        self._notify('verify', username, token=token)

    def user_registration_approval_required(self, username):
        self._notify('approve', username)

    # IAnnouncementDefaultSubscriber method
    def default_subscriptions(self):
        if self.default_on:
            for d in self.default_distributor:
                yield (self.__class__.__name__, d, 101, 'always')

    # IAnnouncementSubscriber methods

    def subscriptions(self, event):
        if event.realm == 'acct_mgr':
            for subscriber in self._get_membership(event):
                self.log.debug("AccountManagerAnnouncement added '%s " \
                        "(%s)'", subscriber[1], subscriber[2])
                yield subscriber

    def matches(self, event):
        if event.realm != 'acct_mgr':
            return
        # DEVEL: Need a better plan, because the real issue is a missing
        #   user_* method on AccountManager changes.
        if not event.category in self.categories:
            return

        klass = self.__class__.__name__
        for i in Subscription.find_by_class(self.env, klass):
            yield i.subscription_tuple()

    def description(self):
        return _(
            """notify me on user account changes (`ACCTMGR_USER_ADMIN`
            required)""")

    def requires_authentication(self):
        # Unauthenticated users must never see that.
        return True

    # IAnnouncementSubscriptionFilter method
    def filter_subscriptions(self, event, subscriptions):
        action = 'ACCTMGR_USER_ADMIN'

        for subscription in subscriptions:
            if event.realm != 'acct_mgr':
                yield subscription
                continue

            # Make acct_mgr subscriptions available only for admins.
            sid, auth = subscription[1:3]
            # PermissionCache already takes care of sid = None
            if not auth:
                sid = 'anonymous'
            perm = PermissionCache(self.env, sid)
            if perm.has_permission(action):
                yield subscription
            else:
                self.log.debug(
                    "Filtering %s because of %s rule"
                    % (sid, self.__class__.__name__)
                )

    # IAnnouncementFormatter methods

    def styles(self, transport, realm):
        if realm == 'acct_mgr':
            yield 'text/plain'

    def alternative_style_for(self, transport, realm, style):
        if realm == 'acct_mgr' and style != 'text/plain':
            return 'text/plain'

    def format(self, transport, realm, style, event):
        if realm == 'acct_mgr' and style == 'text/plain':
            return self._format_plaintext(event)

    # IAnnouncementEmailDecorator method
    def decorate_message(self, event, message, decorates=None):
        if event.realm == "acct_mgr":
            prjname = self.env.project_name
            subject = '[%s] %s: %s' % (prjname, event.category, event.username)
            set_header(message, 'Subject', subject)
        return next_decorator(event, message, decorates)

    # Private methods

    def _notify(self, category, username, password=None, token=None):
        try:
            announcer = AnnouncementSystem(self.env)
            announcer.send(
                AccountChangeEvent(category, username, password, token)
            )
        except Exception, e:
            self.log.exception("Failure creating announcement for account "
                               "event %s: %s", username, category)

    def _format_plaintext(self, event):
        acct_templates = {
            'created': 'acct_mgr_user_change_plaintext.txt', 
            'change': 'acct_mgr_user_change_plaintext.txt', 
            'delete': 'acct_mgr_user_change_plaintext.txt', 
            'reset': 'acct_mgr_reset_password_plaintext.txt', 
            'verify': 'acct_mgr_verify_plaintext.txt',
            'approve': 'acct_mgr_approve_plaintext.txt'
        }
        data = {
            'account': {
                'action': event.category,
                'username': event.username,
                'password': event.password,
                'token': event.token
            },
            'project': {
                'name': self.env.project_name,
                'url': self.env.abs_href(),
                'descr': self.env.project_description
            },
            'login': {
                'link': self.env.abs_href.login()
            }
        }
        if event.category == 'verify':
            data['verify'] = {
                'link': self.env.abs_href.verify_email(token=event.token)
            }
        chrome = Chrome(self.env)
        dirs = []
        for provider in chrome.template_providers:
            dirs += provider.get_templates_dirs()
        templates = TemplateLoader(dirs, variable_lookup='lenient')
        template = templates.load(acct_templates[event.category], 
                                  cls=NewTextTemplate)
        if template:
            stream = template.generate(**data)
            output = stream.render('text')
        return output
