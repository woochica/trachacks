# -*- coding: utf-8 -*-

import inspect
import re

from trac.core import *
from trac.web import IRequestHandler
from trac.web.chrome import Chrome

__all__ = ['APIDocumentation']


class APIDocumentation(Component):
    implements(IRequestHandler)

    # IRequestHandler methods

    def match_request(self, req):
        match = re.match(r'/developer/doc(?:/(.*))?$', req.path_info)
        if match:
            req.args['name'] = match.group(1)
            return True

    def process_request(self, req):
        header = req.get_header('X-Requested-With')
        is_xhr = header and header.lower() == 'xmlhttprequest'

        modname, attrname = req.args['name'].split(':')
        module = __import__(modname, {}, {}, filter(None, [attrname]))
        obj = getattr(module, attrname)
        docstring = inspect.getdoc(obj)

        data = {
            'module': modname,
            'name': attrname or modname,
            'doc': docstring,
            'methods': self._get_methods(obj)
        }
        output = Chrome(self.env).render_template(req, 'developer/apidoc.html',
                                                  data, fragment=True)
        req.send(output.render('xhtml'), 'text/html')

    # Internal methods

    def _get_methods(self, cls, exclude_methods=None):
        methods = [getattr(cls, m) for m in dir(cls) if not m.startswith('_')
                   and m not in (exclude_methods or [])]
        return [{'name': m.__name__,
                 'args': inspect.formatargspec(*inspect.getargspec(m)),
                 'doc': inspect.getdoc(m)}
                for m in methods if inspect.ismethod(m)]
