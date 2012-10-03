# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Dmitry Dianov
# Copyright (C) 2011 Steffen Hoffmann
# Copyright (C) 2011-2012 Ryan J Ollos <ryan.j.ollos@gmail.com>
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.

import re

from genshi.builder import tag
from genshi.core import Markup
from genshi.filters.transform import Transformer
from trac import __version__ as trac_version
from trac.config import Option, BoolOption, ListOption
from trac.core import Component, implements
from trac.resource import Resource, ResourceSystem
from trac.util.text import unicode_quote_plus
from trac.web import IRequestFilter
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import (
    Chrome, ITemplateProvider, add_script, add_stylesheet
)

try:
    from trac.util.text import javascript_quote
except ImportError:
    # Fallback for Trac<0.11.3 - verbatim copy from Trac 1.0.
    _js_quote = {'\\': '\\\\', '"': '\\"', '\b': '\\b', '\f': '\\f',
                 '\n': '\\n', '\r': '\\r', '\t': '\\t', "'": "\\'"}
    for i in range(0x20) + [ord(c) for c in '&<>']:
        _js_quote.setdefault(chr(i), '\\u%04x' % i)
    _js_quote_re = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t\'&<>]')

    def javascript_quote(text):
        """Quote strings for inclusion in javascript"""
        if not text:
            return ''
        def replace(match):
            return _js_quote[match.group(0)]
        return _js_quote_re.sub(replace, text)

try:
    from tractags.api import TagSystem
    tagsplugin_is_installed = True
except ImportError:
    # TagsPlugin not available
    tagsplugin_is_installed = False


class KeywordSuggestModule(Component):
    implements (IRequestFilter, ITemplateProvider, ITemplateStreamFilter)

    field_opt = Option('keywordsuggest', 'field', 'keywords',
        """Field to which the drop-down list should be attached.""")

    keywords_opt = ListOption('keywordsuggest', 'keywords', '', ',',
        doc="A list of comma separated values available for input.")

# This needs to be reimplemented as part of the work on version 0.5, refs th:#8141
#    mustmatch = BoolOption('keywordsuggest', 'mustmatch', False,
#                           """If true, 'keywords' field accepts values from the keywords list only.""")

    matchcontains_opt = BoolOption('keywordsuggest','matchcontains_opt', True,
        "Include partial matches in suggestion list. Default is true.")

    multiple_separator_opt = Option('keywordsuggest','multipleseparator', ' ',
        """Character(s) to use as separators between keywords. Default is a
           single whitespace.""")

    helppage_opt = Option('keywordsuggest','helppage_opt', None,
        "If specified, 'keywords' label will be turned into a link to this URL.")

    helppagenewwindow_opt = BoolOption('keywordsuggest','helppage_opt.newwindow', False,
        """If true and helppage_opt specified, wiki page will open in a new window.
           Default is false.""")

    @property
    def multiple_separator(self):
        return self.multiple_separator_opt.strip('\'') or ' '


    # IRequestFilter methods
    def pre_process_request(self, req, handler):
        return handler
    
    def post_process_request(self, req, template, data, content_type):
        if req.path_info.startswith('/ticket/') or \
           req.path_info.startswith('/newticket') or \
           (tagsplugin_is_installed and req.path_info.startswith('/wiki/')):
                # In Trac 1.0 and later, jQuery-UI is included from the core.
                if trac_version >= '1.0':
                    Chrome(self.env).add_jquery_ui(req)
                else:
                    add_script(req, 'keywordsuggest/js/jquery-ui-1.8.16.custom.min.js')
                    add_stylesheet(req, 'keywordsuggest/css/jquery-ui-1.8.16.custom.css')

        return template, data, content_type


    # ITemplateStreamFilter methods
    def filter_stream(self, req, method, filename, stream, data):

        if not (filename == 'ticket.html' or
                (tagsplugin_is_installed and filename == 'wiki_edit.html')): 
            return stream
        
        keywords = self._get_keywords_string(req)
        if not keywords:
            self.log.debug("""
                No keywords found. KeywordSuggestPlugin is disabled.""")
            return stream

        matchfromstart = '"^" +'
        if self.matchcontains_opt:
            matchfromstart = ''

        js = """jQuery(document).ready(function($) {
                    var keywords = [ %(keywords)s ]
                    var sep = '%(multipleseparator)s'.trim() + ' '
                    function split( val ) {
                        return val.split( /%(multipleseparator)s\s*|\s+/ );
                    }
                    function extractLast( term ) {
                        return split( term ).pop();
                    }                    
                    $('%(field)s')
                        // don't navigate away from the field on tab when selecting an item
                        .bind( "keydown", function( event ) {
                            if ( event.keyCode === $.ui.keyCode.TAB && $( this ).data( "autocomplete" ).menu.active ) {
                                event.preventDefault();
                            }
                        })
                        .autocomplete({
                            delay: 0,
                            minLength: 0,
                            source: function( request, response ) {
                                // delegate back to autocomplete, but extract the last term
                                response( $.ui.autocomplete.filter(
                                    keywords, extractLast( request.term ) ) );
                            },
                            focus: function() {
                                // prevent value inserted on focus
                                return false;
                            },                            
                            select: function( event, ui ) {
                                var terms = split( this.value );
                                // remove the current input
                                terms.pop();
                                // add the selected item
                                terms.push( ui.item.value );
                                // add placeholder to get the comma-and-space at the end
                                terms.push( "" );
                                this.value = terms.join( sep );
                                return false;
                            }                            
                        });
                });"""

        # inject transient part of javascript directly into ticket.html template
        if req.path_info.startswith('/ticket/') or \
           req.path_info.startswith('/newticket'):
            js_ticket =  js % {'field': '#field-' + self.field_opt,
                               'multipleseparator': self.multiple_separator,
                               'keywords': keywords,
                               'matchfromstart': matchfromstart}
            stream = stream | Transformer('.//head').append\
                              (tag.script(Markup(js_ticket),
                               type='text/javascript'))

            # Turn keywords field label into link to an arbitrary resource.
            if self.helppage_opt:
                link = self._get_helppage_link(req)
                if self.helppagenewwindow_opt:
                    link = tag.a(href=link, target='blank')
                else:
                    link = tag.a(href=link)
                stream = stream | Transformer\
                     ('//label[@for="field-keywords"]/text()').wrap(link)

        # inject transient part of javascript directly into wiki.html template
        elif tagsplugin_is_installed and req.path_info.startswith('/wiki/'):
            js_wiki =  js % {'field': '#tags',
                             'multipleseparator': self.multiple_separator,
                             'keywords': keywords,
                             'matchfromstart': matchfromstart}
            stream = stream | Transformer('.//head').append \
                              (tag.script(Markup(js_wiki),
                               type='text/javascript'))
        return stream


    # Private methods
    def _get_keywords_string(self, req):
        # Using a set ensures no duplicates
        keywords = set(self.keywords_opt)
        if tagsplugin_is_installed:
            # '-invalid_keyword' is a workaround for a TagsPlugin regression,
            # see th:#7856 and th:#7857
            query_result = TagSystem(self.env).query(req, '-invalid_keyword')
            for resource, tags in query_result:
                keywords.update(tags)

        if keywords:
            keywords = sorted(keywords)
            keywords = ','.join(("'%s'" % javascript_quote(_keyword)
                                 for _keyword in keywords))
        else:
            keywords = ''
            
        return keywords

    def _get_helppage_link(self, req):
        link = realm = resource_id = None
        if self.helppage_opt.startswith('/'):
            # Assume valid URL to arbitrary resource inside
            #   of the current Trac environment.
            link = req.href(self.helppage_opt)
        if not link and ':' in self.helppage_opt:
            realm, resource_id = self.helppage_opt.split(':', 1)
            # Validate realm-like prefix against resource realm list,
            #   but exclude 'wiki' to allow deferred page creation.
            rsys = ResourceSystem(self.env)
            if realm in set(rsys.get_known_realms()) - set('wiki'):
                mgr = rsys.get_resource_manager(realm)
                # Handle optional IResourceManager method gracefully.
                try:
                    if mgr.resource_exists(Resource(realm, resource_id)):
                        link = mgr.get_resource_url(resource_id, req.href)
                except AttributeError:
                    # Assume generic resource URL build rule.
                    link = req.href(realm, resource_id)
        if not link:
            if not resource_id:
                # Assume wiki page name for backwards-compatibility.
                resource_id = self.helppage_opt
            # Preserve anchor without 'path_safe' arg (since Trac 0.12.2dev).
            if '#' in resource_id:
                path, anchor = resource_id.split('#', 1)
            else:
                anchor = None
                path = resource_id
            if hasattr(unicode_quote_plus, "safe"):
                # Use method for query string quoting (since Trac 0.13dev).
                anchor = unicode_quote_plus(anchor, safe="?!~*'()")
            else:
                anchor = unicode_quote_plus(anchor)
            link = '#'.join([req.href.wiki(path), anchor])
        return link

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('keywordsuggest', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'htdocs')]

