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
from trac.ticket.model import Ticket, Milestone
from trac.web.api import IRequestHandler, IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_stylesheet, add_script
from trac.wiki.model import WikiPage
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
                    add_link(req, 'tracdragdrop.view', req.href.tracdragdrop('view', realm, name))
                    add_link(req, 'tracdragdrop.new', req.href.tracdragdrop('new', realm, name))
                    add_stylesheet(req, 'tracdragdrop/tracdragdrop.css')
                    if req.locale is not None:
                        add_script(req, 'tracdragdrop/messages/%s.js' % req.locale)
                    add_script(req, 'tracdragdrop/tracdragdrop.js')

        return template, data, content_type

    # IRequestHandler#match_request
    def match_request(self, req):
        match = re.match(r'/tracdragdrop/([^/]+)/([^/]+)/(.*)\Z', req.path_info)
        if match:
            req.args['action'] = match.group(1)
            req.args['realm'] = match.group(2)
            req.args['path'] = match.group(3)
            if req.args['action'] == 'new':
                req.args['attachment'] = PseudoAttachmentObject(req)
            return True

    # IRequestHandler#process_request
    def process_request(self, req):
        if req.method != 'POST' or req.get_header('X-Requested-With') != 'XMLHttpRequest':
            self._send_message_on_except(req, unicode(PermissionError()), 403)

        action = req.args['action']
        if action == 'view':
            return self._render_attachments(req)

        if action == 'new':
            # XXX dirty hack
            req.redirect_listeners.insert(0, self._redirect_listener)
            attachment = AttachmentModule(self.env)
            try:
                attachment.process_request(req)
            except RedirectListened:
                req.send('', status=200)
            except TracError, e:
                self._send_message_on_except(req, e, 500)
            except PermissionError, e:
                self._send_message_on_except(req, e, 403)
            except Exception, e:
                self.log.error('AttachmentModule.process_request failed', exc_info=True)
                self._send_message_on_except(req, e, 500)
            req.send('', status=500)

    def _render_attachments(self, req):
        realm = req.args['realm']
        path = req.args['path']

        data = {}
        model = None
        if realm == 'wiki':
            data['compact'] = True
            model = WikiPage(self.env, path)
        elif realm == 'ticket':
            data['compact'] = False
            model = Ticket(self.env, path)
        elif realm == 'milestone':
            data['compact'] = True
            model = Milestone(self.env, path)

        if model is not None:
            context = Context.from_request(req, model.resource)
            attachments = AttachmentModule(self.env).attachment_data(context)
            attachments['can_create'] = False
            data['alist'] = attachments
            return 'list_of_attachments.html', data, None

    def _send_message_on_except(self, req, message, status):
        if not isinstance(message, basestring):
            message = str(message).decode('utf-8')
        req.send_header(_HEADER, unicode_quote(message))
        req.send(message.encode('utf-8'), status=status)

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


