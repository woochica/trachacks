# -*- coding: utf-8 -*-

import cgi
import errno
import os
import re
from pkg_resources import resource_filename
from tempfile import TemporaryFile

from genshi.filters.transform import Transformer

from trac.attachment import AttachmentModule, Attachment
from trac.core import Component, implements, TracError
from trac.env import IEnvironmentSetupParticipant
from trac.perm import PermissionError
from trac.web.api import IRequestHandler, IRequestFilter, \
                         ITemplateStreamFilter, RequestDone
from trac.web.chrome import Chrome, ITemplateProvider, add_stylesheet, \
                            add_script
from trac.util.text import to_unicode, unicode_unquote

try:
    from trac.util.translation import domain_functions
    add_domain, _ = domain_functions('tracdragdrop', 'add_domain', '_')
except ImportError:
    add_domain = lambda env, dir: None
    _ = lambda val: val

try:
    from trac.web.chrome import web_context
except ImportError:
    from trac.mimeview.api import Context
    def web_context(*args, **kwargs):
        return Context.from_request(*args, **kwargs)

try:
    from trac.web.chrome import add_script_data
except ImportError:
    add_script_data = None
    _jsquote_re = re.compile(r'[\010\f\n\r\t"><&\\]')
    _jsquote_chars = {'\010': r'\b', '\f': r'\f', '\n': r'\n', '\r': r'\r',
                      '\t': r'\t', '"': r'\"', '\\': r'\\',
                      '&': r'\u0026', '>': r'\u003E', '<': r'\u003C'}
    def _jsquote_repl(match):
        return _jsquote_chars[match.group(0)]

    def to_json(value):
        """From 0.12-stable/trac/util/presentation.py"""
        if isinstance(value, basestring):
            return '"%s"' % _jsquote_re.sub(_jsquote_repl, value)
        elif value is None:
            return 'null'
        elif value is False:
            return 'false'
        elif value is True:
            return 'true'
        elif isinstance(value, (int, long)):
            return str(value)
        elif isinstance(value, float):
            return repr(value)
        elif isinstance(value, (list, tuple)):
            return '[%s]' % ','.join(to_json(each) for each in value)
        elif isinstance(value, dict):
            return '{%s}' % ','.join('%s:%s' % (to_json(k), to_json(v))
                                     for k, v in sorted(value.iteritems()))
        else:
            raise TypeError('Cannot encode type %s' % value.__class__.__name__)


__all__ = ['TracDragDropModule']


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
            data['attachments'] = attachments

        if template in ('wiki_edit.html', 'milestone_edit.html'):
            self._add_overlayview(req)
        add_stylesheet(req, 'tracdragdrop/tracdragdrop.css')
        if hasattr(req, 'locale'):
            locale = str(req.locale)
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
        if add_script_data:
            add_script_data(req, script_data)
        else:
            setattr(req, '_tracdragdrop_data', script_data)

        return template, data, content_type

    def filter_stream(self, req, method, filename, stream, data):
        if not add_script_data and method == 'xhtml' and filename and \
           data and hasattr(req, '_tracdragdrop_data'):
            def script():
                from genshi.builder import tag
                data = getattr(req, '_tracdragdrop_data')
                text = '\n'.join([
                    'var %s = %s;' % (name, to_json(val))
                    for name, val in data.iteritems()])
                return tag.script(text, type='text/javascript')
            stream |= Transformer('//head').append(script)

        if method == 'xhtml' and \
           filename in ('wiki_edit.html', 'milestone_edit.html') and \
           data.get('attachments', {}).get('can_create'):
            def render():
                d = {'alist': data['attachments'].copy()}
                d['compact'] = True
                d['foldable'] = True
                d['fragment'] = True
                return Chrome(self.env).render_template(
                    req, 'tracdragdrop.html', d, fragment=True)
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
        if req.method == 'POST':
            ctype = req.get_header('Content-Type')
            ctype, options = cgi.parse_header(ctype)
            if ctype not in ('application/x-www-form-urlencoded',
                             'multipart/form-data'):
                if not self._is_xhr(req):
                    req.send(unicode(PermissionError()).encode('utf-8'),
                             status=403)
                req.args['attachment'] = PseudoAttachmentObject(req)
                req.args['compact'] = req.get_header('X-TracDragDrop-Compact')

        action = req.args['action']
        if action in ('new', 'delete'):
            return self._delegate_request(req, action)

        req.send('', content_type='text/plain', status=500)

    def _delegate_request(self, req, action):
        # XXX dirty hack
        if hasattr(req, 'redirect_listeners'):
            req.redirect_listeners.insert(0, self._redirect_listener)
        else:
            def redirect(url, permanent=False):
                raise RedirectListened
            req.redirect = redirect
        try:
            if action == 'new':
                return self._delegate_new_request(req)
            if action == 'delete':
                return self._delegate_delete_request(req)
        except RequestDone:
            raise
        except TracError, e:
            return self._send_message_on_except(req, e, 500)
        except PermissionError, e:
            return self._send_message_on_except(req, e, 403)
        except Exception, e:
            self.log.error('AttachmentModule.process_request failed',
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
        db = self.env.get_db_cnx()
        attachments = Attachment.select(self.env, realm, req.args['path'],
                                        db=db)
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
        data['fragment'] = self._is_xhr(req)
        return 'tracdragdrop.html', data, None

    def _send_message_on_except(self, req, message, status):
        if not isinstance(message, unicode):
            message = to_unicode(message)
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
    def __init__(self, req):
        size = req.get_header('Content-Length')
        if size is None:
            size = -1
        else:
            size = int(size)

        tempfile = TemporaryFile()
        input = req.environ['wsgi.input']
        while True:
            buf = input.read(min(4096, size))
            if not buf:
                break
            tempfile.write(buf)
            size -= len(buf)
        tempfile.flush()
        tempfile.seek(0)

        self.file = tempfile
        filename = req.get_header('X-TracDragDrop-Filename')
        self.filename = unicode_unquote(filename or '').encode('utf-8')


class RedirectListened(Exception):
    pass
