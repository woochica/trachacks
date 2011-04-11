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
from helper import replace_tags
from bibtexparse import capitalizetitle, authors
try:
  from genshi.builder import tag
except ImportError: # for trac 0.10:
  from trac.util.html import html as tag

BIBTEX_PERSON = [
    'author',
    'editor',
    'publisher',
]

BIBTEX_KEYS = [
    'author',
    'editor',
    'title',
    'intype',
    'booktitle',
    'edition',
    'doi',
    'series',
    'journal',
    'volume',
    'number',
    'organization',
    'institution',
    'publisher',
    'school',
    'howpublished',
    'day',
    'month',
    'year',
    'chapter',
    'volume',
    'paper',
    'type',
    'revision',
    'isbn',
    'pages',
]

class BibRefFormatterBasic(Component):
    implements(IBibRefFormatter)

    def formatter_type(self):
        return "basic"

    def format_entry(self,key,value):
        content = ''
        for bibkey in BIBTEX_KEYS:
            if value.has_key(bibkey):
                if bibkey in BIBTEX_PERSON:
                    content += authors(value[bibkey])+', '
                else:
                    content += capitalizetitle(replace_tags(value[bibkey])) + ', '
        if value.has_key('url') == False:
            return tag.li(tag.a(name='ref_%s' % key), tag.a(href='#cite_%s' % key)('^') ,content)
        else:
            url = value['url']
            return tag.li(tag.a(name='ref_%s' % key), tag.a(href='#cite_%s' % key)('^') ,content, tag.br(),tag.a(href=url)(url))

    def format_ref(self,entries,label):
        return self.format_fullref(entries,label)

    def format_fullref(self,entries,label):
        cited = []
        notcited = []
        #first let's render cited articles
        for key,value in entries:
            if value.has_key(':index'):
                cited.append((key,value))
            else:
                notcited.append((key,value))
        
        cited.sort(key = lambda entry:entry[1][':index'])
        notcited.sort(key = lambda entry:entry[1]['author'])

        for key,value in notcited:
            cited.append((key,value))

        return self.format(cited,label)

    def format_cite(self,key,value):
        return ''.join(['[', str(tag.a(name='cite_%s' % key)),str(tag.a(href='#ref_%s' % key)('%d' % value[":index"])), ']'])

    def pre_process_entry(self,key,cite):
        if not cite[key].has_key(":index"):
            cite[key][":index"]=len(cite)

    def format(self,entries,label):
        l = []
        for key,value in entries:
            l.append(self.format_entry(key,value))
        ol = tag.ol(*l)
        tags = []
        tags.append(tag.h1(id='References')(label))
        tags.append(ol)
        return tags