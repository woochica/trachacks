#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
#
# Copyright 2007-2008 Optaros, Inc
#

import re

from trac.core import *
from trac.config import BoolOption
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.web.chrome import add_script, ITemplateProvider
from trac.util.html import html
from trac.util.translation import _
from trac.wiki.formatter import wiki_to_html

from genshi import HTML
from genshi.filters.transform import Transformer

class WikiSectionEditModule(Component):
    implements(IRequestFilter, ITemplateStreamFilter, ITemplateProvider)
    
    preview_whole_page = BoolOption('section-edit', 'preview_whole_page', True, 
                                    'Whether to preview the entire page or just the section.')
    serve_ui_files = BoolOption('section-edit', 'serve_ui_files', True,
                                '???')

    # ITemplateProvider
    def get_templates_dirs(self):
        return []
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('tracsectionedit',resource_filename(__name__, 'htdocs'))]
    
    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        if re.match(r'^/($|wiki)', req.path_info) \
                and 'WIKI_MODIFY' in req.perm:
            if req.method=='POST' \
                    and 'section' in req.args \
                    and 'section_pre' in req.args \
                    and 'section_post' in req.args:
                section_text = req.args.get('text') 
                if len(section_text) > 0 and section_text[-1] != '\n':
                    section_text += '\n'
                if len(req.args['section_pre']) > 0 and req.args['section_pre'][-1] != '\n':
                    section_text = '\n' + section_text
                req.args['section_text'] = req.args.get('text')
                req.args['text'] = "%s%s%s"%(req.args.get('section_pre'), 
                                             section_text, 
                                             req.args.get('section_post'))
        return handler

    def post_process_request(self, req, template, data, content_type):
        if self.serve_ui_files \
                and not 'action' in req.args \
                and 'WIKI_MODIFY' in req.perm:
            add_script(req, 'tracsectionedit/js/tracsectionedit.js')
        return template, data, content_type

    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):
        if filename == 'wiki_edit.html' and 'section' in req.args and 'merge' not in req.args:
            if 'section_text' in req.args:
                section_pre, section_text, section_post = req.args.get('section_pre'), req.args.get('section_text'), req.args.get('section_post')
            else:
                section_pre, section_text, section_post = self._split_page_text(data['page'].text, req.args['section'])
                section_text = ''.join(section_text)
            
            section_element = html.input(type='hidden', name='section', id='section', value=req.args.get('section'))
            pre_element = html.input(type='hidden', name='section_pre', id='section_pre', value=''.join(section_pre))
            post_element = html.input(type='hidden', name='section_post', id='section_post', value=''.join(section_post))
            
            section_html = html(section_element, pre_element, post_element)
            stream = stream | Transformer('//textarea[@name="text"]').empty().append(section_text).before(section_html)
            stream = stream | Transformer('//div[@id="content"]//h1').append("/%s (section %s)"%(section_text[:section_text.find('\n')].strip(" = \r\n"), req.args['section']))
            if not self.preview_whole_page:
               stream = stream | Transformer('//div[@class="wikipage"]').empty().append(HTML(wiki_to_html(section_text, self.env, req)))
        return stream

    # internals
    def _split_page_text(self, page_text, section):
        """Split page_text used for paragraph_edit.
        Based on http://trac.edgewall.org/ticket/6921
        
        @param page_text: str
        @param section: int
        @return: tuple
        """
        count = 0
        pre = [] 
        target = [] 
        post = [] 
        is_code_block = False
        page_list = re.split('(\r\n|\r|\n)', page_text)

        for i, line in enumerate(page_list):
            if is_code_block == False and re.match(r'^\s*{{{\s*$', line):
                is_code_block = True
            elif is_code_block == True and re.match(r'^\s*}}}\s*$', line):
                is_code_block = False
            if is_code_block == False and re.match(r'^\s*([=#]{1,5}) .+ \1(?:\s*#.+)?\s*$', line):
                count = count + 1
            if count < int(section):
                pre.append(line)
            elif count == int(section):
                target.append(line)
            elif count > int(section) :
                break
        post = page_list[i:]
        if len(target) == 0:
            raise TracError(_('The section %(num)d that you chose could not be found.', num=int(section)), _('Initialize Error'))

        return pre, target, post
