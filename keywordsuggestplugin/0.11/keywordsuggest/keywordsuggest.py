# copyright (c) 2008 Dmitry Dianov. All rights reserved.

from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer
from pkg_resources import resource_filename
from trac.config import Option, BoolOption, ListOption
from trac.core import Component, implements
from trac.util.text import javascript_quote
from trac.web import IRequestFilter
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_stylesheet, add_script

try:
    from tractags.api import TagSystem
    tagsplugin_is_installed = True
except ImportError:
    # TagsPlugin not available
    tagsplugin_is_installed = False

class KeywordSuggestModule(Component):
    implements (ITemplateStreamFilter, ITemplateProvider, IRequestFilter)

    field = Option('keywordsuggest', 'field', 'keywords',
                   """Field to which the drop-down list should be attached.""")

    keywords = ListOption('keywordsuggest', 'keywords', '', ',',
                          doc="""A list of comma separated values available for input.""")

# This needs to be reimplemented as part of the work on version 0.5, refs th:#8141
#    mustmatch = BoolOption('keywordsuggest', 'mustmatch', False,
#                           """If true, 'keywords' field accepts values from the keywords list only.""")

    matchcontains = BoolOption('keywordsuggest','matchcontains', True,
                               """Include partial matches in suggestion list. Default is true.""")

    multipleseparator = Option('keywordsuggest','multipleseparator', ",",
                               """Character(s) to use as separators between keywords.
                               Must be enclosed with quotes or other characters. Default is ', '.""")

    helppage = Option('keywordsuggest','helppage', None,
                      """If specified, 'keywords' label will be turned into a link to this URL.""")

    helppagenewwindow = BoolOption('keywordsuggest','helppage.newwindow', False,
                                   """If true and helppage specified, wiki page will open in a new window. Default is false.""")

    # ITemplateStreamFilter
    def filter_stream(self, req, method, filename, stream, data):
        if not (filename == 'ticket.html' or
                (tagsplugin_is_installed and filename == 'wiki_edit.html')): 
            return stream

        keywords = self.keywords
         
        if tagsplugin_is_installed:
            # '-invalid_keyword' is a workaround for a TagsPlugin regression, see th:#7856 and th:#7857
            query_result = TagSystem(self.env).query(req, '-invalid_keyword')
            for resource, tags in query_result:
                for _tag in tags:
                    if (_tag not in keywords):
                        keywords.append(_tag)
        
        if keywords:
            keywords = ','.join(("'%s'" % javascript_quote(_keyword)
                                 for _keyword in keywords))
        else:
            keywords = ''
        
        if not keywords:
            self.log.debug('No keywords found.'\
                           'KeywordSuggestPlugin disabled.')
            return stream

        multipleseparator = self.multipleseparator + ' '

        matchfromstart = '"^" +'
        if not self.matchcontains:
            matchfromstart = ''
            
        js = """jQuery(document).ready(function($) {
                    var sep = '%(multipleseparator)s'
                    $('%(field)s').autocomplete({
                        delay: 0,
                        minLength: 0, 
                        source: function(request, response) {
                            var re = $.ui.autocomplete.escapeRegex(request.term);
                            var matcher = new RegExp( %(matchfromstart)s re );
                            var a = $.grep( [%(keywords)s], function(item,index) {
                                return matcher.test(item);
                            });
                            response( a );
                        }
                    });
                    $("form").submit(function() {
                        // remove trail separator if any
                        keywords = $("input%(field)s").attr('value')
                        if (keywords.lastIndexOf(sep) + sep.length == keywords.length) {
                            $("input%(field)s").attr('value', keywords.substring(0, keywords.length-sep.length))
                        }
                    });
                });"""

        # inject transient part of javascript directly into ticket.html template
        if req.path_info.startswith('/ticket/') or \
           req.path_info.startswith('/newticket'):
            js_ticket =  js % {'field': '#field-' + self.field, 
                               'multipleseparator': multipleseparator,
                               'keywords': keywords,
                               'matchfromstart': matchfromstart}
            stream = stream | Transformer('.//head').append \
                              (tag.script(Markup(js_ticket), type='text/javascript'))
            print js_ticket

            # turn keywords field label into link to a wiki page
            if self.helppage:
                link = tag.a(href=req.href(self.helppage), target='blank')
                if not self.helppagenewwindow:
                    link.attrib -= 'target'
                stream = stream | Transformer\
                     ('//label[@for="field-keywords"]/text()').wrap(link)
                             
        # inject transient part of javascript directly into wiki.html template                             
        elif tagsplugin_is_installed and req.path_info.startswith('/wiki/'):
            js_wiki =  js % {'field': '#tags', 
                             'multipleseparator': multipleseparator,
                             'keywords': keywords,
                             'matchfromstart': matchfromstart}
            stream = stream | Transformer('.//head').append \
                              (tag.script(Markup(js_wiki), type='text/javascript'))
                              
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
           req.path_info.startswith('/newticket') or \
           (tagsplugin_is_installed and req.path_info.startswith('/wiki/')):
            add_script(req, 'keywordsuggest/js/jquery-ui-1.8.16.custom.min.js')
            add_stylesheet(req, 'keywordsuggest/css/ui-darkness/jquery-ui-1.8.16.custom.css')
        return template, data, content_type
