import re
from trac.core import *
from trac.web.chrome import add_script, \
    INavigationContributor, \
    ITemplateProvider


class TicketWebUiAddon(Component):
    implements(INavigationContributor, ITemplateProvider)
    
    def __init__(self):
        pass
    
    def get_navigation_items(self, req):
        if re.search('ticket', req.path_info):
            add_script(req, 'cc_selector/cc_selector.js')
        return []

    # ITemplateProvider
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        from pkg_resources import resource_filename
        return [('cc_selector', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return []
