import re, sys

from pkg_resources         import resource_filename

from genshi.builder        import tag
from trac.core             import Component, implements
from trac.util.translation import domain_functions
from trac.web              import IRequestFilter
from trac.web.chrome       import add_script, add_stylesheet, \
                                  ITemplateProvider, INavigationContributor


add_domain, _ = \
    domain_functions('datasaver', ('add_domain', '_'))

class DataSaverModule(Component):
    implements(IRequestFilter, ITemplateProvider, INavigationContributor)

    def __init__(self):
    # bind the 'datasaver' catalog to the specified locale directory
        locale_dir = resource_filename(__name__, 'locale')
        add_domain(self.env.path, locale_dir)

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'js/datasaver.js')
        if req.locale is not None: 
 	    add_script(req, 'htdocs/lang_js/%s.js' % req.locale)
        add_stylesheet(req, 'css/datasaver.css')
        return (template, data, content_type)

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        return [('js', resource_filename(__name__, 'js')),
                ('css', resource_filename(__name__, 'css'))]

    def get_active_navigation_item(self, req):
        return 'datasaver'

    def get_navigation_items(self, req):
        # TRANSLATOR: metanav button label
        yield ('metanav', 'datasaver',
            tag.a(_('Restore Form'), id='datasaver_restorer',
                    href='javascript:datasaver_restore()'))

