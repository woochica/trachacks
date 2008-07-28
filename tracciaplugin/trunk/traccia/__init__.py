#
# (C) 2008 Mikhail Gusarov <dottedmag@dottedmag.net>
# GPLv2 or later
#

'''
CIA Trac notification tool.
'''

from trac.core import *
from trac.wiki.api import IWikiChangeListener
from trac.attachment import IAttachmentChangeListener
from trac.ticket.api import ITicketChangeListener

from trac.resource import get_resource_url, get_resource_name

import threading
import xmlrpclib
from xml.sax import saxutils
from time import mktime

### User-changeable settings ###

PROJECT_NAME = 'ExampleProject'
SERVICE_URL = 'http://cia.vc'

DRY_RUN = False

### End of user-changeable settings ###

message_template = """
<message>
  <generator>
    <name>Trac wiki CIA client</name>
    <version>0.1</version>
    <url>http://traccia.dottedmag.net/</url>
  </generator>
  %(timestamp)s
  <source>
    <project>""" + PROJECT_NAME + """</project>
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

class CiaNotificationComponent(Component):
    implements(IWikiChangeListener)
    implements(IAttachmentChangeListener)
#    implements(ITicketChangeListener)

    def send_message(self, message):
        threading.Thread(args = (message,), target=self._send_message).start()

    def _send_message(self, message):
        if DRY_RUN:
            self.env.log.debug(message)
        else:
            xmlrpclib.Server(SERVICE_URL).hub.deliver(message)

    def format_and_send_message(self,
                                page,
                                action,
                                author = '',
                                comment = None,
                                version = None,
                                timestamp = None):
        url = get_resource_url(self.env, page.resource, self.env.abs_href)

        args = { 'url': esc(url),
                 'author': esc(author),
                 'component': page.resource.realm }

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
                args['log'] += esc(': ' + comment)
            args['log'] += ' (' + esc(diff_url) + ')'
            args['version'] = '<version>' + esc(str(version)) + '</version>'
        elif action == 'deleted':
            args['log'] = esc(page.name + ' page has been removed')
            args['version'] = ''
        else:
            raise Exception('Unknown action type')

        self.send_message(message_template % args)


    def format_and_send_attachment_notification(self,
                                                attachment,
                                                action):

        args = {
            'component': esc(attachment.parent_realm),
            'timestamp': ''
        }

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

    def wiki_page_added(self, page):
        self.format_and_send_message(page, 'added')
    def wiki_page_changed(self, page, version, t, comment, author, ipnr):
        self.format_and_send_message(page, 'changed', author, comment, version, t)
    def wiki_page_deleted(self, page):
        self.format_and_send_message(page, 'deleted')

    def attachment_added(self, attachment):
        self.format_and_send_attachment_notification(attachment, 'added')
    def attachment_deleted(self, attachment):
        self.format_and_send_attachment_notification(attachment, 'deleted')
