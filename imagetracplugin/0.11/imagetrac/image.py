"""
ImageTrac:
a plugin for Trac to add images to tickets upon creaton
http://trac.edgewall.org
"""

from PIL import Image

from trac.attachment import Attachment
from trac.config import BoolOption
from trac.core import *
from trac.mimeview import Mimeview
from trac.ticket.api import ITicketChangeListener
from trac.ticket.api import ITicketManipulator
from trac.web.api import IRequestFilter

class ImageTrac(Component):

    implements(ITicketManipulator, ITicketChangeListener, IRequestFilter)

    mandatory_image = BoolOption('ticket', 'mandatory_image', 'false', 
                                 "Enforce a mandatory image for created tickets")

    ### methods for ITicketManipulator

    """Miscellaneous manipulation of ticket workflow features."""

    def prepare_ticket(self, req, ticket, fields, actions):
        """Not currently called, but should be provided for future
        compatibility."""

    def validate_ticket(self, req, ticket):
        """Validate a ticket after it's been populated from user input.
        
        Must return a list of `(field, message)` tuples, one for each problem
        detected. `field` can be `None` to indicate an overall problem with the
        ticket. Therefore, a return value of `[]` means everything is OK."""
        if not ticket.exists:
            image = req.args.get('ticket_image')
            if not hasattr(image, 'fp'):
                if self.mandatory_image:
                    return [('ticket_image', 'Images required for tickets. Please upload an image.')]
                else:
                    return []
            mimeview = Mimeview(self.env)
            mimetype = mimeview.get_mimetype(image.filename)
            if mimetype is None:
                return[('ticket_image', 'Uploaded file is not an image')]
            if mimetype.split('/',1)[0] != 'image':
                return [('ticket_image', 'Uploaded file is not an image, instead it is %s' % mimetype)]
            
            try:
                Image.open(image.file)
            except IOError, e:
                return[('ticket_image', str(e))]

        else:
            return []

        # store the image temporarily
        if not hasattr(self, 'image'):
            self.image = {}
        self.image[ticket['summary']] = req.args['ticket_image']


        return []

    ### methods for ITicketChangeListener

    """Extension point interface for components that require notification
    when tickets are created, modified, or deleted."""

    def ticket_changed(self, ticket, comment, author, old_values):
        """Called when a ticket is modified.
        
        `old_values` is a dictionary containing the previous values of the
        fields that have changed.
        """

    def ticket_created(self, ticket):
        """Called when a ticket is created."""
        if not hasattr(self, 'image'):
            # XXX should check if the image is mandatory
            return 
        image = self.image.pop(ticket['summary'], None)
        if image is None:
            # XXX should check if the image is mandatory
            return 
        attachment = Attachment(self.env, 'ticket', ticket.id)
        attachment.author = ticket['reporter']
        attachment.description = ticket['summary']
        image.file.seek(0,2) # seek to end of file
        size = image.file.tell()
        image.file.seek(0)
        attachment.insert(image.filename, image.file, size)

    def ticket_deleted(self, ticket):
        """Called when a ticket is deleted."""
        

    ### methods for IRequestFilter

    """Extension point interface for components that want to filter HTTP
    requests, before and/or after they are processed by the main handler."""

    def post_process_request(self, req, template, data, content_type):
        """Do any post-processing the request might need; typically adding
        values to the template `data` dictionary, or changing template or
        mime type.
        
        `data` may be update in place.

        Always returns a tuple of (template, data, content_type), even if
        unchanged.

        Note that `template`, `data`, `content_type` will be `None` if:
         - called when processing an error page
         - the default request handler did not return any result

        (Since 0.11)
        """

        if template == 'ticket.html':
            ticket = data['ticket']
            if ticket.exists:
                images = []
                for image in self.images(ticket):
                    images.append(req.href('attachment', 'ticket', 'ticket.id', image.filename, format='raw'))
            data['images'] = images
        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler

    

    ### internal methods

    def images(self, ticket):
        """returns images for a ticket"""
        
        
        attachments = list(Attachment.select(self.env, 'ticket', ticket.id))
        images = []
        mimeview = Mimeview(self.env)
        for attachment in attachments:
            mimetype = mimeview.get_mimetype(attachment.filename)
            if mimetype.split('/',1)[0] != 'image':
                continue
            images.append(attachment)
        return images
        
