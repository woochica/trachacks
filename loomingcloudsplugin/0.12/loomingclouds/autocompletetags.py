"""
TagsRequestHandler:
a plugin for Trac for autocompletion of tags
http://trac.edgewall.org
"""
from pkg_resources import resource_filename
from trac.core import *
from trac.web.api import IRequestHandler
from trac.web.api import IRequestFilter
from tractags.api import TagSystem
from trac.web.chrome import ITemplateProvider
from trac.web.chrome import add_script
from trac.web.chrome import add_stylesheet


class TagsRequestHandler(Component):

    implements(IRequestHandler, IRequestFilter)

    ### methods for IRequestHandler

    """Extension point interface for request handlers."""

    def match_request(self, req):
        """Return whether the handler wants to process the given request."""
        return False

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
        query = req.args.get('q', '').lower()
        tagsystem = TagSystem(self.env)
        alltags = tagsystem.query(req)
        tags = {}
        for resource, _tags in alltags:
            for tag in _tags:
                if query in tag.lower():
                    tags[tag] = tags.setdefault(tag, 0) + 1

        tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
        writeOut=str('\n'.join(['%s|%d' % (name, number) for name, number in tags]))
        req.send_header('Content-length', str(len(writeOut)))
        req.end_headers() 
        req.write(writeOut)

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
        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        if req.path_info.rstrip() == '/tags' and req.args.get('format') == 'txt':
            return self
        return handler

class AutocompleteTags(Component):
    
    implements(IRequestFilter, ITemplateProvider)

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
            add_stylesheet(req, 'tags/css/autocomplete.css')
            add_script(req, 'tags/js/autocomplete.js')
            add_script(req, 'tags/js/format_tags.js')
            add_script(req, 'tags/js/autocomplete_keywords.js')

        return (template, data, content_type)

    def pre_process_request(self, req, handler):
        """Called after initial handler selection, and can be used to change
        the selected handler or redirect request.
        
        Always returns the request handler, even if unchanged.
        """
        return handler

    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)
        
        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        return [('tags', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return a list of directories containing the provided template
        files.
        """
        return []                    
