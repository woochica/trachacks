import fnmatch
import unicodedata
import os

from pkg_resources import resource_filename

from trac.core import *

from trac.config import ListOption
from trac.web.api import IRequestFilter
from trac.web.api import IRequestHandler
from trac.web.chrome import add_script
from trac.web.chrome import add_link
from trac.web.chrome import Chrome
from trac.web.chrome import ITemplateProvider 
from trac.web.chrome import ITemplateStreamFilter
from trac.web.href import Href
from trac.ticket.web_ui import TicketModule
from trac.config import IntOption
from trac.util.translation import _
from trac.ticket.notification import TicketNotifyEmail
from trac.attachment import Attachment
from trac.util import get_reporter_id

class AwesomeAttachments(Component):
  
  implements(ITemplateProvider, IRequestFilter)
  
  prefix = "awesomeattachments"
  
  ### methods for ITemplateProvider
  def get_htdocs_dirs(self):
    return [(self.prefix, resource_filename(__name__, 'htdocs'))]

  def get_templates_dirs(self):
    return []
  
  ### methods for IRequestFilter
  def post_process_request(self, req, template, data, content_type):
    if template == 'ticket.html' and req.path_info.rstrip() == '/newticket':
      add_script(req, '%s/js/awesome.js' % self.prefix)
      href = req.href
      href = href.chrome
      add_link(req, 'image', href('%s/images/add.png' % self.prefix), 'add', 'text/png', 'add-image')
      add_link(req, 'image', href('%s/images/delete.png' % self.prefix), 'delete', 'text/png', 'delete-image')
      add_link(req, 'image', href('%s/images/edit.png' % self.prefix), 'edit', 'text/png', 'edit-image')
      
    return (template, data, content_type)
    
  def pre_process_request(self, req, handler):
    return handler
    
class TicketUploadModule(TicketModule):

  max_size = IntOption('attachment', 'max_size', 262144,
        """Maximum allowed file size (in bytes) for ticket and wiki 
        attachments.""")
  
  def _create_attachment(self, req, ticket, upload, description):
    if hasattr(upload, 'filename'):
      attachment = Attachment(self.env, 'ticket', ticket.id)
      
      if hasattr(upload.file, 'fileno'):
        size = os.fstat(upload.file.fileno())[6]
      else:
        upload.file.seek(0, 2)
        size = upload.file.tell()
        upload.file.seek(0)
      if size == 0:
        raise TracError(_("Can't upload empty file"))
        
      max_size = self.max_size
      if max_size >= 0 and size > max_size:
        raise TracError(_('Maximum attachment size: %(num)s bytes', num=max_size), _('Upload failed'))
        
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
        "ticket #%s: %s", ticket.id, e)

    # Redirect the user to the newly created ticket or add attachment
    if(isinstance(req.args['attachment[]'], list)):
      for i in range(len(req.args['attachment[]'])):
        self._create_attachment(req, ticket, req.args['attachment[]'][i], req.args['description[]'][i])
    else:
      self._create_attachment(req, ticket, req.args['attachment[]'], req.args['description[]'])

    if 'TICKET_VIEW' not in req.perm('ticket', ticket.id):
      req.redirect(req.href.newticket())

    req.redirect(req.href.ticket(ticket.id))
    
    

