# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

import re

from email.utils import parseaddr
from genshi.template import NewTextTemplate, TemplateError

from trac import __version__ as trac_version
from trac.config import ListOption, Option
from trac.core import Component, implements
from trac.util.text import to_unicode

from announcer import __version__ as announcer_version
from announcer.distributors.mail import IAnnouncementEmailDecorator
from announcer.util.mail import msgid, next_decorator, set_header, uid_encode

"""Email decorators have the chance to modify emails or their headers, before
the email distributor sends them out.
"""

class ThreadingEmailDecorator(Component):
    """Add Message-ID, In-Reply-To and References message headers for resources.
    All message ids are derived from the properties of the ticket so that they
    can be regenerated later.
    """

    implements(IAnnouncementEmailDecorator)

    supported_realms = ListOption('announcer', 'email_threaded_realms',
        'ticket,wiki',
        doc="""These are realms with announcements that should be threaded
        emails.  In order for email threads to work, the announcer
        system needs to give the email recreatable Message-IDs based
        on the resources in the realm.  The resources must have a unique
        and immutable id, name or str() representation in it's realm
        """)

    def decorate_message(self, event, message, decorates=None):
        """
        Added headers to the outgoing email to track it's relationship
        with a ticket.

        References, In-Reply-To and Message-ID are just so email clients can
        make sense of the threads.
        """
        if to_unicode(event.realm) in self.supported_realms:
            uid = uid_encode(self.env.abs_href(), event.realm, event.target)
            email_from = self.config.get('announcer', 'email_from', 'localhost')
            _, email_addr = parseaddr(email_from)
            host = re.sub('^.+@', '', email_addr)
            mymsgid = msgid(uid, host)
            if event.category == 'created':
                set_header(message, 'Message-ID', mymsgid)
            else:
                set_header(message, 'In-Reply-To', mymsgid)
                set_header(message, 'References', mymsgid)

        return next_decorator(event, message, decorates)


class StaticEmailDecorator(Component):
    """The static ticket decorator implements a policy to -always- send an
    email to a certain address.

    Controlled via the always_cc and always_bcc option in the announcer section
    of the trac.ini.  If no subscribers are found, then even if always_cc and
    always_bcc addresses are specified, no announcement will be sent.  Since
    these fields are added after announcers subscription system, filters such
    as never_announce and never_notify author won't work with these addresses.

    These settings are considered dangerous if you are using the verify email
    or reset password features of the accountmanager plugin.
    """

    # FIXME: mark that emails as 'private' in AcctMgr and eval that mark here

    implements(IAnnouncementEmailDecorator)

    always_cc = Option("announcer", "email_always_cc", None,
        """Email addresses specified here will always
        be cc'd on all announcements.  This setting is dangerous if
        accountmanager is present.
        """)

    always_bcc = Option("announcer", "email_always_bcc", None,
        """Email addresses specified here will always
        be bcc'd on all announcements.  This setting is dangerous if
        accountmanager is present.
        """)

    def decorate_message(self, event, message, decorates=None):
        for k, v in {'Cc': self.always_cc, 'Bcc': self.always_bcc}.items():
            if v:
                self.log.debug("StaticEmailDecorator added '%s' "
                        "because of rule: email_always_%s"%(v, k.lower())),
                if message[k] and len(str(message[k]).split(',')) > 0:
                    recips = ", ".join([str(message[k]), v])
                else:
                    recips = v
                set_header(message, k, recips)
        return next_decorator(event, message, decorates)


class AnnouncerEmailDecorator(Component):
    """Add some boring headers that should be set."""

    implements(IAnnouncementEmailDecorator)

    def decorate_message(self, event, message, decorators):
        mailer = 'AnnouncerPlugin v%s on Trac v%s' % (
            announcer_version,
            trac_version
        )
        set_header(message, 'Auto-Submitted', 'auto-generated')
        set_header(message, 'Precedence', 'bulk')
        set_header(message, 'X-Announcer-Version', announcer_version)
        set_header(message, 'X-Mailer', mailer)
        set_header(message, 'X-Trac-Announcement-Realm', event.realm)
        set_header(message, 'X-Trac-Project', self.env.project_name)
        set_header(message, 'X-Trac-Version', trac_version)

        return next_decorator(event, message, decorators)


class TicketSubjectEmailDecorator(Component):
    """Formats ticket announcement subject headers based on the
    ticket_email_subject configuration.
    """

    implements(IAnnouncementEmailDecorator)

    ticket_email_subject = Option('announcer', 'ticket_email_subject',
            "Ticket #${ticket.id}: ${ticket['summary']} " \
                    "{% if action %}[${action}]{% end %}",
            """Format string for ticket email subject.  This is
               a mini genshi template that is passed the ticket
               event and action objects.""")

    def decorate_message(self, event, message, decorates=None):
        if event.realm == 'ticket':
            if 'status' in event.changes:
                action = 'Status -> %s' % (event.target['status'])
            template = NewTextTemplate(
                self.ticket_email_subject.encode('utf8'))
            # Create a fallback for invalid custom Genshi template in option.
            default_template = NewTextTemplate(
                Option.registry[('announcer', 'ticket_email_subject')
                    ].default.encode('utf8'))
            try:
                subject = template.generate(
                    ticket=event.target,
                    event=event,
                    action=event.category
                ).render('text', encoding=None)
            except TemplateError:
                # Use fallback template.
                subject = default_template.generate(
                    ticket=event.target,
                    event=event,
                    action=event.category
                ).render('text', encoding=None)

            prefix = self.config.get('announcer', 'email_subject_prefix')
            if prefix == '__default__':
                prefix = '[%s] ' % self.env.project_name
            if prefix:
                subject = "%s%s" % (prefix, subject)
            if event.category != 'created':
                subject = 'Re: %s' % subject
            set_header(message, 'Subject', subject)

        return next_decorator(event, message, decorates)


class TicketAddlHeaderEmailDecorator(Component):
    """Adds X-Announcement-(id,priority and severity) headers to ticket
    emails.  This is useful for automated handling of incoming emails or
    customized filtering.
    """

    implements(IAnnouncementEmailDecorator)

    def decorate_message(self, event, message, decorates=None):
        if event.realm == 'ticket':
            for k in ('id', 'priority', 'severity'):
                name = 'X-Announcement-%s'%k.capitalize()
                set_header(message, name, event.target[k])

        return next_decorator(event, message, decorates)


class WikiSubjectEmailDecorator(Component):
    """Formats wiki announcement subject headers based on the
    wiki_email_subject configuration.
    """

    implements(IAnnouncementEmailDecorator)

    wiki_email_subject = Option('announcer', 'wiki_email_subject',
            "Page: ${page.name} ${action}",
            """Format string for the wiki email subject.  This is a
               mini genshi template and it is passed the page, event
               and action objects.""")

    def decorate_message(self, event, message, decorates=None):
        if event.realm == 'wiki':
            template = NewTextTemplate(self.wiki_email_subject.encode('utf8'))
            subject = template.generate(
                page=event.target,
                event=event,
                action=event.category
            ).render('text', encoding=None)

            prefix = self.config.get('announcer', 'email_subject_prefix')
            if prefix == '__default__':
                prefix = '[%s] ' % self.env.project_name
            if prefix:
                subject = "%s%s"%(prefix, subject)
            if event.category != 'created':
                subject = 'Re: %s'%subject
            set_header(message, 'Subject', subject)

        return next_decorator(event, message, decorates)
