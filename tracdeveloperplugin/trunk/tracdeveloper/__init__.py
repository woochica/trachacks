from trac.core import *
from trac.web.chrome import ITemplateProvider


class DeveloperTemplates(Component):
    implements(ITemplateProvider)

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('developer', resource_filename(__name__, 'htdocs'))]
