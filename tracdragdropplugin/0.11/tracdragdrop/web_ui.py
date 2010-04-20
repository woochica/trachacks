# -*- coding: utf-8 -*-

import cgi
import re
import shutil
from pkg_resources import resource_filename
from tempfile import TemporaryFile

from trac.attachment import AttachmentModule
from trac.core import Component, implements, TracError
from trac.mimeview.api import Context
from trac.perm import PermissionError
from trac.resource import get_resource_url
from trac.web.api import IRequestHandler, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_stylesheet, add_script
from trac.util.text import unicode_quote


__all__ = ['TracDragDropModule']


_HEADER = 'X-TracDragDrop'


class TracDragDropModule(Component):
    implements(ITemplateProvider, IRequestFilter, IRequestHandler)

    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracdragdrop', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return []

    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        if isinstance(data, dict):
            can_create = False

            if template == 'wiki_edit.html':
                page = data['page']
                if page.exists:
                    context = Context.from_request(req, page.resource)
                    attachments = AttachmentModule(self.env).attachment_data(context)
                    can_create = attachments['can_create']

            elif template == 'milestone_edit.html':
                milestone = data['milestone']
                if milestone.exists:
                    context = Context.from_request(req, milestone.resource)
                    attachments = AttachmentModule(self.env).attachment_data(context)
                    can_create = attachments['can_create']

            elif 'attachments' in data:
                can_create = data['attachments']['can_create']

            if can_create:
                name = None

                if template in ('wiki_view.html', 'wiki_edit.html'):
                    if 'page' in data:
                        realm = 'wiki'
                        name = data['page'].name
                elif template == 'ticket.html':
                    if 'ticket' in data:
                        realm = 'ticket'
                        name = data['ticket'].id
                elif template in ('milestone_view.html', 'milestone_edit.html'):
                    if 'milestone' in data:
                        realm = 'milestone'
                        name = data['milestone'].name

                if name is not None:
                    add_link(req, 'tracdragdrop.upload', req.href.tracdragdrop(realm, name))
                    add_stylesheet(req, 'tracdragdrop/tracdragdrop.css')
                    add_script(req, 'tracdragdrop/tracdragdrop.js')

        return template, data, content_type

    # IRequestHandler#match_request
    def match_request(self, req):
        match = re.match(r'/tracdragdrop/([^/]+)/(.*)\Z', req.path_info)
        if match:
            req.args['action'] = 'new'
            req.args['realm'] = match.group(1)
            req.args['path'] = match.group(2)
            req.args['attachment'] = PseudoAttachmentObject(req)
            return True

    # IRequestHandler#process_request
    def process_request(self, req):
        if req.get_header('X-Requested-With') != 'XMLHttpRequest':
            self._send_message_on_except(req, unicode(PermissionError()), 403)

        # XXX dirty hack
        req.redirect_listeners.insert(0, self._redirect_listener)
        attachment = AttachmentModule(self.env)
        try:
            attachment.process_request(req)
        except RedirectListened:
            req.send('', status=200)
        except TracError, e:
            self._send_message_on_except(req, unicode(e), 500)
        except PermissionError, e:
            self._send_message_on_except(req, unicode(e), 403)
        except Exception, e:
            self.log.error('AttachmentModule.process_request failed', exc_info=True)
            self._send_message_on_except(req, unicode(e), 500)

    def _send_message_on_except(self, req, message, status):
        req.send_header(_HEADER, unicode_quote(message))
        req.send(message, status=status)

    def _redirect_listener(self, req, url, permanent):
        raise RedirectListened


class PseudoAttachmentObject(object):
    def __init__(self, req):
        ctype = req.get_header('Content-Type')
        if ctype:
            ctype, options = cgi.parse_header(ctype)

        tempfile = TemporaryFile()
        shutil.copyfileobj(req.environ['wsgi.input'], tempfile)
        tempfile.flush()
        tempfile.seek(0)

        self.file = tempfile
        self.filename = options.get('filename')


class RedirectListened(Exception):
    pass


