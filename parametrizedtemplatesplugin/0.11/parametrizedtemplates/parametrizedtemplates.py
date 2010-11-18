# -*- coding: utf-8 -*-
# Author: Alvaro Iradier <alvaro.iradier@polartechnologies.es>

import re
from trac.core import *
from trac.web import IRequestHandler, IRequestFilter
from trac.web.chrome import add_stylesheet, ITemplateProvider, add_warning
from trac.wiki.formatter import format_to_html
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule
from pkg_resources import resource_filename

class ParametrizedTemplates(Component):
    """
    Allows creating new wiki pages from a template using a form to fill in
    some named parameters.
    
    New pages are created through /newpage/PageName?template=TemplateName
    """
    
    implements(ITemplateProvider)
    implements(IRequestHandler)
    implements(IRequestFilter)
    
    ##################################
    ## IRequestFilter

    def pre_process_request(self, req, handler):
        """Check if request of for new page creation from a template. If that's true,
        check if template has parameters, then redirect to our own page creation form."""
        if handler == WikiModule(self.env):
            template = req.args.get('template', '')
            page = req.args.get('page', 'WikiStart')
            action = req.args.get('action', '')
            
            if action == 'edit' and page and template:
                template_page =  WikiPage(self.env, WikiModule.PAGE_TEMPLATES_PREFIX + template)
                if len(self._find_fields(template_page.text)) > 0:
                    req.redirect(req.href.newpage(page.strip('/'), template=template))
        return handler

    def post_process_request(self, req, template, content_type):
        return (template, content_type)

    def post_process_request(req, template, data, content_type):
        return (template, data, content_type)

    ##################################
    
    ##################################
    ## ITemplateProvider

    def get_htdocs_dirs(self):
        """
        Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [resource_filename(__name__, 'templates')]

    ##################################

    ##################################
    ## IRequestHandler
    def match_request(self, req):
        match = re.match(r'/newpage(?:/(.+))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['page'] = match.group(1)
            return True

    def process_request(self, req):
        pagename = req.args.get('page', '')
        template = req.args.get('template', '')
        
        assert pagename, "Must specify a page name"

        if pagename.endswith('/'):
            req.redirect(req.href.newpage(pagename.strip('/')))

        page = WikiPage(self.env, pagename)
        template_page =  WikiPage(self.env, WikiModule.PAGE_TEMPLATES_PREFIX + template)
        
        fields = self._find_fields(template_page.text)
        
        #If page already exists, tell it
        if page.version != 0:
            add_warning(req, "Page %s already exists" % pagename)
            req.perm(page.resource).require('WIKI_MODIFY')
        else:
            req.perm.require('WIKI_CREATE')

        #Add wiki styles css
        add_stylesheet(req, 'common/css/wiki.css')

        data = {'template_page': template_page,
            'template': template,
            'page': page,
            'fields': fields}
        
        #Template has no fields?
        if len(fields) == 0:
            if page.version == 0 and template:
                req.redirect(req.href.wiki(page.name, action='edit', template=template))
            else:
                req.redirect(req.href.wiki(page.name))
        elif req.method == 'POST':
            page.text = self._replace_fields(fields, template_page.text, req)
            page.save(req.authname, 'New page from template %s' % template, req.remote_addr)
            req.redirect(req.href.wiki(page.name))
        else:
            return 'newpage.html', data, None
    ##################################

    def _find_fields(self, text):
        fields = []
        existing_fields = []
        for match in re.finditer(r'{{\s*(?P<name>.*?)\s*,\s*(?P<title>.*?)\s*(?:,\s*(?P<type>.*?)\s*(?:,\s*(?P<default>.*?)\s*)?)?}}', text):
            if match.group(1) not in existing_fields:
                existing_fields.append(match.group(1))
                fields.append((match.group('name'), 
                    match.group('title'), 
                    match.group('type') or 'text', 
                    match.group('default')))
        
        return fields
        
    def _replace_fields(self, fields, text, req):
        new_text = text
        for field in fields:
            if req.args.get('field_%s' % field[0], ''):
                new_text = re.sub(r'{{\s*(%s)\s*,\s*(.*?)\s*(?:,\s*(.*?)\s*)?}}' % field[0], 
                    req.args.get('field_%s' % field[0], ''), new_text)
        
        return new_text