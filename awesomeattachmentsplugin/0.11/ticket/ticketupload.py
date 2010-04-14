import csv
from datetime import datetime
import os
import pkg_resources
import re
from StringIO import StringIO
import time
import unicodedata

from genshi.core import Markup
from genshi.builder import tag

from trac.attachment import AttachmentModule
from trac.config import BoolOption, Option, IntOption, _TRUE_VALUES
from trac.core import *
from trac.mimeview.api import Mimeview, IContentConverter, Context
from trac.resource import Resource, get_resource_url, \
                         render_resource_link, get_resource_shortname
from trac.search import ISearchSource, search_to_sql, shorten_result
from trac.ticket.api import TicketSystem, ITicketManipulator, \
                            ITicketActionController
from trac.ticket.model import Milestone, Ticket, group_milestones
from trac.ticket.notification import TicketNotifyEmail
from trac.timeline.api import ITimelineEventProvider
from trac.util import get_reporter_id
from trac.util.compat import any, set
from trac.util.datefmt import to_timestamp, utc
from trac.util.text import CRLF, shorten_line, obfuscate_email_address, \
                           exception_to_unicode
from trac.util.presentation import separated
from trac.util.translation import _
from trac.versioncontrol.diff import get_diff_options, diff_blocks
from trac.web import IRequestHandler
from trac.web.chrome import add_link, add_script, add_stylesheet, \
                            add_warning, add_ctxtnav, prevnext_nav, Chrome, \
                            INavigationContributor, ITemplateProvider
from trac.wiki.formatter import format_to, format_to_html, format_to_oneliner
from trac.attachment import Attachment, AttachmentModule, \
                            LegacyAttachmentPolicy
from trac.ticket.web_ui import TicketModule

class TicketUploadModule(TicketModule):
  
  max_size = IntOption('attachment', 'max_size', 262144,
        """Maximum allowed file size (in bytes) for ticket and wiki 
        attachments.""")
  
  # ITemplateProvider methods

  # Merge our custom templates with the parent classes templates
  def get_templates_dirs(self):
    return [pkg_resources.resource_filename('trac.ticket', 'templates'),
            pkg_resources.resource_filename('ticket', 'templates')]
            
  def get_htdocs_dirs(self):
    from pkg_resources import resource_filename
    return [['up', resource_filename(__name__, 'htdocs')]]
  
  def _create_attachment(self, req, ticket, upload, description):
    if hasattr(upload, 'filename'):
      attachment = Attachment(self.env, 'ticket', ticket.id)
      
      if hasattr(upload.file, 'fileno'):
        size = os.fstat(upload.file.fileno())[6]
      else:
        upload.file.seek(0, 2) # seek to end of file
        size = upload.file.tell()
        upload.file.seek(0)
      if size == 0:
        raise TracError(_("Can't upload empty file"))
      
      # Maximum attachment size (in bytes)
      max_size = self.max_size
      if max_size >= 0 and size > max_size:
        raise TracError(_('Maximum attachment size: %(num)s bytes', num=max_size), _('Upload failed'))

      #Create proper filename
      filename = unicodedata.normalize('NFC', unicode(upload.filename, 'utf-8'))
      filename = filename.replace('\\', '/').replace(':', '/')
      filename = os.path.basename(filename)
      if not filename:
        raise TracError(_('No file uploaded'))
      
      attachment.description = description
      if 'author' in req.args:
        attachment.author = get_reporter_id(req, 'author')
      attachment.ipnr = req.remote_addr
             
      attachment.insert(filename, upload.file, size)

  def _do_create(self, req, ticket):
    ticket.insert()

    # Notify
    try:
      tn = TicketNotifyEmail(self.env)
      tn.notify(ticket, newticket=True)
    except Exception, e:
      self.log.error("Failure sending notification on creation of "
        "ticket #%s: %s", ticket.id, exception_to_unicode(e))

    # Redirect the user to the newly created ticket or add attachment
    if(isinstance(req.args['attachment[]'], list)):
      for i in range(len(req.args['attachment[]'])):
        self._create_attachment(req, ticket, req.args['attachment[]'][i], req.args['description[]'][i])
    else:
      self._create_attachment(req, ticket, req.args['attachment[]'], req.args['description[]'])

    if 'TICKET_VIEW' not in req.perm('ticket', ticket.id):
      req.redirect(req.href.newticket())
      
    req.redirect(req.href.ticket(ticket.id))
    
  def _process_newticket_request(self, req):
    #Override ticket.html template with our own template
    template, data, o = super(TicketUploadModule, self)._process_newticket_request(req)
    return 'ticketupload.html', data, None
  

