# -*- coding: utf-8 -*-

from urllib import unquote_plus

from trac.core import Component, implements
from trac.web import IRequestHandler
from trac.web.api import HTTPBadRequest, HTTPUnauthorized

from api import TracFormDBUser
from compat import json
from iface import TracPasswordStoreUser
from tracforms import _


class TracFormUpdater(TracFormDBUser, TracPasswordStoreUser):
    implements(IRequestHandler)

    def match_request(self, req):
        return req.path_info.endswith('/formdata/update')

    def process_request(self, req):
        req.perm.require('FORM_EDIT_VAL')
        try:
            self.log.debug('UPDATE ARGS:' + str(req.args))
            args = dict(req.args)
            backpath = args.pop('__backpath__', None)
            context = json.loads(
                unquote_plus(args.pop('__context__', None)) or \
                '(None, None, None)')
            basever = args.pop('__basever__', None)
            keep_history = args.pop('__keep_history__', None)
            track_fields = args.pop('__track_fields__', None)
            args.pop('__FORM_TOKEN', None)  # Ignore.
            if context is None:
                # TRANSLATOR: HTTP error message
                raise HTTPBadRequest(_("__context__ is required"))
            who = req.authname
            result = json.dumps(args, separators=(',', ':'))
            self.save_tracform(context, result, who, basever,
                                keep_history=keep_history,
                                track_fields=track_fields)
            if backpath is not None:
                req.send_response(302)
                req.send_header('Content-Type', 'text/plain')
                req.send_header('Location', backpath)
                req.send_header('Content-Length', len('OK'))
                req.end_headers()
                req.write('OK')
            else:
                req.send_response(200)
                req.send_header('Content-Type', 'text/plain')
                req.send_header('Content-Length', len('OK'))
                req.end_headers()
                req.write('OK')
        except Exception, e:
            req.send_response(500)
            req.send_header('Content-type', 'text/plain')
            req.send_header('Content-Length', len(str(e)))
            req.end_headers()
            req.write(str(e))

