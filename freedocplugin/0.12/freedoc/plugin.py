# Freedoc plugin

import re

from genshi.builder import tag

from pkg_resources import resource_filename

from trac.core import *
from trac.web.chrome import ITemplateProvider, add_stylesheet
from trac.web import IRequestFilter

from trac.wiki.api import IWikiSyntaxProvider
from trac.wiki.formatter import format_to_oneliner

class TracFreeDoc(Component):
    implements(ITemplateProvider,IRequestFilter, IWikiSyntaxProvider)


    # ITemplateProvider methods


    def get_htdocs_dirs(self):
        return [('freedoc-htdocs', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []


    # IRequestFilter methods


    def pre_process_request(self, req, handler):
        return handler

    # Include the custom CSS by default on wiki pages
    def post_process_request(self, req, template, data, content_type):
        add_stylesheet(req, 'freedoc-htdocs/css/docbook.css')
        return (template, data, content_type)


    # IWikiSyntaxProvider methods


    def _cli_formatter(self, formatter, match, fullmatch):
        host = fullmatch.group('host')
        codeblock = fullmatch.group('codeblock')
        return tag.tt(host, class_='USERPROMPTHOST') +\
            tag.tt(codeblock, class_='USERPROMPT') + tag.br

    def _file_formatter(self, formatter, match, fullmatch):
        return tag.tt(fullmatch.group('filename'),class_='FILENAME')

    def _info_formatter(self, formatter, match, fullmatch):
        infotype = fullmatch.group('infotype').lower()
        body = format_to_oneliner(formatter.env, formatter.context,
                    fullmatch.group('notes'), False)
        return tag.div(tag.blockquote(tag.b(infotype.capitalize() + ': ')
            + body,class_=infotype.upper()),
            class_=infotype.upper())

    def _man_formatter(self, formatter, match, fullmatch):
        sektion =  fullmatch.group('sektion')
        item = fullmatch.group('item')
        url_target = 'http://www.FreeBSD.org/cgi/man.cgi?query=%s&sektion=%s' % (item, sektion)
        return tag.a(match,href=url_target)

    def _instruction_formatter(self,formatter,match,fullmatch):
        return tag(':') + tag.br

    def _boldstar_formatter(self,formatter,match,fullmatch):
        return tag.b(fullmatch.group('text'))

    def get_wiki_syntax(self):
        # Command prompt
        yield(r"(?P<cli>!?(?P<host>\S*?[\$\#] )(?P<codeblock>.*?)$)", self._cli_formatter )
        # File name
        yield(r"(?P<file>!?(file|dir):(?P<filename>\S*))", self._file_formatter )
        # Info box
        yield(r"(?P<info>!?(?P<infotype>[Tt]ip|[Nn]ote|[Ii]mportant|[Ww]arning):(?P<notes>.*?)$)", self._info_formatter)
        # Man page entry
        yield(r"(?P<man>!?(?P<item>\S*?)\((?P<sektion>[0-9])\))", self._man_formatter)
        # Always include cariage return after ':' at end of line
        yield(r"(?P<instruction>!?:$)", self._instruction_formatter)
        # Alternative bold, email style
        yield(r"(?P<boldstar>!?\*(?P<text>.*?)\*)", self._boldstar_formatter)

    def get_link_resolvers(self):
        return []
