#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Claudio Manuel Fernández Barreiro <claudio.sphinx@gmail.com>
'''

from trac.core import *
from trac.mimeview import *
from genshi.core import Markup
from trac.util import escape
from formatter import Formatter
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
from tempfile import mkstemp
import os
import re

EXCLUDE_RES = [
    re.compile(r'\[\[PageOutline([^]]*)\]\]'),
    re.compile(r'\[\[TracGuideToc([^]]*)\]\]'),
    re.compile(r'----(\r)?$\n^Back up: \[\[ParentWiki\]\]', re.M|re.I)
]

class Export(Component):
    implements(IContentConverter)
    
    ODT = 'vnd.oasis.opendocument.text'
    DOC = 'msword'
    PDF = 'pdf'
    
    def procesar_wiki(self,text,pageName):
        imageMacroPattern = re.compile('\[\[Image\(([^\:)]+)\)\]\]')
        return re.sub(imageMacroPattern, r'[[Image(%s:\1)]]' % pageName, text)

    def addUser(self,texto):
        if len(self.env.config.get('openOffice-exporter','user')) > 0:
            urlPattern = re.compile('http://(.*)')
            pagina = re.sub(urlPattern, r'http://%s:%s@\1' % (self.env.config.get('openOffice-exporter','user'),self.env.config.get('openOffice-exporter','psswrd')), texto)
            self.env.log.debug('^^^^^^^^^^^^^^^^^^ %s',pagina)
            return pagina
        return texto
        
    def get_supported_conversions(self):
        yield('vnd.oasis.opendocument.text','Exportar ODT','vnd.oasis.opendocument.text','text/x-trac-wiki','application/vnd.oasis.opendocument.text', 7)
        yield ('pdf', 'Exportar PDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 8)
        yield ('msword', 'Exportar DOC', 'msword', 'text/x-trac-wiki', 'application/msword', 9)
        
    def get_formato(self,format):
        if (format == self.ODT):
            return '.odt'
        elif (format == self.DOC):
            return '.doc'
        else:
            return '.pdf'
        
    
    def convert_content(self,req, input_type,text,output_type):
        cadena = wiki_to_html(self.procesar_wiki(text, req.args['page']),self.env,req).encode(self.env.config.get('trac', 'charset', 'utf-8'),'replace')

        parser = Formatter(self.env.config)
        parser.write(self.env,'<body>' + cadena + '</body>',req.base_url)
        filePath = parser.returnDocument(self.get_formato(req.args['format']))
        req.send_file(filePath)
        
        
    def __outputFile(self, req, filePath, mime):
        req.send_response()
        req.send_header('Content-Type', mime)
        req.end_headers()
        req.write()
        
        
        