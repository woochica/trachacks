"""
 tracbib/formatter.py

 Copyright (C) 2011 Roman Fenkhuber

 Tracbib is a trac plugin hosted on trac-hacks.org. It brings support for
 citing from bibtex files in the Trac wiki from different sources.

 This file provides a basic wiki formatter for cited sources.

 tracbib is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.

 tracbib is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with tracbib.  If not, see <http://www.gnu.org/licenses/>.
"""

from api import IBibRefFormatter
from trac.core import implements, Component
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.web.api import IRequestFilter
from helper import replace_tags, remove_braces
from trac.util.text import unicode_unquote
from bibtexparse import capitalizetitle, authors
from pkg_resources import resource_filename
import re
try:
    from genshi.builder import tag
    from genshi.core import Markup
    version = ">0.10"
except ImportError:  # for trac 0.10:
    version = "0.10"
    from trac.util.html import html as tag
    from trac.util.html import Markup


BIBTEX_PERSON = [
    'author',
    'editor',
]

types = {
    'article': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '\"', 'post': ',\" '},
            'journal': {'pre': '', 'post': ', ',
                        'postsub': ['volume', 'number', 'pages']},
            'year': {'presub': ['month'], 'pre': '', 'post': '.'}
        },

        'optional': {
            'volume': {'pre': ', vol. ', 'post': ''},
            'number': {'pre': ', (', 'post': ')'},
            'pages': {'pre': ', pp. ', 'post': ''},
            'month': {'pre': '', 'post': ' '},
            'note': {'pre': '', 'post': ''},
            'key': {'pre': '', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
        },
        'order':
        ['author', 'title', 'journal', 'year',
         'doi', 'url'],
    },

    'book': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '', 'post': '. ',
                      'postsub': ['series', 'volume', 'editor', 'edition']},
            'publisher': {'pre': '', 'presub': ['address'], 'post': ', '},
            'year': {'pre': '', 'presub': ['month'], 'post': '.'}},

        'optional': {
            'editor': {'pre': ', ', 'post': ''},
            'volume': {'pre': ', vol. ', 'post': ''},
            'number': {'pre': ', no. ', 'post': ''},
            'series': {'pre': ' (', 'post': ')', 'postsub': ['number']},
            'address': {'pre': '', 'post': ': '},
            'edition': {'pre': ' ', 'post': ' ed'},
            'month': {'pre': '', 'post': ' '},
            'note': {'pre': '', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},

            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'publisher', 'year',
         'doi', 'url'],
    },

    'booklet': {
        'required': {
            'title': {'pre': '', 'post': '. '}},

        'optional': {
            'author': {'pre': '', 'post': ', '},
            'howpublished': {'pre': '', 'post': ', '},
            'address': {'pre': '', 'post': ': '},
            'month': {'pre': '', 'post': ' '},
            'year': {'pre': '', 'presub': ['month'], 'post': '.'},
            'note': {'pre': '', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'address',
         'howpublished', 'year', 'doi', 'url'],
    },

    'inproceedings': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '\"', 'post': ',\" '},
            'booktitle': {'pre': 'in ', 'post': '. ',
                          'postsub': ['series', 'volume', 'editor']},
            'year': {'pre': '', 'presub': ['month'],
                     'postsub': ['pages'], 'post': '.'}},

        'optional': {
            'editor': {'pre': ', ', 'post': ''},
            'volume': {'pre': ', vol. ', 'post': ''},
            'number': {'pre': ', no. ', 'post': ''},
            'series': {'pre': ' (', 'post': ')', 'postsub': ['number']},
            'pages': {'pre': ', pp. ', 'post': ''},
            'address': {'pre': ', ', 'post': ': '},
            'month': {'pre': '', 'post': ' '},
            'organization': {'pre': '', 'post': ''},
            'publisher': {'pre': '', 'post': ', '},
            'note': {'pre': '', 'post': ''},
            'key': {'pre': '', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'}},
        'order':
        ['author', 'title', 'booktitle', 'address',
         'publisher', 'year', 'doi', 'url'],

    },

    'conference': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '\"', 'post': ',\" '},
            'booktitle': {'pre': 'in ', 'post': '. ',
                          'postsub': ['series', 'volume', 'editor']},
            'year': {'pre': '', 'presub': ['month'],
                     'postsub': ['pages'], 'post': '.'}},

        'optional': {
            'editor': {'pre': ', ', 'post': ''},
            'volume': {'pre': ', vol. ', 'post': ''},
            'number': {'pre': ', no. ', 'post': ''},
            'series': {'pre': ' (', 'post': ')',
                       'postsub': ['number']},
            'pages': {'pre': ', pp. ', 'post': ''},
            'address': {'pre': '', 'post': ': '},
            'month': {'pre': '', 'post': ' '},
            'organization': {'pre': '', 'post': ''},
            'publisher': {'pre': '', 'post': ', '},
            'note': {'pre': '', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'booktitle', 'address',
         'publisher', 'year', 'doi', 'url'],
    },

    'inbook': {
        'required': {
            'author': {'pre': '', 'post': ','},
            'editor': {'pre': ', ', 'post': ''},
            'title': {'pre': ' in ', 'post': '. ',
                      'postsub': ['series', 'volume', 'editor', 'edition']},
            'chapter': {'pre': ' \"', 'post': ',"'},
            'pages': {'pre': ', pp. ', 'post': ''},
            'publisher': {'pre': '', 'post': ', '},
            'year': {'pre': '',
                     'presub': ['month'],
                     'postsub': ['pages'], 'post': '.'}},

        'optional': {
            'volume': {'pre': ', vol. ', 'post': ''},
            'number': {'pre': ', no. ', 'post': ''},
            'series': {'pre': ' (', 'post': ')',
                       'postsub': ['number']},
            'type': {'pre': '', 'post': ''},
            'address': {'pre': '', 'post': ': '},
            'edition': {'pre': '', 'post': ' ed'},
            'month': {'pre': '', 'post': ' '},
            'note': {'pre': '', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'chapter', 'title', 'address',
         'publisher', 'year', 'doi', 'url'],

    },

    'incollection': {
        'required': {
            'author': {'pre': '', 'post': ''},
            'booktitle': {'pre': 'in ', 'post': '. ',
                          'postsub':
                          ['series', 'volume', 'editor', 'edition']},
            'title': {'pre': '\"', 'post': ',\" '},
            'publisher': {'pre': '', 'post': ', '},
            'year': {'pre': '', 'presub': ['month'],
                     'postsub': ['chapter', 'pages'], 'post': '.'}},

        'optional': {
            'editor': {'pre': ', ', 'post': ''},
            'volume': {'pre': ', vol. ', 'post': ''},
            'number': {'pre': '', 'post': ''},
            'series': {'pre': ' (', 'post': ')',
                       'postsub': ['number']},
            'type': {'pre': '', 'post': ''},
            'chapter': {'pre': ', ch. ', 'post': ''},
            'pages': {'pre': ', pp. ', 'post': ''},
            'address': {'pre': '', 'post': ': '},
            'edition': {'pre': ', ', 'post': ' ed'},
            'month': {'pre': '', 'post': ''},
            'note': {'pre': '', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'booktitle', 'address',
         'publisher', 'year', 'doi', 'url'],
    },

    'proceedings': {
        'required': {
            'title': {'pre': '', 'post': '. ',
                      'postsub': ['series', 'volume', 'editor', 'edition']},
            'year': {'pre': '', 'presub': ['month'], 'post': '.'}},

        'optional': {
            'publisher': {'pre': '', 'presub': ['address'], 'post': ', '},
            'editor': {'pre': ', ', 'post': ''},
            'volume': {'pre': ', vol. ', 'post': ''},
            'number': {'pre': ', no. ', 'post': ''},
            'series': {'pre': ' (', 'post': ')', 'postsub': ['number']},
            'address': {'pre': '', 'post': ': '},
            'edition': {'pre': ' ', 'post': ' ed'},
            'month': {'pre': '', 'post': ' '},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'note': {'pre': '', 'post': ''},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['title', 'publisher', 'year', 'doi', 'url'],
    },

    'manual': {
        'required': {
            'title': {'pre': '', 'post': ', ',
                      'postsub': ['edition']}},

            'optional': {
                'author': {'pre': '', 'post': ', '},
                'organization': {'pre': '', 'post': ', '},
                'address': {'pre': '', 'post': ', '},
                'edition': {'pre': '', 'post': ' ed.'},
                'month': {'pre': '', 'post': ' '},
                'year': {'pre': '', 'post': '.', 'presub': ['month'],
                         'postsub': ['pages']},
                'pages': {'pre': ', pp. ', 'post': ''},
                'doi': {'pre': ' DOI: ', 'post': '.'},
                'url': {'pre': ' Available: ', 'post': '.'},
                'note': {'pre': '', 'post': ''},
                'key': {'pre': '', 'post': ''}},
        'order':
            ['author', 'title', 'organization',
                'address', 'year', 'doi', 'url'],

    },

    'mastersthesis': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '\"', 'post': ',\" M.S. thesis, '},
            'school': {'pre': '', 'post': ', '},
            'year': {'pre': '', 'post': '.', 'presub': ['month']}},

        'optional': {
            'type': {'pre': '', 'post': ''},
            'address': {'pre': '', 'post': ', '},
            'month': {'pre': '', 'post': ' '},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'note': {'pre': '', 'post': ''},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'school', 'address',
         'year', 'doi', 'url'],

    },

    'misc': {
        'required': {},

        'optional': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '', 'post': ', '},
            'howpublished': {'pre': '', 'post': ', '},
            'month': {'pre': '', 'post': ' '},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'year': {'pre': '', 'presub': ['month'], 'post': '.'},
            'note': {'pre': '', 'post': ''},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'howpublished', 'year',
         'doi', 'url'],
    },

    'phdthesis': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '\"', 'post': ',\" Ph.D. dissertation, '},
            'school': {'pre': '', 'post': ', '},
            'year': {'pre': '', 'post': '.', 'presub': ['month']}},

        'optional': {
            'type': {'pre': '', 'post': ''},
            'address': {'pre': '', 'post': ', '},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'month': {'pre': '', 'post': ' '},
            'note': {'pre': '', 'post': ''},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'school', 'address',
         'year', 'doi', 'url'],
    },

    'techreport': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '\"', 'post': ',\" '},
            'institution': {'pre': '', 'post': ''},
            'year': {'pre': '', 'post': '.', 'presub': ['month']}},

        'optional': {
            'type': {'pre': '', 'post': ''},
            'number': {'pre': 'Rep. ', 'post': ''},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'address': {'pre': '', 'post': ': '},
            'month': {'pre': '', 'post': ' '},
            'note': {'pre': '', 'post': ''},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'institution',
         'address', 'year', 'doi', 'url'],

    },

    'unpublished': {
        'required': {
            'author': {'pre': '', 'post': ', '},
            'title': {'pre': '', 'post': '. '},
            'note': {'pre': '', 'post': ''}},

        'optional': {
            'month': {'pre': '', 'post': ' '},
            'doi': {'pre': ' DOI: ', 'post': '.'},
            'url': {'pre': ' Available: ', 'post': '.'},
            'year': {'pre': '', 'post': ', ', 'presub': ['month']},
            'key': {'pre': '', 'post': ''}},
        'order':
        ['author', 'title', 'year', 'note', 'doi',
         'url'],
    },
}


class BibRefFormatterIEEELike(Component):
    """An IEEE-like citation style"""
    implements(IBibRefFormatter)
    implements(IRequestFilter, ITemplateProvider)

    __stack = []

    def formatter_type(self):
        return "ieeelike"

    def __format_value(self, bibkey, value, style):
        required = style['required']
        optional = style['optional']
        if bibkey in value:
            if bibkey in required:
                pre = required[bibkey]['pre']
                post = required[bibkey]['post']
                entry = required[bibkey]
            else:
                pre = optional[bibkey]['pre']
                post = optional[bibkey]['post']
                entry = optional[bibkey]

            span = tag.span(class_=bibkey)
            self.__stack.append(pre)
            if 'presub' in entry:
                for sub in entry['presub']:
                    self.__stack.append(self.__format_value(sub, value, style))

            if bibkey in BIBTEX_PERSON:
                a = authors(value[bibkey])
                for person in a:
                    if 'first' in person:
                        formatted = ""
                        for first in person['first'].split(' '):
                            first = remove_braces(replace_tags(first))
                            if len(first) > 0:
                                formatted = formatted + first[0] + "."
                        partspan = tag.span(class_='first')
                        partspan.append(formatted)
                        span.append(partspan)
                        span.append(" ")

                    for part in ['von', 'last']:
                        if part in person:
                            partspan = tag.span(class_=part)
                            partspan.append(
                                remove_braces(replace_tags(person[part])))
                            span.append(partspan)
                            if part != 'last':
                                span.append(" ")
                    if person != a[-1] and len(a) < 3:
                        span.append(" and ")
                    else:
                        if len(a) >= 3:
                            etal = tag.span(class_='etal')
                            etal.append(" et al.")
                            span.append(etal)
                        if bibkey == 'editor':
                            if len(a) > 1 and person == a[-1]:
                                span.append(", Eds.")
                            else:
                                span.append(", Ed.")
                        break

            elif bibkey == 'url':
                url = value['url']
                span.append(tag.a(href=url)(unicode_unquote(url)))
            elif bibkey == 'doi':
                url = 'http://dx.doi.org/' + value['doi'].strip()
                span.append(tag.a(href=url)(value['doi']))
            else:
                if bibkey == 'pages':
                    value[bibkey] = re.sub('---', '--', value[bibkey])
                    value[bibkey] = re.sub(
                        r'([^-])-([^-])', r'\1--\2', value[bibkey])
                span.append(
                    Markup(capitalizetitle(replace_tags(value[bibkey]))))
            self.__stack.append(span)
            if 'postsub' in entry:
                for sub in entry['postsub']:
                    self.__format_value(sub, value, style)
            self.__stack.append(post)

    def format_entry(self, key, value):
        self.__stack = []
        content = tag()
        content.append(tag.a(name='ref_%s' % key))
        style = types['misc']

        if value['type'] in types:
            style = types[value['type']]
        keys = style['order']

        for bibkey in keys:
            self.__format_value(bibkey, value, style)
        #return tag.li(tag.a(name='ref_%s' % key),
        #    tag.a(href='#cite_%s' % key)('^') ,content)
        content.append(self.__stack)
        return content

    def format_ref(self, entries, label):
        return self.format_fullref(entries, label)

    def format_fullref(self, entries, label):
        cited = []
        notcited = []
        #first let's render cited articles
        for key, value in entries.iteritems():
            if ':index' in value:
                cited.append((key, value))
            else:
                notcited.append((key, value))

        cited.sort(key=lambda entry: entry[1][':index'])
        #notcited.sort(key = lambda entry:entry[1]['author'])

        for key, value in notcited:
            cited.append((key, value))

        return self.format(cited, label)

    def format_cite(self, key, value, page):
        if not page:
            return ''.join(['[', str(tag.a(name='cite_%s' % key)),
                            str(tag.a(href='#ref_%s' %
                                key)('%d' % value[":index"])),
                            ']'])
        else:
            return ''.join(['[', str(tag.a(name='cite_%s' % key)),
                            str(tag.a(href='#ref_%s' %
                                key)('%d' % value[":index"])),
                            ',', page, ']'])

    def pre_process_entry(self, key, cite):
        if ":index" not in cite[key]:
            cite[key][":index"] = len(cite)

    def format(self, entries, label):
        div = tag.div(class_="references")
        div.append(tag.h1(id='references')(label))
        count = 0
        for key, value in entries:
            count = count + 1
            sortkey = tag.span(class_="key")
            sortkey.append("[" + str(count) + "]")
            element = tag.div(class_=value["type"])
            element.append(sortkey)
            element.append(self.format_entry(key, value))
            div.append(element)

        return div

    #IRequestFilter
    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        add_stylesheet(req, "tracbib/base.css")
        return (template, data, content_type)

    #ITemplateProvider
    def get_htdocs_dirs(self):
        return [('tracbib', resource_filename('tracbib', 'htdocs'))]

    def get_templates_dirs(self):
        return []
