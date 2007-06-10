import inspect
from trac.core import *
from trac.util.compat import set, sorted
from trac.core import ComponentManager
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet
from trac.wiki.formatter import wiki_to_html
from trac.admin.api import IAdminPanelProvider


def extract_section(cls):
    module = cls.__module__
    if module.startswith('trac.'):
        return module.split('.')[1]
    else:
        return module.split('.')[0] + '*'


class APIBrowser(Component):
    implements(IAdminPanelProvider, ITemplateProvider)

    # IAdminPanelProvider methods

    def get_admin_panels(self, req):
        if 'TRAC_ADMIN' not in req.perm: return
        yield ('developer', 'Trac Developer', 'api', 'API')

    def render_admin_panel(self, req, category, page, path_info):
        if 'TRAC_ADMIN' not in req.perm: return
        add_script(req, 'tracdeveloper/js/api.js')
        add_stylesheet(req, 'tracdeveloper/css/api.css')
        data = {'api': self.get_api(req)}
        return 'api.html', data

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracdeveloper', resource_filename(__name__, 'htdocs'))]


    # Internal methods
    def extract_methods(self, req, cls, exclude_methods=None):
        methods = [getattr(cls, m) for m in dir(cls) if not m.startswith('_')
                   and m not in (exclude_methods or [])]
        methods = [m for m in methods if inspect.ismethod(m)]
        methods = [{'name': m.__name__,
                    'args': inspect.formatargspec(*inspect.getargspec(m)),
                    'doc': inspect.getdoc(m),
                    'formatted_doc': wiki_to_html(inspect.getdoc(m), self.env, req)}
                   for m in methods]
        return methods

    def base_data(self, req, cls):
        data = {'name': '%s.%s' % (cls.__module__,
                                   cls.__name__),
                'doc': inspect.getdoc(cls),
                'formatted_doc': wiki_to_html(inspect.getdoc(cls), self.env, req)}
        return data

    def extension_points(self, req, cls):
        xp = [(m, getattr(cls, m)) for m in dir(cls) if not m.startswith('_')]
        xp = [{'name': name,
               'interface': self.base_data(req, m.interface)}
              for name, m in xp if isinstance(m, ExtensionPoint)]
        return xp

    def get_api(self, req):
        api = {}

        # Populate Interface API details
        interfaces = {}
        for interface in Interface.__subclasses__():
            data = self.base_data(req, interface)
            data['methods'] = self.extract_methods(req, interface)
            interfaces[data['name']] = data
        api['interfaces'] = interfaces

        components = {}
        for component in [c.__class__ for c in self.env.components.values()]:
            impl = [interfaces['%s.%s' % (i.__module__, i.__name__)]
                          for i in component._implements]
            interface_methods = [m['name'] for i in impl for m in i['methods']]
            methods = self.extract_methods(req, component, interface_methods)
            data = self.base_data(req, component)
            data['extensionpoints'] = self.extension_points(req, component)
            data['implements'] = impl
            data['methods'] = methods
            components[data['name']] = data
        api['components'] = components
        return api
