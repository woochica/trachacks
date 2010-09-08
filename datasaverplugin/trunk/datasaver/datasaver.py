import re, sys

from genshi.builder import tag
from trac.core import Component, implements
from trac.web import IRequestFilter
from trac.web.chrome import \
    add_script, add_stylesheet, ITemplateProvider, INavigationContributor

class DataSaverModule(Component):
    implements(IRequestFilter, ITemplateProvider, INavigationContributor)

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'js/datasaver.js')
        add_stylesheet(req, 'css/datasaver.css')
        return (template, data, content_type)

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('js', resource_filename(__name__, 'js')),
                ('css', resource_filename(__name__, 'css'))]

    def get_active_navigation_item(self, req):
        return 'datasaver'

    def get_navigation_items(self, req):
        yield ('metanav', 'datasaver',
            tag.a('Restore Form', id='datasaver_restorer',
                    href='javascript:datasaver_restore()'))

