from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from ticketsidebarprovider import ITicketSidebarProvider
from trac.attachment import Attachment
from trac.attachment import AttachmentModule
from trac.config import Option
from trac.core import *
from trac.mimeview import Mimeview
from trac.web.api import ITemplateStreamFilter


class SidebarImage(Component):
    """add an image to the ticket sidebar"""

    implements(ITicketSidebarProvider)

    ### internal methods

    def image(self, ticket):
        """
        return the first image attachment
        or None if there aren't any
        """
        attachments = list(Attachment.select(self.env, 'ticket', ticket.id))
        mimeview = Mimeview(self.env)
        for attachment in attachments:
            mimetype = mimeview.get_mimetype(attachment.filename)
            if not mimetype or mimetype.split('/',1)[0] != 'image':
                continue
            return attachment

    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        """should the image be shown?"""
        return bool(self.image(ticket))

    def content(self, req, ticket):
        image = self.image(ticket)
        return tag.img(None, src=req.href('attachment', 'ticket', ticket.id, image.filename, format='raw'), alt=image.description)


class ImageFormFilter(Component):
    """add image submission to the ticket form"""

    implements(ITemplateStreamFilter)
    fieldset_id = Option('ticket-image', 'fieldset_id', 'properties', 
                         'fieldset after which to insert the form')
        
    ### methods for ITemplateStreamFilter

    """Filter a Genshi event stream prior to rendering."""

    def filter_stream(self, req, method, filename, stream, data):
        """Return a filtered Genshi event stream, or the original unfiltered
        stream if no match.

        `req` is the current request object, `method` is the Genshi render
        method (xml, xhtml or text), `filename` is the filename of the template
        to be rendered, `stream` is the event stream and `data` is the data for
        the current template.

        See the Genshi documentation for more information.
        """

        if filename == 'ticket.html' and not data['ticket'].exists:
            if not hasattr(self, 'loader'):
                from pkg_resources import resource_filename
                templates_dir = resource_filename(__name__, 'templates')
                self.loader = TemplateLoader(templates_dir,
                                             auto_reload=True)
            template = self.loader.load('image-upload.html')
            stream |= Transformer("//fieldset[@id='%s']" % self.fieldset_id).after(template.generate())
            stream |= Transformer("//form[@id='propertyform']").attr('enctype', "multipart/form-data")

        return stream
