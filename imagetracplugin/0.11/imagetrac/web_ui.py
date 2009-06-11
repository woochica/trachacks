from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from imagetrac.image import ImageTrac
from pkg_resources import resource_filename
from ticketsidebarprovider import ITicketSidebarProvider
from trac.attachment import Attachment
from trac.attachment import AttachmentModule
from trac.config import Option
from trac.core import *
from trac.mimeview import Mimeview
from trac.web.api import IRequestFilter
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.web.chrome import add_stylesheet
from trac.web.chrome import Chrome
from trac.web.chrome import ITemplateProvider


class SidebarImage(Component):
    """add an image to the ticket sidebar"""

    implements(ITicketSidebarProvider, ITemplateProvider)

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
            return attachment.filename

    ### methods for ITicketSidebarProvider

    def enabled(self, req, ticket):
        """should the image be shown?"""
        imagetrac = self.env.components.get(ImageTrac)
        if imagetrac:
            images = imagetrac.images(ticket, req.href)
            for image in images.values():
                if 'default' in image:
                    return True
        else:
            return bool(self.image(ticket))

    def content(self, req, ticket):
        chrome = Chrome(self.env)
        template = chrome.load_template('image-sidebar.html')
        imagetrac = self.env.components.get(ImageTrac)
        if imagetrac:
            images = imagetrac.images(ticket, req.href)
            display = 'default'
        else:
            image = self.image(ticket)
            link = req.href('attachment', 'ticket', ticket.id, image, format='raw')
            images = dict(image=dict(original=link))
            display = 'original'
        return template.generate(display=display, images=images)


    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []


    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [ resource_filename(__name__, 'templates') ]



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

        if filename == 'ticket.html':
            chrome = Chrome(self.env)
            template = chrome.load_template('image-upload.html')
            stream |= Transformer("//fieldset[@id='%s']" % self.fieldset_id).after(template.generate())
            stream |= Transformer("//form[@id='propertyform']").attr('enctype', "multipart/form-data")

        return stream


    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return []


    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return [ resource_filename(__name__, 'templates') ]


class Galleria(Component):

    implements(ITemplateProvider, IRequestFilter)

    ### methods for ITemplateProvider

    """Extension point interface for components that provide their own
    ClearSilver templates and accompanying static resources.
    """

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('imagetrac', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return []

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
            add_stylesheet(req, 'imagetrac/css/galleria.css')
            add_script(req, 'imagetrac/js/jquery.galleria.js')
            add_script(req, 'imagetrac/js/init_galleria.js')
            
        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler
