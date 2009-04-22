from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from ticketsidebarprovider import ITicketSidebarProvider
from trac.attachment import Attachment
from trac.attachment import AttachmentModule
from trac.core import *
from trac.mimeview import Context
from trac.web.api import ITemplateStreamFilter


class SidebarImage(Component):
    """add an image to the ticket sidebar"""

    implements(ITicketSidebarProvider)

    ### internal methods
    def image(self, ticket):
        attachments = list(Attachment.select(self.env, 'ticket', ticket.id))
        if len(attachments):
            return attachments[0]

    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        """should the image be shown?"""
        if self.image(ticket):        
            return True
        else:
            return False

    def content(self, req, ticket):
        image = self.image(ticket)
        return tag.img(None, src=req.href('attachment', 'ticket', ticket.id, image.filename, format='raw'), alt=image.description)


class ImageFormFilter(Component):
    """add image submission to the ticket form"""

    implements(ITemplateStreamFilter)
        
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
            stream |= Transformer("//fieldset[@id='properties']").after(template.generate())
            stream |= Transformer("//form[@id='propertyform']").attr('enctype', "multipart/form-data")

        return stream
