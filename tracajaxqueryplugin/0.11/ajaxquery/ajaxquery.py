from trac.core import implements, Component
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider
from trac.prefs.api import IPreferencePanelProvider

from genshi.builder import tag
from genshi.filters import Transformer

class AjaxQuery(Component):
    implements(ITemplateStreamFilter, ITemplateProvider)

    # ITemplateStreamFilter

    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'query.html':
            filter_script = Transformer('//script[contains(@src, "jquery.js")]')
            filter_query = Transformer('table[@class="listing tickets"]/.')
            return stream | filter_script.after(
                tag.script(
                    type="text/javascript",
                    src=self.env.href('chrome', 'aq', 'js', 'query.js'))) \
                    | filter_query.prepend('<!-- Hello -->')
        return stream

    # ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('aq', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]
