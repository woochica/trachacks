# -*- coding: utf-8 -*-

from fnmatch import fnmatch
import re

from trac.core import Component, implements
from trac.config import ListOption
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_stylesheet, add_script
from trac.web.href import Href
from trac.util.html import Markup


__all__ = ['WysiwygModule']


class WysiwygModule(Component):
    implements(ITemplateProvider, IRequestFilter)

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
    def post_process_request(self, req, template, content_type):
        if not _is_wysiwyg_enabled(template, self.templates):
            return template, content_type

        add_link(req, 'tracwysiwyg-base', req.href() or '/')
        stylesheets = ['chrome/common/css/trac.css', 'chrome/tracwysiwyg/editor.css']
        stylesheets += self.wysiwyg_stylesheets
        for stylesheet in stylesheets:
            add_link(req, 'tracwysiwyg-stylesheet', _expand_filename(req, stylesheet))
        add_stylesheet(req, 'tracwysiwyg/wysiwyg.css')
        add_script(req, 'tracwysiwyg/wysiwyg.js')
        footer = req.hdf['project.footer'] + '<script type="text/javascript">TracWysiwyg.initialize();</script>'
        req.hdf['project.footer'] = Markup(footer)
        return template, content_type


def _expand_filename(req, filename):
    if filename.startswith('chrome/common/') and 'htdocs_location' in req.hdf:
        href = Href(req.hdf['htdocs_location'])
        return href(filename[14:])
    if filename.startswith('/') or re.match(r'https?://', filename):
        href = Href(filename)
        return href()
    return req.href(filename)


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
