import inspect
import re

from trac.core import *
from trac.util.compat import set, sorted
from trac.web import IRequestHandler
from trac.web.chrome import add_script, add_stylesheet
from trac.wiki.formatter import wiki_to_html

__all__ = ['PluginRegistry']


class PluginRegistry(Component):
    implements(IRequestHandler)

    # IRequestHandler methods

    def match_request(self, req):
        return re.match(r'/developer/plugins?$', req.path_info)

    def process_request(self, req):
        interfaces = {}
        for interface in Interface.__subclasses__():
            data = self.base_data(req, interface)
            data['implemented_by'] = []
            interfaces[data['name']] = data

        components = {}
        for component in [c.__class__ for c in self.env.components.values()]:
            if hasattr(component, '_implements'):
                impl = [interfaces['%s.%s' % (i.__module__, i.__name__)]
                        for i in component._implements]
            else:
                impl = []
            data = self.base_data(req, component)
            data['extension_points'] = self.extension_points(req, component)
            data['implements'] = [i['name'] for i in impl]
            for imp in impl:
                imp['implemented_by'].append(data['name'])
            components[data['name']] = data

        add_script(req, 'developer/js/plugins.js')
        add_stylesheet(req, 'developer/css/plugins.css')
        return 'developer/plugins.html', {
            'components': components,
            'interfaces': interfaces
        }, None

    # Internal methods

    def base_data(self, req, cls):
        return {
            'name': '%s.%s' % (cls.__module__, cls.__name__),
            'doc': inspect.getdoc(cls)
        }

    def extension_points(self, req, cls):
        xp = [(m, getattr(cls, m)) for m in dir(cls) if not m.startswith('_')]
        return [{'name': name,
                 'interface': self.base_data(req, m.interface)}
                for name, m in xp if isinstance(m, ExtensionPoint)]
