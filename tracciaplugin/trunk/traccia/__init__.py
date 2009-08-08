#
# (C) 2008,2009 Mikhail Gusarov <dottedmag@dottedmag.net>
# (C) 2008 Igor Stroh <igor@rulim.de>
#
# GPLv2 or later
#

'''
CIA Trac notification tool.
'''

from trac.core import *
from trac.wiki.api import IWikiChangeListener
from trac.wiki.model import WikiPage
from trac.attachment import IAttachmentChangeListener
from trac.ticket.api import ITicketChangeListener

from trac.resource import get_resource_url, get_resource_name

import threading
import xmlrpclib
from xml.sax import saxutils
from time import mktime

PROJECT_NAME = 'ExampleProject'
SERVICE_URL = 'http://cia.vc'

TICKET_FIELDS = [
    'status',
    'owner',
    'description',
    'summary',
    'reporter',
    'type',
    'milestone',
    'priority',
    'version',
    'keywords',
    'component'
]

message_template = """
<message>
  <generator>
    <name>Trac wiki CIA client</name>
    <version>0.1</version>
    <url>http://trac-hacks.org/wiki/TracCiaPlugin</url>
  </generator>
  %(timestamp)s
  <source>
    <project>%(project)s</project>
    <branch>%(component)s</branch>
    <module></module>
  </source>
  <body>
    <commit>
      <author>%(author)s</author>
      %(version)s
      <log>%(log)s</log>
      <url>%(url)s</url>
    </commit>
  </body>
</message>
"""

def authorinfo(author):
    if author:
        return author
    else:
        return 'anonymous'

def esc(s):
    return saxutils.escape(s)

def smart_truncate(content, length=100, suffix='...'):
    """
    Smart string truncate with ellipsis and whitespace collapsing.
    """
    content = ' '.join(content.split())
    if len(content) <= length:
        return content
    else:
        if ' ' in content[:length]:
            # Find the last space (maybe right after cutoff point) and cut the string
            return content[:content[:length+1].rindex(' ')] + suffix
        else:
            return content[:length]  + suffix

class CiaNotificationComponent(Component):
    implements(IWikiChangeListener)
    implements(IAttachmentChangeListener)
    implements(ITicketChangeListener)

    def __init__(self):
        self.service_url = self.config.get('traccia', 'service_url') or SERVICE_URL
        self.project_name = self.config.get('traccia', 'project_name') or PROJECT_NAME
        self.dry_run = self.config.get('traccia', 'dry_run') or False
        self.wiki_notifications = self.config.get('traccia', 'wiki_notifications') or True
        self.tickets_notifications = self.config.get('traccia', 'tickets_notifications') or True

    def send_message(self, message):
        threading.Thread(args = (message,), target=self._send_message).start()

    def _send_message(self, message):
        if self.dry_run:
            self.env.log.debug(message)
        else:
            xmlrpclib.Server(self.service_url).hub.deliver(message)

    def make_args(self, args):
        args.update({
            'project': self.project_name
        })
        return args

    def format_and_send_wikipage_notification(self,
                                page,
                                action,
                                author = '',
                                comment = None,
                                version = None,
                                timestamp = None):
        if not self.wiki_notifications:
            return

        if action == 'added':
            page = WikiPage(self.env, page.name, 1)
            author = page.author
            version = page.version

        url = get_resource_url(self.env, page.resource, self.env.abs_href)

        args = self.make_args({
            'url': esc(url),
            'author': esc(author),
            'component': page.resource.realm
        })

        if timestamp:
            args['timestamp'] = '<timestamp>' + \
                esc(str(int(mktime(timestamp.timetuple())))) + '</timestamp>'
        else:
            args['timestamp'] = ''

        if action == 'added':
            args['log'] = esc(page.name + ' page has been created (' + esc(url) + ')')
            args['version'] = ''
        elif action == 'changed':
            diff_url = self.env.abs_href('wiki', page.name, action='diff', version=str(version))
            args['log'] = esc(page.name + ' has been changed')
            if comment:
                args['log'] += esc(': ' + smart_truncate(comment, 150))
            args['log'] += ' (' + esc(diff_url) + ')'
            args['version'] = '<version>' + esc(str(version)) + '</version>'
        elif action == 'deleted':
            args['log'] = esc(page.name + ' page has been removed')
            args['version'] = ''
        else:
            raise Exception('Unknown action type')

        self.send_message(message_template % args)


    def format_and_send_attachment_notification(self, attachment, action):
        if not self.tickets_notifications:
            return

        args = self.make_args({
            'component': esc(attachment.parent_realm),
            'timestamp': ''
        })

        if action == 'added':
            args['author'] = esc(authorinfo(attachment.author))
            args['url'] = esc(get_resource_url(self.env, attachment.resource, self.env.abs_href))
            desc = attachment.description and (" '" + attachment.description + "'") or ""
            args['log'] = esc('File ' + attachment.filename + ("%s has been attached to " % desc) + get_resource_name(self.env, attachment.resource.parent))
            args['version'] = ''
        elif action == 'deleted':
            args['author'] = ''
            args['log'] = esc('File ' + attachment.filename + ' has been deleted from ' + get_resource_name(self.env, attachment.resource.parent))
            args['version'] = ''
            args['url'] = esc(get_resource_url(self.env, attachment.resource.parent, self.env.abs_href))
        else:
            raise Exception('Unknown action type')

        self.send_message(message_template % args)

    def format_and_send_ticket_notification(self, ticket, action, **kwargs):
        if not self.tickets_notifications:
            return

        version = ticket.values.get('version', '')
        milestone = ticket.values.get('milestone', '')
        status = ticket.values.get('status')
        is_new = status == 'new'
        t_url = get_resource_url(self.env, ticket.resource, self.env.abs_href)

        if action == 'created':
            author = ticket.values.get('reporter', 'anonymous')
        else:
            author = kwargs.get('author', 'anonymous')

        args = self.make_args({
            'component': 'tickets/' + esc(ticket.values.get('component', '')),
            'timestamp': '',
            'author': esc(author),
            'version': '<version>#' + esc(str(ticket.id)) + '</version>'
        })
        summary = ticket.values.get('summary', '')
        if action == 'deleted':
            args['url'] = t_url
            args['log'] = esc('%shas been deleted' % (summary and ' (' + summary+ ') ' or ''))
        elif action == 'created':
            args['url'] = t_url + '/' + str(ticket.id)
            args['log'] = 'Created ['+ticket['type']+']: ('+ticket['summary']+')' + (version and (' in ' + version) or '')
            args['log'] += ' (' + t_url + '/' + str(ticket.id) + ')'
        elif action == 'changed':
            old = kwargs.get('old_values', {})
            db = self.env.get_db_cnx()
            cursor = db.cursor()
            cursor.execute("SELECT count(*) FROM ticket_change WHERE ticket = %s and field = 'comment'" % (ticket.id));
            r = cursor.fetchone()
            num_comments = int(r and r[0] or 0)
            if num_comments:
                t_url += '#comment:%s' % (num_comments,)
            log = ''
            if old.get('status', None):
                if log: log += '; '
                log += 'status <- ' + status
            if old.get('version', None):
                if log: log += '; '
                log += 'version <- ' + version
            if old.get('milestone', None):
                if log: log += '; '
                log += 'milestone <- ' + milestone
            old_owner = old.get('owner', None)
            if old_owner:
                if author == ticket.values.get('owner'):
                    if log: log += '; '
                    log += "took over the ticket from " + old_owner
                else:
                    if log: log += '; '
                    log += 'owner <- ' + ticket.values.get('owner')
            changes = []
            for key in TICKET_FIELDS:
                if old.get(key, None) is not None and key not in ('owner', 'status', 'version', 'milestone'):
                    changes.append(key)
            if changes:
                if log: log += '; '
                log += "changed " + ', '.join(changes)
            log += ' (' + t_url + ')'
            comment = kwargs.get('comment', None)
            if comment:
                log += ': ' + esc(smart_truncate(comment, 150))
            args['url'] = t_url
            args['log'] = esc(log)
        else:
            raise Exception('Unknown action type')

        self.send_message(message_template % args)

    ## IWikiChangeListener interface impl
    def wiki_page_added(self, page):
        self.format_and_send_wikipage_notification(page, 'added')
    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self.format_and_send_wikipage_notification(page, 'changed', author, comment, version, t)
    def wiki_page_deleted(self, page):
        self.format_and_send_wikipage_notification(page, 'deleted')

    ## IAttachmentChangeListener interface impl
    def attachment_added(self, attachment):
        self.format_and_send_attachment_notification(attachment, 'added')
    def attachment_deleted(self, attachment):
        self.format_and_send_attachment_notification(attachment, 'deleted')

    ## ITicketChangeListener interface impl
    def ticket_created(self, ticket):
        self.format_and_send_ticket_notification(ticket, 'created')

    def ticket_changed(self, ticket, comment, author, old_values):
        self.format_and_send_ticket_notification(ticket, 'changed', comment=comment, author=author, old_values=old_values)

    def ticket_deleted(self, ticket):
        self.format_and_send_ticket_notification(ticket, 'deleted')
