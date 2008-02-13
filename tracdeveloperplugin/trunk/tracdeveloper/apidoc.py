# -*- coding: utf-8 -*-

import inspect
import re

from trac.core import *
from trac.web import HTTPNotFound, IRequestHandler
from trac.web.chrome import Chrome
from trac.mimeview import Mimeview, Context

from tracdeveloper.util import linebreaks

__all__ = ['APIDocumentation']


class APIDocumentation(Component):
    implements(IRequestHandler)

    mimetype_map = {
        'tracwiki': 'text/x-trac-wiki',
        'restructuredtext': 'text/x-rst',
    }

    # IRequestHandler methods
    def match_request(self, req):
        match = re.match(r'/developer/doc(?:/(.*))?$', req.path_info)
        if match:
            req.args['name'] = match.group(1)
            return True

    def process_request(self, req):
        modname, attrname = str(req.args['name']).split(':')
        try:
            module = __import__(modname, {}, {}, filter(None, [attrname]))
            obj = getattr(module, attrname)
        except (ImportError, AttributeError), e:
            raise HTTPNotFound(e)

        formatter = self._get_formatter(module)

        data = {
            'module': modname,
            'name': attrname or modname,
            'doc': formatter(req, inspect.getdoc(obj)),
            'methods': self._get_methods(req, formatter, obj)
        }
        output = Chrome(self.env).render_template(req, 'developer/apidoc.html',
                                                  data, fragment=True)
        req.send(output.render('xhtml'), 'text/html')

    # Internal methods
    def _get_formatter(self, module):
        format = getattr(module, '__docformat__', 'default').split()[0]
        if format == 'default':
            return self._format_default

        mimetype = self.mimetype_map.get(format, 'text/plain')

        def mimeview_formatter(req, text):
            mimeview = Mimeview(self.env)
            context = Context.from_request(req)
            return mimeview.render(context, mimetype, text)
        return formatter

    def _format_default(self, req, text):
        return linebreaks(text)

    def _get_methods(self, req, formatter, cls, exclude_methods=None):
        methods = [getattr(cls, m) for m in dir(cls) if not m.startswith('_')
                   and m not in (exclude_methods or [])]
        return [{'name': m.__name__,
                 'args': inspect.formatargspec(*inspect.getargspec(m)),
                 'doc': formatter(req, inspect.getdoc(m))}
                for m in methods if inspect.ismethod(m)]
