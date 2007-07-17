# ManualTestingPlugin

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup

class ManualTestingPlugin(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'testing'

    def get_navigation_items(self, req):
        yield 'mainnav', 'testing', Markup('<a href="%s">Testing</a>', self.env.href.testing() )

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/testing'

    def process_request(self, req):
        add_stylesheet(req, 'mt/css/manualtesting.css')
        return 'testing.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'htdocs/templates')]

    def get_htdocs_dirs(self):
        """Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.

        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('mt', resource_filename(__name__, 'htdocs'))]