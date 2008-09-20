# copyright (c) 2008 Dmitry Dianov. All rights reserved.

from trac.core import *
from trac.web.api import ITemplateStreamFilter
from genshi.builder import tag
from genshi.filters.transform import Transformer
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script
from pkg_resources import resource_filename
from trac.web import IRequestFilter

class KeywordSuggestModule(Component):
    implements (ITemplateStreamFilter, ITemplateProvider, IRequestFilter)

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        if (filename <> 'ticket.html'):
            return stream
       
        keywords = self.config.getlist('keywordsuggest','keywords')
        if not keywords:
            self.log.debug('List of keywords not found in trac.ini. '\
                           'Plugin keywordsuggest disabled.')
            return stream

        keywords = ','.join(("'%s'" % keyword for keyword in keywords))
        mustmatch = 'mustMatch: true,' \
            if self.config.getbool('keywordsuggest','mustmatch') else ""

		# inject transient part of javascript directly into ticket.html template
        js = """
        $(function($) {
        $('#field-keywords').autocomplete([%s], {multiple: true, 
                                          %s autoFill: true}); 
        });""" % (keywords, mustmatch)
        stream = stream | Transformer('.//head').append \
		                  (tag.script(js, type='text/javascript'))
        return stream

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return [('keywordsuggest', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return [resource_filename(__name__, 'htdocs')]

    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket/') or \
           req.path_info.startswith('/newticket'):
            add_script(req, 'keywordsuggest/jquery.autocomplete.pack.js')
            add_stylesheet(req, 'keywordsuggest/autocomplete.css')
        return template, data, content_type