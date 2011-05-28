# -*- coding: utf-8 -*-

import re

from trac.core import Component, implements
from trac.config import ListOption
from trac.ticket.web_ui import TicketModule
from trac.web.api import IRequestFilter
from trac.web.chrome import ITemplateProvider, add_link, add_stylesheet, add_script, add_script_data
from trac.web.href import Href


__all__ = ['WysiwygModule']


class WysiwygModule(Component):
    implements(ITemplateProvider, IRequestFilter)

    wysiwyg_stylesheets = ListOption('ckeditortrac', 'wysiwyg_stylesheets',
            doc="""Add stylesheets to the WYSIWYG editor""")

    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('ckeditortrac', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return []

    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        add_stylesheet(req, 'ckeditortrac/wysiwyg.css')
        add_script(req, 'ckeditortrac/ckeditortrac_load.js')
        add_script(req, 'ckeditortrac/ckeditor/ckeditor.js')
        add_script(req, 'tracwysiwyg/ckeditor/adapters/jquery.js')
        

        return (template, data, content_type)


def _expand_filename(req, filename):
    if filename.startswith('chrome/common/') and 'htdocs_location' in req.chrome:
        href = Href(req.chrome['htdocs_location'])
        return href(filename[14:])
    if filename.startswith('/') or re.match(r'https?://', filename):
        href = Href(filename)
        return href()
    return req.href(filename)


