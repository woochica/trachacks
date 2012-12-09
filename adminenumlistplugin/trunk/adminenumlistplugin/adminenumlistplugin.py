"""
AdminEnumListPlugin:
a plugin for Trac
http://trac.edgewall.org

(C) Stepan Riha, 2009
"""

from trac.core import Component, implements
from trac.web.api import IRequestFilter
from trac.web.chrome import Chrome, ITemplateProvider, add_script


class AdminEnumListPlugin(Component):

    implements(IRequestFilter, ITemplateProvider)
    
    
    ### methods for IRequestFilter
    
    def pre_process_request(self, req, handler):
        return handler

    _has_add_jquery_ui = hasattr(Chrome, 'add_jquery_ui')

    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/admin/'):
            add_script(req, 'adminenumlistplugin/adminenumlist.js')
            if not self._has_add_jquery_ui:
                add_script(req, 'adminenumlistplugin/jquery-ui-custom.js')
            else:
                Chrome(self.env).add_jquery_ui(req)

        return template, data, content_type

    ### methods for ITemplateProvider

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('adminenumlistplugin', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
