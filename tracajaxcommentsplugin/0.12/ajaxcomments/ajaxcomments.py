from trac.core import implements, Component
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider
from trac.prefs.api import IPreferencePanelProvider

from genshi.builder import tag
from genshi.filters import Transformer


class AjaxComments(Component):
    implements(ITemplateStreamFilter, ITemplateProvider, IPreferencePanelProvider)

    session_field = 'ajaxcomments_enabled'

    # ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'ticket.html':
            ticket = data.get('ticket')
            if ticket and ticket.exists and \
                   req.session.get(self.session_field, 'True') == 'True':
                filter_ = Transformer(
                    '//script[contains(@src, "jquery.js")]')
                return stream | filter_.after(
                    tag.script(
                        type="text/javascript",
                        src=self.env.href('chrome', 'ac', 'js', 'jquery.form.js'))) \
                        | filter_.after(
                    tag.script(
                        type="text/javascript",
                        src=self.env.href('chrome', 'ac', 'js', 'comments.js')))
        return stream

    # ITemplateProvider
    
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ac', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    # IPreferencePanelProvider
    def get_preference_panels(self, req):
        return [('ajaxcomments', 'AjaxComments preferences')]

    def render_preference_panel(self, req, panel):
        if (panel == 'ajaxcomments'):
            if req.method == 'POST':
                req.session[self.session_field] = 'False'
                if req.args.get('enabled'):
                    req.session[self.session_field] = 'True'
                req.redirect(req.href.prefs(panel))
            return 'preferences.html', {
                'enabled': req.session.get(self.session_field, 'True') == 'True'}
