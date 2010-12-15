#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Claudio Manuel Fernández Barreiro <claudio.sphinx@gmail.com>
         Carlos López Pérez <carlos.lopezperez@gmail.com>
           * 09/12/2009 
            - Simplificación de código
            - Se refactoriza la inicialización de los componentes.
            - Se gestiona el posible fallo de que el servidor de openoffice no 
              esté operativo.
            - Se añade soporte docx
            - Se añade soporte de subrayado
            - Se añade soporte de tachado
            - Se añade soporte de pre
'''

import os
import re

from tempfile import mkstemp

from trac.core import Component, implements
from trac.mimeview.api import IContentConverter
from trac.util import escape
from trac.wiki.api import WikiSystem
from trac.wiki.formatter import wiki_to_html

from genshi.core import Markup

from openoffice import Formatter
from parser import HTMLParser

class Export(Component):
    """ Clase que se integra con el TRAC y gestiona la configuración e 
        inicialización de las clases de soporte.
    """    
    implements(IContentConverter)
    
    CONF_QUERY = "SELECT text FROM wiki WHERE name = 'WikiTemplateConf' ORDER BY version DESC LIMIT 1"
    FORMAT = {'vnd.oasis.opendocument.text': ('.odt', 'application/vnd.oasis.opendocument.text'), 
              'pdf': ('.pdf', 'application/pdf'),
              'msword': ('.doc', 'application/msword'),
              'vnd.openxmlformats-officedocument.wordprocessingml.document' : ('.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
              'rtf': ('.rtf', 'application/rtf'),
              }
    IMAGE_MACRO = re.compile('\[\[Image\(([^\:)]+)\)\]\]')
    INDEX_MACRO = re.compile('\[\[PageOutline*\]\]')
    INIT = False

    #--------------------------------------------------------------------------
    # ------------------------------------------------------------ init methods
    #--------------------------------------------------------------------------    
    
    def __load_plugin(self):
        """ Gestiona los componentes de soporte, sus dependencias y la 
            configuración suministrada por el Trac.
        """
        if self.INIT:
            return
        self.enabled = False
       
        # inicialización del openoffice-formatter
        host = self.config.get('openOffice-exporter','host','localhost')
        port = self.config.get('openOffice-exporter','port','8100')
        
        para_style = self.config.get('openOffice-exporter','para-styles','Cuerpo de texto, Texto preformateado, Encabezado 1, Encabezado 2, Encabezado 3, Encabezado 4, Encabezado 5, Encabezado 6, Encabezado 7, Encabezado 8, Encabezado 9, Encabezado 10').split(', ')
        char_style = self.config.get('openOffice-exporter','char-styles','Predeterminado, Texto fuente, Vínculo Internet').split(', ')
        list_style = self.config.get('openOffice-exporter','list-styles','Enumeración 1, Numeración 1, Numeración 2, Numeración 3').split(', ')
        
        user = self.config.get('openOffice-exporter','user', None) 
        passwd = self.config.get('openOffice-exporter','password', None)
        
        attribute  = self.config.get('openOffice-exporter','isPersonalizeAttribute', 'False') == 'True'

        formatter = Formatter(host, port, self.env.log)
        formatter.setStyles(para_style, char_style, list_style, attribute)
 
        # inicialización del html-parser
        self.parser = HTMLParser(user, passwd, self.env.log)
        self.parser.setFormatter(formatter)

        if formatter.isEnabled:
            self.enabled = True
        self.INIT = True

    #--------------------------------------------------------------------------
    # -------------------------------------------- implements IContentConverter
    #--------------------------------------------------------------------------
    
    def get_supported_conversions(self):
        """ Obtiene los filtros de trasformación soportados. Se comprueba si
            está habilitado el servicio openoffice.
        """
        print '------> Baseurl', self.env.base_url
        print '------> Baseurl', self.env.base_url_for_redirect
        if not self.INIT:
            self.__load_plugin()
        if not self.enabled:
            return
        yield ('pdf', 'pdf', 'pdf', 'text/x-trac-wiki', 'application/pdf', 8)            
        yield('vnd.oasis.opendocument.text', 'odt','vnd.oasis.opendocument.text','text/x-trac-wiki','application/vnd.oasis.opendocument.text', 9)
        yield ('msword', 'doc', 'msword', 'text/x-trac-wiki', 'application/msword', 7)
        yield ('rtf', 'rtf', 'rtf', 'text/x-trac-wiki', 'application/rtf', 6)
        #yield ('vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx', 'vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/x-trac-wiki', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 5)

    def convert_content(self, req, input_type, text, output_type):
        """ Realiza la trasformación en base a la conversión seleccionada
        """
        pageName = req.args['page']
        templatePath = self.__loadTemplatePage(pageName)
        self.env.log.debug('Plantilla seleccionada %s' % templatePath)
        
        self.parser.setTemplate(templatePath, pageName, req.session['name'])
        
        self.env.log.debug('Texto wiki previo %s' % text)
        clean_text = self.__cleanwiki(text, pageName)
        self.env.log.debug('Texto wiki procesado %s' % clean_text)
        htmlwiki = wiki_to_html(clean_text, self.env, req, absurls=True).encode(self.env.config.get('trac', 'charset', 'utf-8'), 'replace')

        self.env.log.debug('Pagina renderizada:\n\n%s\n\n' % htmlwiki)
        self.parser.read('<body>' + htmlwiki + '</body>')
        filePath = self.parser.generateDocument(self.FORMAT[req.args['format']][0])
        self.env.log.info('Fichero generado %s' % filePath)
        req.send_file(filePath, self.FORMAT[req.args['format']][1])
        
    #--------------------------------------------------------------------------
    # ---------------------------------------------------------- helper methods
    #--------------------------------------------------------------------------    

    def __cleanwiki(self, text, pageName):
        clean = re.sub(self.INDEX_MACRO, '', text)
        clean = re.sub(self.IMAGE_MACRO, r'[[Image(%s:\1)]]' % pageName, clean)
        return clean
        
         
    def __loadTemplatePage(self,pagina):
        """ Carga la plantilla desde los adjuntos de una página wiki concreta
        """
        page_content = ''
        template_list = []
        template_file = []
        wiki_system = WikiSystem(self.env)
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        cursor.execute(self.CONF_QUERY)
        for (text, ) in cursor:
            page_content = text
            self.env.log.debug('Accedo a la pagina de plantillas %s', page_content)
            break
        
        for line in page_content.strip().splitlines():
            if line.find('=') != -1:
                name, value = [token.strip()
                    for token in line.split("=", 2)]
                self.env.log.debug('-------> %s %s',name, value)
                if name == 'template_list':
                    template_list = value.split(', ')
                if name == 'template_file':
                    template_file = value.split(', ')
        i = 0
        for element in template_list:
            self.env.log.debug('->>>>>>> %s', pagina)
            if re.match('.*' + element + '.*', pagina):
                return os.path.join(self.env.path, 'attachments', 'wiki','WikiTemplateConf', template_file[i])
            i = i + 1
        return None                