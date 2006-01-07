# Tracpydoc plugin

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape
from trac.wiki import IWikiSyntaxProvider
import urllib
import pydoc
import re

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
    implements(INavigationContributor, ITemplateProvider, IRequestHandler, IWikiSyntaxProvider)

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
        target = req.path_info[7:]
        try:
            if not target or target == 'index':
                import sys, os
                doc = self.doc.heading('<big><big><strong>Python: Index of Modules</strong></big></big>', '#ffffff', '#7799ee')
                for dir in sys.path:
                    if os.path.isdir(dir):
                        doc += self.doc.index(dir)
                    req.hdf['pydoc'] = Markup(doc)
            else:
                req.hdf['pydoc'] = Markup(self.doc.document(self.load_object(target)))
        except ImportError:
            req.hdf['pydoc'] = "No Python documentation found for '%s'" % target
        return 'pydoc.cs', None

    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('pydoc', resource_filename(__name__, 'htdocs'))]

    # IWikiSyntaxProvider methods
    def get_wiki_syntax(self):
        """Return an iterable that provides additional wiki syntax.

        Additional wiki syntax correspond to a pair of (regexp, cb),
        the `regexp` for the additional syntax and the callback `cb`
        which will be called if there's a match.
        That function is of the form cb(formatter, ns, match).
        """
        return []

    def get_link_resolvers(self):
        """Return an iterable over (namespace, formatter) tuples.

        Each formatter should be a function of the form
        fmt(formatter, ns, target, label), and should
        return some HTML fragment.
        The `label` is already HTML escaped, whereas the `target` is not.
        """
        yield ('pydoc', self._pydoc_formatter)

    def _pydoc_formatter(self, formatter, ns, object, label):
        object = urllib.unquote(object)
        label = urllib.unquote(label)
        return '<a class="wiki" href="%s">%s</a>' % (formatter.href.pydoc(object), label)
