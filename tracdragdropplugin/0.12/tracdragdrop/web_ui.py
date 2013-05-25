# -*- coding: utf-8 -*-

import cgi
import errno
import os
import re
import socket
from pkg_resources import resource_filename
from tempfile import TemporaryFile

from genshi.filters.transform import Transformer

from trac.attachment import AttachmentModule, Attachment
from trac.core import Component, implements, TracError
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionError
from trac.web.api import IRequestHandler, IRequestFilter, \
                         ITemplateStreamFilter, RequestDone, HTTPBadRequest
from trac.web.chrome import Chrome, ITemplateProvider, add_stylesheet, \
                            add_script, add_script_data
from trac.util.text import to_unicode, unicode_unquote
from trac.util.translation import domain_functions, dgettext

try:
    from trac.web.chrome import web_context
except ImportError:
    from trac.mimeview.api import Context
    def web_context(*args, **kwargs):
        return Context.from_request(*args, **kwargs)


__all__ = ['TracDragDropModule']

add_domain, _ = domain_functions('tracdragdrop', 'add_domain', '_')


def _list_message_files(dir):
    if not os.path.isdir(dir):
        return set()
    return set(file[0:-3] for file in os.listdir(dir) if file.endswith('.js'))


class TracDragDropModule(Component):
    implements(ITemplateProvider, IRequestFilter, IRequestHandler,
               ITemplateStreamFilter, IEnvironmentSetupParticipant)

    htdocs_dir = resource_filename(__name__, 'htdocs')
    templates_dir = resource_filename(__name__, 'templates')
    messages_files = _list_message_files(os.path.join(htdocs_dir, 'messages'))

    def __init__(self):
        try:
            dir = resource_filename(__name__, 'locale')
        except:
            dir = None
        if dir:
            add_domain(self.env.path, dir)

    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        return False

    def upgrade_environment(self, db):
        pass

    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        return [('tracdragdrop', self.htdocs_dir)]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return [self.templates_dir]

    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        if req.method != 'POST' and req.args.get('action') == 'new' and \
           handler is AttachmentModule(self.env):
            req.redirect(req.href(req.path_info).rstrip('/') + '/')
        return handler

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        if not req or not template or not isinstance(data, dict):
            return template, data, content_type

        model = None
        resource = None
        attachments = None

        if template in ('wiki_view.html', 'wiki_edit.html'):
            model = data.get('page')
        elif template == 'ticket.html':
            model = data.get('ticket')
        elif template in ('milestone_view.html', 'milestone_edit.html'):
            model = data.get('milestone')
        elif template == 'attachment.html':
            attachments = data.get('attachments')
            if attachments:
                resource = attachments['parent']

        if not resource and model and model.exists:
            resource = model.resource
        if not resource:
            return template, data, content_type
        if not attachments:
            attachments = data.get('attachments')
        if not attachments and model and resource:
            context = web_context(req, resource)
            attachments = AttachmentModule(self.env).attachment_data(context)
            # mark appending list of attachments in filter_stream
            attachments['tracdragdrop'] = True
            data['attachments'] = attachments

        if template in ('wiki_edit.html', 'milestone_edit.html'):
            self._add_overlayview(req)
        add_stylesheet(req, 'tracdragdrop/tracdragdrop.css')
        locale = req.locale and str(req.locale)
        if locale in self.messages_files:
            add_script(req, 'tracdragdrop/messages/%s.js' % locale)
        add_script(req, 'common/js/folding.js')
        add_script(req, 'tracdragdrop/tracdragdrop.js')
        script_data = {
            '_tracdragdrop': {
                'base_url': req.href().rstrip('/') + '/',
                'new_url': req.href('tracdragdrop', 'new', resource.realm,
                                    resource.id),
                'can_create': attachments.get('can_create') or False,
                'max_size': AttachmentModule(self.env).max_size,
            },
            'form_token': req.form_token,
        }
        add_script_data(req, script_data)

        return template, data, content_type

    def filter_stream(self, req, method, filename, stream, data):
        if method == 'xhtml' and \
           filename in ('wiki_edit.html', 'milestone_edit.html'):
            attachments = data.get('attachments')
            if attachments and attachments.get('can_create') and \
               'tracdragdrop' in attachments:
                del attachments['tracdragdrop']
                def render():
                    d = {'alist': attachments.copy()}
                    d['compact'] = True
                    d['foldable'] = True
                    return Chrome(self.env).render_template(
                        req, 'list_of_attachments.html', d, fragment=True)
                stream |= Transformer('//form[@id="edit"]').after(render)

        return stream

    # IRequestHandler#match_request
    def match_request(self, req):
        match = re.match(r'/tracdragdrop/([^/]+)/([^/]+)/(.*)\Z', req.path_info)
        if match:
            req.args['action'] = match.group(1)
            req.args['realm'] = match.group(2)
            req.args['path'] = match.group(3)
            return True

    # IRequestHandler#process_request
    def process_request(self, req):
        try:
            if req.method == 'POST':
                ctype = req.get_header('Content-Type')
                ctype, options = cgi.parse_header(ctype)
                if ctype not in ('application/x-www-form-urlencoded',
                                 'multipart/form-data'):
                    if not self._is_xhr(req):
                        raise PermissionError()
                    req.args['attachment'] = PseudoAttachmentObject(self.env,
                                                                    req)
                    req.args['compact'] = req.get_header(
                                                    'X-TracDragDrop-Compact')

                # XXX dirty hack
                req.redirect_listeners.insert(0, self._redirect_listener)
                action = req.args['action']
                if action == 'new':
                    return self._delegate_new_request(req)
                if action == 'delete':
                    return self._delegate_delete_request(req)

            raise TracError('Invalid request')

        except RequestDone:
            raise
        except TracError, e:
            return self._send_message_on_except(req, e, 500)
        except PermissionError, e:
            return self._send_message_on_except(req, e, 403)
        except Exception, e:
            self.log.error('Internal error in tracdragdrop',
                           exc_info=True)
            return self._send_message_on_except(req, e, 500)

    def _delegate_new_request(self, req):
        attachments = req.args.get('attachment')
        if not isinstance(attachments, list):
            attachments = [attachments]

        mod = AttachmentModule(self.env)
        for val in attachments:
            req.args['attachment'] = val
            try:
                mod.process_request(req)
            except OSError, e:
                if e.args[0] == errno.ENAMETOOLONG:
                    raise TracError(_("File name too long"))
                if os.name == 'nt' and e.args[0] == errno.ENOENT:
                    raise TracError(_("File name too long"))
                raise TracError(os.strerror(e.args[0]))
            except RedirectListened:
                pass
        return self._render_attachments(req)

    def _add_overlayview(self, req):
        try:
            from tracoverlayview.web_ui import OverlayViewModule
        except ImportError:
            return
        if self.env.is_component_enabled(OverlayViewModule):
            mod = OverlayViewModule(self.env)
            mod.post_process_request(req, 'attachment.html', {}, None)

    def _delegate_delete_request(self, req):
        try:
            AttachmentModule(self.env).process_request(req)
        except RedirectListened:
            req.send('Ok', status=200)

    def _render_attachments(self, req):
        realm = req.args['realm']
        path = req.args['path']
        db = self.env.get_read_db()
        attachments = [
            attachment for attachment
                       in Attachment.select(self.env, realm, path, db=db)]
        data = {}
        data['alist'] = {
            'can_create': False,
            'attachments': attachments,
        }
        if 'compact' in req.args:
            data['compact'] = req.args['compact'] != '0'
        else:
            data['compact'] = realm != 'ticket'
        data['foldable'] = True
        if self._is_xhr(req):
            template = 'list_of_attachments.html'
        else:
            template = 'tracdragdrop.html'
        return template, data, None

    def _send_message_on_except(self, req, message, status):
        if not isinstance(message, unicode):
            message = to_unicode(message)
        req.send_header('Connection', 'close')
        if self._is_xhr(req):
            req.send(message.encode('utf-8'), content_type='text/plain',
                     status=status)
        data = {'error': message}
        return 'tracdragdrop.html', data, None

    def _redirect_listener(self, req, url, permanent):
        raise RedirectListened()

    def _is_xhr(self, req):
        return req.get_header('X-Requested-With') == 'XMLHttpRequest'


class PseudoAttachmentObject(object):

    CHUNK_SIZE = 4096

    def __init__(self, env, req):
        max_size = AttachmentModule(env).max_size
        size = self.__get_content_length(req)
        self.__verify_size(size, max_size)
        tempfile = TemporaryFile()
        try:
            self.__read_content(req, tempfile, size, max_size)
        except:
            tempfile.close()
            raise
        self.file = tempfile
        filename = req.get_header('X-TracDragDrop-Filename')
        self.filename = unicode_unquote(filename or '').encode('utf-8')

    def __get_content_length(self, req):
        value = req.get_header('Content-Length')
        if value is None:
            return None
        if isinstance(value, unicode):
            value = value.encode('utf-8')

        size = None
        if value.isdigit():
            try:
                size = int(value)
            except:
                pass
        if size is None or size < 0:
            raise HTTPBadRequest('Invalid Content-Length: %r' % value)
        return size

    def __verify_size(self, size, max_size):
        if max_size >= 0 and size > max_size:
            message = dgettext('messages',
                               'Maximum attachment size: %(num)s bytes',
                               num=max_size)
            raise TracError(message, dgettext('messages', 'Upload failed'))

    def __read_content(self, req, out, size, max_size):
        input = req.environ['wsgi.input']
        readbytes = 0
        while True:
            if size is None:
                n = self.CHUNK_SIZE
            else:
                n = min(self.CHUNK_SIZE, size - readbytes)
            try:
                buf = input.read(n)
            except (IOError, socket.error), e:
                if e.args[0] in (errno.EPIPE, errno.ECONNRESET,
                                 10053,  # WSAECONNABORTED
                                 10054,  # WSAECONNRESET
                                 'request data read error',  # from mod_wsgi
                                ):
                    raise RequestDone
                raise
            if not buf:
                break
            out.write(buf)
            readbytes += len(buf)
            self.__verify_size(readbytes, max_size)
        out.flush()
        out.seek(0)


class RedirectListened(Exception):
    pass
