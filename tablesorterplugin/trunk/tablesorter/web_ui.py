from pkg_resources import resource_filename

from trac.core import *
from trac.web import IRequestFilter
from trac.web.chrome import add_stylesheet, \
                            add_script, \
                            ITemplateProvider

class TableSorterModule(Component):
    """Adds tablesorter.js to any wiki table.
    
    See http://http://tablesorter.com/
    
    Tables must have the `tablesorter` class and contain a `thead` element."""

    implements(ITemplateProvider, IRequestFilter)

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        return [('tablesorter', resource_filename('tablesorter', 'htdocs'))]

    def get_templates_dirs(self):
        return []
        
    # IRequestFilter methods
    
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_stylesheet(req, 'tablesorter/style.css')
        add_script(req, 'tablesorter/jquery.tablesorter.min.js')
        return template, data, content_type