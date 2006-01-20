# Tracpydoc plugin

from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, \
     add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, shorten_line
from trac.wiki.api import IWikiSyntaxProvider, IWikiMacroProvider
from trac.Search import ISearchSource
import inspect, os
from pydoc import ispackage

try:
    from trac.util import Markup
except ImportError:
    def Markup(markup): return markup


import urllib
import pydoc
import re
import time
import sys
import os
import imp
from fnmatch import fnmatch

try:
    import threading
except ImportError:
    import dummy_threading as threading


def any(gen):
    for p in gen:
        if p: return True
    return False


class TracDoc(pydoc.HTMLDoc):

    _cleanup_re = re.compile(r'(?:bg)?color="[^"]+"')
    _cleanup_heading_re = re.compile(r'href="([^"]+).html"')
    _cleanup_html_re = re.compile(r'\.html($|#)')
    _cleanup_inline_re = re.compile(r'<a href=".">index</a>(?:<br>)?|'
                                    r'<a href="file:.*?</a>(?:<br>)?')
    
    def __init__(self, env):
        self.env = env

    def index(self, dir, shadowed=None, includes=[], excludes=[]):
        """Generate an HTML index for a directory of modules."""
        modpkgs = []
        if shadowed is None: shadowed = {}
        seen = {}
        files = os.listdir(dir)

        def found(name, ispackage, modpkgs=modpkgs, shadowed=shadowed,
                  seen=seen):
            if name not in seen:
                modpkgs.append((name, '', ispackage, name in shadowed))
                seen[name] = 1
                shadowed[name] = 1

        matched = PyDoc(self.env).filter_match

        # Package spam/__init__.py takes precedence over module spam.py.
        for file in files:
            path = os.path.join(dir, file)
            if ispackage(path) and matched(path) or matched(file):
                found(file, 1)

        for file in files:
            path = os.path.join(dir, file)
            if os.path.isfile(path):
                modname = inspect.getmodulename(file)
                if modname and matched(modname):
                    found(modname, 0)

        modpkgs.sort()
        contents = self.multicolumn(modpkgs, self.modpkglink)
        if modpkgs:
            return self.bigsection(dir, '#ffffff', '#ee77aa', contents)
        else:
            return ''

    def modulelink(self, obj):
        return '<a href="%s">%s</a>' % \
               (self.env.href.pydoc(obj.__name__), obj.__name__)

    def modpkglink(self, (name, path, ispackage, shadowed)):
        fpath = '%s%s' % (path and path + '.' or '', name)
        return '<a href="%s">%s</a>' % (self.env.href.pydoc(fpath), name)

    def namelink(self, name, *dicts):
        for dict in dicts:
            if name in dict:
                return '<a href="%s">%s</a>' % \
                       (re.sub(self._cleanup_html_re, r'\1', dict[name]), name)
        return name

    def _link_components(self, path):
        if not path: return ''
        links = []
        sofar = []
        for mod in path.split('.'):
            sofar.append(mod)
            links.append('<a href="%s">%s</a>' % \
                         (self.env.href.pydoc('.'.join(sofar)), mod))
        return links

    def classlink(self, object, modname):
        module = object.__module__
        path = '%s.%s' % (module, object.__name__)
        return '.'.join(self._link_components(path))

    def heading(self, *args):
        return re.sub(self._cleanup_heading_re, r'href="\1"',
                      self._cleanup('heading', *args))
        
    def section(self, *args):
        return self._cleanup('section', *args)

    def grey(self, *args):
        return self._cleanup('grey', *args)

    def _cleanup(self, kind, *args):
        return re.sub(self._cleanup_inline_re, '', 
                      re.sub(self._cleanup_re, 'class="pydoc%s"'% kind,
                             getattr(pydoc.HTMLDoc, kind)(self, *args)))
    

class PyDoc(Component):
    """ Allow browsing of Python documentation through Trac. """

    implements(INavigationContributor, ITemplateProvider, IRequestHandler)

    def __init__(self):
        self.doc = TracDoc(self.env)
        syspath = self.config.get('pydoc', 'sys.path')
        if syspath:
            self.syspath = [os.path.normpath(p) for p in
                            syspath.split(os.pathsep)]
        else:
            self.syspath = sys.path

        self.includes, self.excludes = self.get_filters()

        show_private = self.config.get('pydoc', 'show_private', '')
        self.show_private = [p.rstrip('.*') for p in show_private.split()]
        self.makedoc_lock = threading.Lock()

    def filter_match(self, file):
        includes, excludes = self.get_filters()
        for match in excludes:
            if fnmatch(file, match):
                return 0
        for match in includes:
            if fnmatch(file, match):
                return 1
        return not includes


    def get_filters(self):
        return ([p for p in self.config.get('pydoc',
                         'include', '').split() if p],
                [p for p in self.config.get('pydoc',
                         'exclude', '').split() if p])

    def load_object(self, fullobject):
        """ Load an arbitrary object from a full dotted path. """
        fullspec = fullobject.split('.')
        i = 0
        module = mfile = mdescr = None
        mpath = self.syspath
        # Find module
        if fullspec[0] in sys.builtin_module_names:
            module = __import__(fullspec[0], None, None)
            i += 1
        else:
            while i < len(fullspec):
                try:
                    f, p, mdescr = imp.find_module(fullspec[i], mpath)
                    if mfile:
                        mfile.close()
                    mfile, mpath = f, [p]
                    i += 1
                except ImportError:
                    break
            try:
                mname = ".".join(fullspec[0:i])
                if sys.modules.has_key(mname):
                    module =  sys.modules[mname]
                elif mname and mdescr:
                    module = imp.load_module(mname, mfile, mpath[0], mdescr)
            finally:
                if mfile:
                    mfile.close()
        # Find object
        object = module
        while i < len(fullspec):
            try:
                object = getattr(object, fullspec[i])
                i += 1
            except AttributeError:
                raise ImportError, fullobject
        return (module, object)

    def generate_help(self, target, inline=False, visibility=''):
        """Show documentation for named `target`.

        If `inline` is set, no header will be generated.
        For the `visibility` argument, see `PyDocMacro`.
        """
        try:
            if not target or target == 'index':
                if inline:
                    doc = ''
                else:
                    doc = '<h1>Python: Index of Modules</h1>'
                for dir in self.syspath:
                    if os.path.isdir(dir):
                        doc += self.doc.index(dir, includes=self.includes,
                                              excludes=self.excludes)
                return doc
            else:
                if inline:
                    doc = ''
                else:
                    doc = '<h1>Python: Documentation for %s</h1>' % \
                          '.'.join(self.doc._link_components(target))
                return doc + self._makedoc(target, visibility)
        except ImportError:
            return "No Python documentation found for '%s'" % target

    def _makedoc(self, target, visibility):
        module, object = self.load_object(target)
        try:
            self.makedoc_lock.acquire()
            if visibility == 'private' or \
                   visibility == '' and any([module.__name__.startswith(p)
                                             for p in self.show_private]):
                try:
                    # save pydoc's original visibility function
                    visiblename = pydoc.visiblename
                    # define our own: show everything but imported symbols
                    is_imported_from_other_module = {}
                    for k, v in object.__dict__.iteritems():
                        if hasattr(v, '__module__') and \
                               v.__module__ != module.__name__:
                            is_imported_from_other_module[k] = True
                    def show_private(name, all=None):
                        return not is_imported_from_other_module.has_key(name)
                    # install our visibility function
                    pydoc.visiblename = show_private
                    return self.doc.document(object)
                finally:
                    # restore saved visibility function
                    pydoc.visiblename = visiblename
            else:
                return self.doc.document(object)
        finally:
            self.makedoc_lock.release()
    
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
        req.hdf['trac.href.pydoc'] = self.env.href.pydoc()
        req.hdf['pydoc.trail'] = [Markup(x) for x in 
                                  self.doc._link_components(target)[:-1]]
        req.hdf['pydoc.trail_last'] = target.split('.')[-1]
        req.hdf['pydoc.content'] = Markup(self.generate_help(target))
        req.hdf['title'] = target
        return 'pydoc.cs', None

    # ITemplateProvider methods
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('pydoc', resource_filename(__name__, 'htdocs'))]


class PyDocWiki(Component):
    """Provide wiki pydoc:object link syntax."""

    implements(IWikiSyntaxProvider)

    # IWikiSyntaxProvider methods

    def get_wiki_syntax(self):
        return []

    def get_link_resolvers(self):
        yield ('pydoc', self._pydoc_formatter)

    def _pydoc_formatter(self, formatter, ns, object, label):
        object = urllib.unquote(object)
        label = urllib.unquote(label)
        if not object or object == 'index':
            return '<a class="wiki" href="%s">%s</a>' % \
                   (formatter.href.pydoc(), label)
        else:
            try:
                _, target = PyDoc(self.env).load_object(object)
                doc = pydoc.getdoc(target)
                if doc: doc = doc.strip().splitlines()[0]
                return '<a class="wiki" title="%s" href="%s">%s</a>' % \
                       (shorten_line(doc), formatter.href.pydoc(object), label)
            except ImportError:
                return '<a class="missing wiki" href="%s">%s?</a>' % \
                       (formatter.href.pydoc(object), label)
            

class PyDocMacro(Component):
    """Show the Python documentation for the given `target`.

    An optional second argument (`visibility`) can be set in order
    to control the type of documentation that will be shown:
     * using "public", only show the documentation for exported symbols 
     * using "private", all the documentation will be shown

    If the `visibility` argument is omitted, the private documentation
    will be shown if the `target`'s module is listed in the
    `[pydoc] show_private` configuration setting.
    """

    implements(IWikiMacroProvider)

    # IWikiMacroProvider methods

    def get_macros(self):
        yield 'pydoc'

    def get_macro_description(self, name):
        return self.__doc__
    
    def render_macro(self, req, name, content):
        args = content.split(',')
        target = args and args.pop(0)
        visibility = args and args.pop(0).strip() or ''
        add_stylesheet(req, 'pydoc/css/pydoc.css')
        return PyDoc(self.env).generate_help(target, inline=True,
                                             visibility=visibility)


class PyDocSearch(Component):
    """ Provide searching of Python documentation. """

    implements(ISearchSource)

    # ISearchSource methods

    def get_search_filters(self, req):
        yield ('pydoc', 'Python Documentation', 0)

    def get_search_results(self, req, query, filters):
        query = [q.lower() for q in query.split()]
        results = []
        matched = PyDoc(self.env).filter_match
        if 'pydoc' in filters:
            def callback(path, modname, desc):
                for q in query:
                    if (path and not matched(path)) and (modname and not matched(modname)):
                        return
                    if q in modname.lower() or q in desc.lower():
                        results.append((self.env.href.pydoc(modname), modname,
                                        int(time.time()), 'pydoc', desc or ''))
                        return
            pydoc.ModuleScanner().run(callback)
        return results

