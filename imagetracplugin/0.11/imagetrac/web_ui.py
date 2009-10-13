from componentdependencies import IRequireComponents
from genshi.builder import tag
from genshi.filters import Transformer
from genshi.template import TemplateLoader
from imagetrac.image import ImageTrac
from imagetrac.default_image import DefaultTicketImage
from pkg_resources import resource_filename
from ticketsidebarprovider import ITicketSidebarProvider
from ticketsidebarprovider import TicketSidebarProvider
from trac.attachment import Attachment
from trac.attachment import AttachmentModule
from trac.config import Option
from trac.core import *
from trac.mimeview import Mimeview
from trac.web.api import IRequestFilter
from trac.web.api import IRequestHandler
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import add_script
from trac.web.chrome import add_stylesheet
from trac.web.chrome import Chrome
from trac.web.chrome import ITemplateProvider


class SidebarImage(Component):
    """add an image to the ticket sidebar"""

    implements(ITicketSidebarProvider, ITemplateProvider, IRequireComponents)

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

    ### method for IRequireComponents
    
    def requires(self):
        return [ TicketSidebarProvider ]

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
        imagetrac = ImageTrac(self.env)
        if imagetrac:
            images = imagetrac.images(ticket, req.href)
            display = 'default'
        else:
            image = self.image(ticket)
            link = req.href('attachment', 'ticket', ticket.id, image, format='raw')
            images = dict(image=dict(original=link))
            display = 'original'

        # default ticket image
        default = None
        if self.env.is_component_enabled(DefaultTicketImage):
            default = DefaultTicketImage(self.env).default_image(ticket.id)

        # generate the template
        return template.generate(display=display, 
                                 images=images,
                                 req=req,
                                 default=default,
                                 ticket=ticket)


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
    """
    adds Galleria for Trac
    see: http://devkick.com/lab/galleria/
    """


    implements(ITemplateProvider, IRequestFilter, IRequireComponents)

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
            if not 'images' in data:
                ImageTrac(self.env).post_process_request(req, template, data, content_type)

            # add galleria if more than one image
            if len(data['images']) > 1:
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

    ### method for IRequireComponents

    def requires(self):
        return [ ImageTrac ]


class TicketImageHandler(Component):
    """
    web handler for returning images for a ticket
    """

    
    implements(IRequestHandler, IRequireComponents)

    ### method for IRequireComponents
        
    def requires(self):
        return [ DefaultTicketImage ]

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        if req.method == 'GET':
            
            try:
                ticket_id, size = self.ticket_id_and_size(req.path_info)
                return True
            except:
                return False

        # set default image
        if req.method == 'POST' and 'TICKET_ADMIN' in req.perm:
            path = req.path_info.strip('/').split('/')
            if len(path) != 3:
                return False
            if path[0] != 'ticket' or path[2] != 'image':
                return False
            try:
                ticket_id = int(path[1])
            except ValueError:
                return False
            return True
            

    def process_request(self, req):
        """Process the request. For ClearSilver, return a (template_name,
        content_type) tuple, where `template` is the ClearSilver template to use
        (either a `neo_cs.CS` object, or the file name of the template), and
        `content_type` is the MIME type of the content. For Genshi, return a
        (template_name, data, content_type) tuple, where `data` is a dictionary
        of substitutions for the template.

        For both templating systems, "text/html" is assumed if `content_type` is
        `None`.

        Note that if template processing should not occur, this method can
        simply send the response itself and not return anything.
        """

        # handle image setting
        if req.method == 'POST':
            self.set_default_image(req)
            req.redirect(req.path_info)

        # GET default image
        ticket_id, size = self.ticket_id_and_size(req.path_info)
        image = DefaultTicketImage(self.env).default_image(ticket_id, size)
        assert image is not None # TODO better
        images = ImageTrac(self.env).images(ticket_id)
        attachment = Attachment(self.env, 'ticket', ticket_id, images[image][size])
        mimeview = Mimeview(self.env)
        mimetype = mimeview.get_mimetype(attachment.filename)
        req.send(attachment.open().read(), mimetype)


    ### internal methods

    def ticket_id_and_size(self, path_info):
        imagetrac = ImageTrac(self.env)
        sizes = imagetrac.sizes().keys()
        path = path_info.strip('/').split('/')
        if len(path) == 3:
            path.append('default')
        if len(path) != 4:
            return None
        if path[0] != 'ticket':
            return None
        try:
            ticket_id = int(path[1])
        except ValueError:
            return None
        if path[2] != 'image':
            return None
        if path[3] not in sizes + [ 'original' ]:
            return None
        return (ticket_id, path[3])
        
    def set_default_image(self, req):
        default_ticket_image = DefaultTicketImage(self.env)

