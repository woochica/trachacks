# -*- coding: utf-8 -*-

import re

from trac.core import Component, implements, TracError
from trac.attachment import AttachmentModule
from trac.perm import PermissionError
from trac.resource import ResourceNotFound
from trac.util.text import exception_to_unicode
from trac.web.api import IRequestHandler, IRequestFilter, RequestDone, \
                         HTTPForbidden, HTTPNotFound, HTTPInternalError
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet, \
                            add_script_data


class OverlayViewModule(Component):

    implements(IRequestHandler, IRequestFilter, ITemplateProvider)

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('overlayview', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        if template in ('timeline.html', 'wiki_view.html', 'ticket.html',
                        'milestone_view.html', 'attachment.html'):
            add_stylesheet(req, 'common/css/code.css')
            add_stylesheet(req, 'overlayview/base.css')
            add_script(req, 'common/js/folding.js')
            add_script(req, 'overlayview/jquery.colorbox.js')
            add_script(req, 'overlayview/base.js')
            script_data = {}
            script_data['baseurl'] = req.href().rstrip('/') + '/'
            add_script_data(req, {'overlayview': script_data})
        return template, data, content_type

    _match_request_re = re.compile(r'/overlayview/([^/]+)/([^/]+)(?:/(.*))?\Z')

    def match_request(self, req):
        match = self._match_request_re.match(req.path_info)
        if match:
            cmd, realm, path = match.groups()
            req.args['cmd'] = cmd
            req.args['realm'] = realm
            if path:
                req.args['path'] = path
            return True

    def process_request(self, req):
        if req.get_header('X-Requested-With') != 'XMLHttpRequest':
            req.send('', status=204)

        cmd = req.args.get('cmd')
        try:
            if cmd == 'attachment':
                req.environ['PATH_INFO'] = req.path_info[len('/overlayview'):] \
                                           .encode('utf-8')
                template, data, content_type = \
                    AttachmentModule(self.env).process_request(req)
                return 'overlayview_attachment.html', data, content_type
        except RequestDone:
            raise
        except (PermissionError, HTTPForbidden), e:
            self._send_exception(req, e, 403)
        except (ResourceNotFound, HTTPNotFound), e:
            self._send_exception(req, e, 404)
        except (TracError, HTTPInternalError), e:
            self._send_exception(req, e, 500)

        req.send('', status=204)

    def _send_exception(self, req, e, status):
        message = exception_to_unicode(e)
        self.log.warn(message)
        req.send(message.encode('utf-8'), status=status)
