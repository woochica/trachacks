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
from trac.wiki.api import WikiSystem
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
    CONF_QUERY = "SELECT text FROM wiki WHERE name = 'WikiTemplateConf' ORDER BY version DESC LIMIT 1"
    template_filename = None
    
    def procesar_wiki(self,text,pageName):
        imageMacroPattern = re.compile('\[\[Image\(([^\:)]+)\)\]\]')
        return re.sub(imageMacroPattern, r'[[Image(%s:\1)]]' % pageName, text)
  
#---------------------------------------------------------------------------------------------------------------------------------------------------              
  
    def get_supported_conversions(self):
        yield('vnd.oasis.opendocument.text','Exportar ODT','vnd.oasis.opendocument.text','text/x-trac-wiki','application/vnd.oasis.opendocument.text', 7)
        yield ('pdf', 'Exportar PDF', 'pdf', 'text/x-trac-wiki', 'application/pdf', 8)
        yield ('msword', 'Exportar DOC', 'msword', 'text/x-trac-wiki', 'application/msword', 9)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
        
    def get_formato(self,format):
        if (format == self.ODT):
            return '.odt'
        elif (format == self.DOC):
            return '.doc'
        else:
            return '.pdf'
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
    
    def convert_content(self,req, input_type,text,output_type):
        #self.__loadTemplatePage()
        self.env.log.debug(req.args)
        cadena = wiki_to_html(self.procesar_wiki(text, req.args['page']),self.env,req).encode(self.env.config.get('trac', 'charset', 'utf-8'),'replace')
        if self.template_filename == None:
            parser = Formatter(self.env.config)
        else:
            parser = Formatter(self.env.config,self.template_filename)
        parser.write(self.env,'<body>' + cadena + '</body>',req.base_url)
        filePath = parser.returnDocument(self.get_formato(req.args['format']))
        req.send_file(filePath)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
        
    def __outputFile(self, req, filePath, mime):
        req.send_response()
        req.send_header('Content-Type', mime)
        req.end_headers()
        req.write()
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
        
    def __loadTemplatePage(self):
        wiki_system = WikiSystem(self.env)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(self.CONF_QUERY)
        for (text,) in cursor:
            page_content = text
            break
        
        for line in page_content.strip().splitlines():
            if line.find('=') != -1:
                name, value = [token.strip()
                    for token in line.split("=", 2)]
                if name == 'template_list':
                    template_list = value.split(', ')
                if name == 'template_file':
                    template_file = value.split(', ')
                    #self.template_filename = os.path.join(
                    #    self.env.path, 'attachments', 'wiki',
                    #    'WikiTemplateConf', value)
        
        #self.env.log.debug('El contenido de la pagina es: ' + template_list + ' ' + template_file)
                