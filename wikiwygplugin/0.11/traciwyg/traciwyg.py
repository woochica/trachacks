# vim: expandtab tabstop=4

# TraciWyg plugin

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_javascript
from trac.web.main import IRequestHandler
from trac.util import escape, Markup

class UserbaseModule(Component):
    implements(INavigationContributor, IRequestHandler,  ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'traciwyg'
                
    def get_navigation_items(self, req):
        add_stylesheet(req, 'twyg/wikiwyg.css')
        add_javascript(req, 'twyg/Wikiwyg.js')
        add_javascript(req, 'twyg/Toolbar.js')
        add_javascript(req, 'twyg/Wysiwyg.js')
        add_javascript(req, 'twyg/Wikitext.js')
        add_javascript(req, 'twyg/Preview.js')
        add_javascript(req, 'twyg/Trac.js')
        yield 'mainnav', 'prepare-wikiwyg', Markup('<a href="%s">prepare wikiwyg</a>', self.env.href.traciwyg())

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/traciwyg'
    
    def process_request(self, req):
        return 'wikiwyg.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('twyg', resource_filename(__name__, 'htdocs'))]
