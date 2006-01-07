# Tracpydoc plugin

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape
from trac.wiki.api import IWikiSyntaxProvider, IWikiMacroProvider
import urllib
import pydoc
import re
import HTMLParser

try:
    from trac.util import Markup
except ImportError:
    def Markup(markup): return markup

class TracDoc(pydoc.HTMLDoc):

    _cleanup_re = re.compile(r'(?:bg)?color="[^"]+"')
    _cleanup_heading_re = re.compile(r'href="([^"]+).html"')
    _cleanup_html_re = re.compile(r'\.html($|#)')
    
    def __init__(self, env):
        self.env = env

    def modulelink(self, obj):
        return '<a href="%s">%s</a>' % (self.env.href.pydoc(obj.__name__), obj.__name__)

    def modpkglink(self, (name, path, ispackage, shadowed)):
        fpath = '%s%s' % (path and path + '.' or '', name)
        return '<a href="%s">%s</a>' % (self.env.href.pydoc(fpath), name)

    def namelink(self, name, *dicts):
        for dict in dicts:
            if name in dict:
                return '<a href="%s">%s</a>' % (re.sub(self._cleanup_html_re, r'\1', dict[name]), name)
        return name

    def classlink(self, object, modname):
        module = object.__module__
        path = '%s.%s' % (module, object.__name__)
        links = []
        sofar = []
        for mod in path.split('.'):
            sofar.append(mod)
            links.append('<a href="%s">%s</a>' % (self.env.href.pydoc('.'.join(sofar)), mod))
        return '.'.join(links)

    def heading(self, *args):
        return re.sub(self._cleanup_heading_re, r'href="\1"',
            self._cleanup('heading', *args))
        
    def section(self, *args):
        return self._cleanup('section', *args)

    def grey(self, *args):
        return self._cleanup('grey', *args)

    def _cleanup(self, kind, *args):
        return re.sub(self._cleanup_re, 'class="pydoc%s"'% kind,
                      getattr(pydoc.HTMLDoc, kind)(self, *args))
    

class TracPyDocPlugin(Component):
    """ Allow browsing of Python documentation through Trac. Also provides a
        pydoc:object link for linking to the browseable documentation and a
        [[pydoc(object)]] macro which expands documentation inline. """

    implements(INavigationContributor, ITemplateProvider, IRequestHandler,
        IWikiSyntaxProvider, IWikiMacroProvider)

    _fix_inline_re = re.compile(r'<a href=".">index</a><br>|<a href="file:.*?</a>')

    def __init__(self):
        self.doc = TracDoc(self.env)

    def load_object(self, fullobject):
        """ Load an arbitrary object from a full dotted path. """
        mod = fullobject.split('.')
        obj = []
        object = None
        # Find module
        while mod:
            try:
                object = __import__('.'.join(mod), None, None, [''])
                break
            except ImportError:
                pass
            obj.insert(0, mod.pop())
        if not object: object = __builtins__
        # Find object
        while obj:
            try:
                object = getattr(object, obj[0])
            except AttributeError:
                raise ImportError, fullobject
            mod.append(obj.pop(0))
        return object

    def generate_help(self, target):
        try:
            if not target or target == 'index':
                import sys, os
                doc = self.doc.heading('<big><big><strong>Python: Index of Modules</strong></big></big>', '#ffffff', '#7799ee')
                for dir in sys.path:
                    if os.path.isdir(dir):
                        doc += self.doc.index(dir)
                return doc
            else:
                return self.doc.document(self.load_object(target))
        except ImportError:
            return "No Python documentation found for '%s'" % target
    
    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'pydoc'
                
    def get_navigation_items(self, req):
        yield 'mainnav', 'pydoc', Markup('<a href="%s">PyDoc</a>' \
                                  % escape(self.env.href.pydoc()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info.startswith('/pydoc')

    def process_request(self, req):
        add_stylesheet(req, 'pydoc/css/pydoc.css')
        req.hdf['pydoc'] = Markup(self.generate_help(req.path_info[7:]))
        return 'pydoc.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('pydoc', resource_filename(__name__, 'htdocs'))]

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('pydoc', self._pydoc_formatter)

    def _pydoc_formatter(self, formatter, ns, object, label):
        object = urllib.unquote(object)
        label = urllib.unquote(label)
        return '<a class="wiki" href="%s">%s</a>' % (formatter.href.pydoc(object), label)

    # IWikiMacroProvider methods
    def get_macros(self):
        yield 'pydoc'

    def get_macro_description(self, name):
        return self.__doc__

    def render_macro(self, req, name, content):
        return re.sub(self._fix_inline_re, '', self.generate_help(content))
