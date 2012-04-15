# copyright (c) 2008 Dmitry Dianov. All rights reserved.

from trac.core import Component, implements
from trac.web.api import ITemplateStreamFilter
from genshi.builder import tag
from genshi.core import Markup
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
        mustmatch = 'mustMatch: true,'
        if not self.config.getbool('keywordsuggest','mustmatch'):
            mustmatch = ""
        sep = self.config.get('keywordsuggest','multipleseparator', '')[1:-1] or ', '
        matchcontains = 'matchContains: true,'
        if not self.config.getbool('keywordsuggest','matchcontains',True):
            matchcontains = ""

        # inject transient part of javascript directly into ticket.html template
        js = """
        $(function($) {
          var sep = '%s'
          $('#field-keywords').autocomplete([%s], {multiple: true, %s
                                            %s multipleSeparator: sep, autoFill: true}); 
          $("form").submit(function() {
              // remove trail separator if any
              keywords = $("input#field-keywords").attr('value')
              if (keywords.lastIndexOf(sep) + sep.length == keywords.length) {
                  $("input#field-keywords").attr('value', keywords.substring(0, keywords.length-sep.length))
              }
          });
        });""" % (sep, keywords, matchcontains, mustmatch)
        stream = stream | Transformer('.//head').append \
                          (tag.script(Markup(js), type='text/javascript'))

        # turn keywords field label into link to wiki page
        helppage = self.config.get('keywordsuggest','helppage')
        if helppage:
            link = tag.a(href='wiki/%s' % helppage, target='blank')
            if not self.config.getbool('keywordsuggest','helppage.newwindow',
                                       'false'):
                link.attrib -= 'target'
            stream = stream | Transformer\
                         ('//label[@for="field-keywords"]/text()').wrap(link)
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
            add_script(req, 'keywordsuggest/jquery.bgiframe.min.js')
            add_script(req, 'keywordsuggest/jquery.autocomplete.pack.js')
            add_stylesheet(req, 'keywordsuggest/autocomplete.css')
        return template, data, content_type