# -*- coding: utf-8 -*-

from fnmatch import fnmatch
import re

from genshi.builder import tag
from genshi.filters.transform import Transformer

from trac.core import Component, implements
from trac.config import ListOption, _TRUE_VALUES
from trac.ticket.web_ui import TicketModule
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_link, add_stylesheet, add_script
from trac.web.href import Href


__all__ = ['WysiwygModule']


class WysiwygModule(Component):
    implements(ITemplateProvider, IRequestFilter, ITemplateStreamFilter)

    wysiwyg_stylesheets = ListOption('tracwysiwyg', 'wysiwyg_stylesheets',
            doc="""Add stylesheets to the WYSIWYG editor""")

    templates = ListOption('tracwysiwyg', 'templates', doc="""\
            List of template names that the plugin will show a WYSIWYG editor
            on each TracWiki textarea. The plugin shows on all pages by
            default.""")

    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracwysiwyg', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return []

    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        if not _is_wysiwyg_enabled(template, self.templates):
            return template, data, content_type

        add_link(req, 'tracwysiwyg.base', req.href() or '/')
        stylesheets = ['chrome/common/css/trac.css', 'chrome/tracwysiwyg/editor.css']
        stylesheets += self.wysiwyg_stylesheets
        for stylesheet in stylesheets:
            add_link(req, 'tracwysiwyg.stylesheet', _expand_filename(req, stylesheet))
        add_stylesheet(req, 'tracwysiwyg/wysiwyg.css')
        add_script(req, 'tracwysiwyg/wysiwyg.js')
        add_script(req, 'tracwysiwyg/wysiwyg-load.js')

        return template, data, content_type

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        if not _is_wysiwyg_enabled(filename, self.templates):
            return stream

        options = {}
        if filename == 'ticket.html':
            options['escapeNewlines'] = _preserve_newlines(self.env)

        if options:
            text = 'var _tracwysiwyg = %s' % _to_json(options)
            stream |= Transformer('//head').append(tag.script(text, type='text/javascript'))

        return stream


def _preserve_newlines(env):
    ticket = TicketModule(env)
    # Trac 0.11.2 later
    if hasattr(ticket, 'must_preserve_newlines'):
        return ticket.must_preserve_newlines

    preserve_newlines = ticket.preserve_newlines
    if preserve_newlines == 'default':
        preserve_newlines = env.get_version(initial=True) >= 21 # 0.11
    return preserve_newlines in _TRUE_VALUES

def _expand_filename(req, filename):
    if filename.startswith('chrome/common/') and 'htdocs_location' in req.chrome:
        href = Href(req.chrome['htdocs_location'])
        return href(filename[14:])
    if filename.startswith('/') or re.match(r'https?://', filename):
        href = Href(filename)
        return href()
    return req.href(filename)


_escape_re = re.compile(r'[\010\f\n\r\t"><&\\]')

_escape_chars = {
    '\010': r'\b',
    '\f'  : r'\f',
    '\n'  : r'\n',
    '\r'  : r'\r',
    '\t'  : r'\t',
    '"'   : r'\"',
    '>'   : r'\u003E',
    '<'   : r'\u003C',
    '&'   : r'\u0026',
    '\\'  : r'\\',
}


def _escape_replace(match):
    return _escape_chars[match.group(0)]


def _to_json(value):
    if isinstance(value, basestring):
        return '"%s"' % _escape_re.sub(_escape_replace, value)
    if value is None:
        return 'null'
    if value is False:
        return 'false'
    if value is True:
        return 'true'
    if isinstance(value, (int, long)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return '[ %s ]' % ', '.join([_to_json(v) for v in value])
    if isinstance(value, dict):
        return '{ %s }' % ', '.join([
                '%s: %s' % (_to_json(k), _to_json(v))
                for k, v in value.iteritems()])
    raise TypeError, 'Unsupported type "%s"' % type(value)


def _is_wysiwyg_enabled(template, patterns):
    if not patterns:
        return True
    for pattern in patterns:
        positive = not pattern.startswith('!')
        if not positive:
            pattern = pattern[1:]
        if fnmatch(template, pattern):
            return positive
    return False
