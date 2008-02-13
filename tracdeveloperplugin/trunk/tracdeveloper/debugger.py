# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import re
from types import BuiltinFunctionType, FunctionType, GeneratorType, MethodType
from UserDict import DictMixin

from genshi import Markup
from genshi.builder import tag
from trac.core import *
from trac.util.text import shorten_line
from trac.web import HTTPBadRequest, HTTPNotFound, IRequestFilter, \
                     IRequestHandler
from trac.web.chrome import add_script, add_stylesheet, Chrome

__all__ = ['TemplateDebugger']
__docformat__ = 'tracwiki en'


class TemplateDebugger(Component):
    """Something ''wicked'' this way comes."""
    _cache = {}
    _cache_bytime = {}

    implements(IRequestFilter, IRequestHandler)

    # IRequestFilter methods

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if 'debug' not in req.args:
            return template, data, content_type

        # Purge outdated debug info from cache
        for time, key in [(time, key) for time, key
                          in self._cache_bytime.items()
                          if time < datetime.now() - timedelta(hours=1)]:
            del self._cache[key]
            del self._cache_bytime[time]

        local_keys = list(data.keys())
        data = Chrome(self.env).populate_data(req, data)

        token = str(id(req))
        new_data = {
            'context': None,
            'drillable': self._is_drillable(req),
            'token': token
        }
        ctxt = ObjectTree(data, 'context')
        for node in ctxt:
            if node.name in local_keys:
                node.highlight = True
        cache_key = token + ':context'
        self._cache[cache_key] = ctxt
        self._cache_bytime[datetime.now()] = cache_key
        new_data['context'] = ctxt

        del req.chrome # reset chrome info
        add_script(req, 'developer/js/apidoc.js')
        add_script(req, 'developer/js/debugger.js')
        add_stylesheet(req, 'common/css/code.css')
        add_stylesheet(req, 'developer/css/apidoc.css')
        add_stylesheet(req, 'developer/css/debugger.css')
        return 'developer/debug.html', new_data, 'text/html'

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/developer/debug(?:/(.*))?$', req.path_info)
        if match:
            req.args['path'] = match.group(1)
            return True

    def process_request(self, req):
        header = req.get_header('X-Requested-With')
        if not header or header.lower() != 'xmlhttprequest':
            # Not an XHR request from the debugger, so send a help page
            add_stylesheet(req, 'common/css/code.css')
            return 'developer/debug_help.html', {}, None

        path = req.args['path']
        token = req.args['token']
        assert path is not None and token is not None

        key = token + ':' + path.split(':', 1)[0]
        data = self._cache.get(key)
        if not data:
            raise HTTPNotFound()
        node = data.lookup(path)
        data = {'node': node, 'drillable': self._is_drillable(req)}
        output = Chrome(self.env).render_template(req, 'developer/debug_node.html',
                                                  data, fragment=True)
        req.send(output.render('xhtml'), 'text/html')

    # Internal methods

    def _is_drillable(self, req):
        if req.environ['wsgi.multiprocess'] or req.environ['wsgi.run_once']:
            return False
        return True


class ObjectTree(object):
    """Represents the root of a hierarchical object namespace."""

    def __init__(self, d, prefix):
        self.tree = {}
        self.idmap = {}
        self.toplevel = []
        for name, value in sorted(d.items()):
            path = '%s:%s' % (prefix, name)
            node = ObjectNode(self, name, value, path)
            self.tree[path] = node
            self.idmap[id(value)] = node
            self.toplevel.append(node)

    def __iter__(self):
        return iter(self.toplevel)

    def _add(self, name, value, path):
        child = ObjectNode(self, name, value, path)
        self.tree[path] = child
        self.idmap[id(value)] = child
        return child

    def expand(self, node):
        if node.is_collection:
            if isinstance(node.value, (dict, DictMixin)):
                for name, value in sorted(node.value.items()):
                    yield self._add("['%s']" % name, value,
                                    '%s.%s' % (node.path, name))
            elif isinstance(node.value, (list, tuple)):
                for idx, value in enumerate(node.value):
                    yield self._add('[%d]' % idx, value,
                                    '%s.%d' % (node.path, idx))
            elif isinstance(node.value, (set, frozenset)):
                for idx, value in enumerate(node.value):
                    yield self._add("", value, '%s.%d' % (node.path, idx))
        else:
            for name in dir(node.value):
                if name.startswith('_'):
                    continue
                try:
                    value = getattr(node.value, name)
                except Exception, e:
                    value = str(e)
                if type(value) in (FunctionType, GeneratorType, MethodType):
                    continue
                yield self._add(name, value, '%s.%s' % (node.path, name))

    def lookup(self, path):
        return self.tree[path]


class ObjectNode(object):
    """Represents a single named node in the object graph."""

    COLLECTION_TYPES = (dict, DictMixin, list, tuple, set, frozenset)
    SCALAR_TYPES = (bool, int, long, float, basestring)
    FUNCTION_TYPES = (BuiltinFunctionType, FunctionType, GeneratorType,
                      MethodType)

    def __init__(self, root, name, value, path):
        self.root = root
        self.name = name
        self.value = value
        self.path = path
        self.highlight = False

    def __iter__(self):
        return self.root.expand(self)

    def __repr__(self):
        return '<%s %r %r %r>' % (type(self).__name__, self.name, self.value,
                                  self.path)

    def full_name(self):
        return self.path[self.path.index('.') + 1:] + ' ' + self.short_type
    full_name = property(full_name)

    def is_expandable(self):
        try:
            if self.value is None or self.is_function:
                return False
            if isinstance(self.value, (bool, int, long, float)):
                return False
            if isinstance(self.value, basestring):
                return len(self.value) > 60
            if self.is_collection:
                return len(self.value) > 0
            return True
        except:
            return False
    is_expandable = property(is_expandable)

    def is_collection(self):
        return isinstance(self.value, self.COLLECTION_TYPES)
    is_collection = property(is_collection)

    def is_function(self):
        return type(self.value) in self.FUNCTION_TYPES
    is_function = property(is_function)

    def is_scalar(self):
        if self.value is None:
            return True
        return isinstance(self.value, self.SCALAR_TYPES)
    is_scalar = property(is_scalar)

    def is_string(self):
        return isinstance(self.value, basestring)
    is_string = property(is_string)

    def short_value(self):
        if self.is_scalar:
            if isinstance(self.value, basestring):
                value = self.value
                if not isinstance(self.value, unicode):
                    value = unicode(self.value, 'utf-8', 'replace')
                return tag.q(shorten_line(value, 60)).generate()
            else:
                return shorten_line(repr(self.value), 60)
        elif self.is_collection:
            if isinstance(self.value, (dict, DictMixin)):
                return u'{…}'
            elif isinstance(self.value, list):
                return u'[…]'
            elif isinstance(self.value, tuple):
                return u'(…)'
            elif isinstance(self.value, set):
                return u'set([…])'
            elif isinstance(self.value, frozenset):
                return u'frozenset([…])'
        else:
            try:
                return tag.code(shorten_line(str(self.value), 60))
            except:
                return '?'
    short_value = property(short_value)

    def short_type(self):
        if type(self.value).__name__ == 'instance':
            return '<%s>' % self.value.__class__.__name__
        elif self.value is not None:
            return '<%s>' % type(self.value).__name__
        return ''
    short_type = property(short_type)

    def long_type(self):
        obj = self.value
        if type(obj) not in (BuiltinFunctionType, FunctionType):
            obj = type(obj)
        return ':'.join([obj.__module__, obj.__name__])
    long_type = property(long_type)
