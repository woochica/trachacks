#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Claudio Manuel Fernández Barreiro <claudio.sphinx@gmail.com>
         Carlos López Pérez <carlos.lopezperez@gmail.com>
           * 09-12-2009
               - Refactorización de código. 
               - Intento de añadir enlaces.
               - Adición de quotas.
               - Eliminación de espacios y \n superfluos.
               - Sangrado de los listados.
               - Anidamiento de etiquetas siguiendo el orden strong->i->tt->a
               - Se añade soporte de subrayado
               - Se añade soporte de tachado
               - Se añade soporte de pre               
"""

import sys
import os
import re
import string
import logging

from BeautifulSoup import BeautifulSoup, NavigableString
from openoffice import Formatter

class HTMLParser():
    """ Clase que realiza un parseo del renderizado html de las páginas wiki e 
        intenta traducir el contenido a un documento odt utilizando el api 
        suministrado por el OpenofficeFormatter.
    """
    
    HEADER = re.compile('h(\d+)')
    NO_EOL = re.compile('^([ \t]*\n)')
    
    # -------------------------------------------------------------------------
    # ------------------------------------------------------------ init methods
    # -------------------------------------------------------------------------                        
    
    def __init__(self, user=None, passwd=None, logger=None):
        """ Inicialización genérica
        """
        self.isBreak = True
        self._formatter = None
        self._user = user
        self._passwd = passwd
        self.logger = logger
        self.baseURL = 'http://'        
        if not logger:
            self.logger = logging.getLogger()
    
    def setFormatter(self, formatter):
        """ Se inyecta el servicio de formateo de documentos para openoffice
        """
        self._formatter = formatter
    
    def setTemplate(self, template=None, title='Título', author='Autor'):
        self._formatter.setTemplate(template)
        self._formatter.updateUserInfo(title, author)
        
    # -------------------------------------------------------------------------
    # ------------------------------------------------------------- api methods
    # -------------------------------------------------------------------------                    
        
    def read(self, texto):
        """ Recorre el documento html, desde el cuerpo.
        """
        if not self._formatter.isEnabled:
            return
        for element in BeautifulSoup(texto, fromEncoding='utf8').body:
            if type(element) == NavigableString:   # normally, case to ignore
                continue
            self.__parser_tag(element)
            
    def generateDocument(self, format):
        """ Genera el documento y devuelve una ruta accesible para poder
            ser descargada por el navegador.
        """
        return self._formatter.saveContent(format)
            
    # -------------------------------------------------------------------------
    # ------------------------------------------------------- transform methods
    # -------------------------------------------------------------------------
    
    def __parser_tag(self, tag, deep=-1):
        """ Procesa las etiquetas html del documento.
        """        
        if type(tag) == NavigableString:
            text = self.__clean_text(tag)
            if text == '':
                self.logger.debug('Vacio se ignora. Tag padre {%s}' % tag.parent)
                return
            self._formatter.insertText(text)
            self.isBreak = False
        elif tag.name == 'br':
            self._formatter.generateBreakContent()
            self.isBreak = True
            return
        elif tag.name in ('strong', 'i', 'tt', 'del', 'a', 'span'):
            self.__write_text(tag, deep)
        elif tag.name in 'p':
            self.__write_p(tag, deep)
        elif tag.name == 'li':
            self.__write_li(tag, deep)
        elif tag.name in ('ul', 'ol'):
            self.__write_ulol(tag, deep+1)
        elif self.HEADER.match(tag.name):
            self.__write_h(tag, deep)
        elif tag.name == 'img':
            self.__write_img(tag, deep)
        elif tag.name == 'pre':
            self.__write_pre(tag, deep)
        elif tag.name == 'hr':        
            self.__write_hr(tag, deep)
        elif tag.name == 'dt':
            self.__write_dt(tag, deep)            
        else:
            self.logger.warn('Tag no reconocido {%s}. Se profundiza en el contenido' % tag)
            if tag.name == 'table' or (tag.name == 'div' and tag.has_key('class') and 'wiki-toc' in tag['class']):
                return
            for e in tag.contents:
                self.__parser_tag(e, deep)
                
    def __write_text(self, tag, deep):
        """ Escribe un texto que contiene una o varias palabras.
        """
        if tag.name == 'span' and (not tag.has_key('class') or tag['class'] != 'underline'):
            return
        text, intag, link = self.__analize_tag(tag)        
        
        if tag.name == 'a' and 'img' in intag:          ## quita los espacios ocasionados por las imágenes de los enlaces al mailto
            self.__parser_tag(tag.contents[0], deep)
            return
        
        bold = False
        italic = False
        quoted = False
        underline = False
        strike = False
        url = False
        if tag.name == 'strong' or 'strong' in intag: 
            bold = True
        if tag.name == 'i' or 'i' in intag: 
            italic = True            
        if tag.name == 'tt' or 'tt' in intag:
            quoted = True
        if tag.name == 'del' or 'del' in intag:
            strike = True
        if tag.name == 'span' or 'underline' in intag:                        
            underline = True
        if tag.name == 'a' or 'a' in intag:
            url = link
            
        self._formatter.insertText(text, bold, italic, quoted, underline, strike, url)
        self.isBreak = False                
                
    def __write_hr(self, tag, deep):
        """ Inserta un texto tal cual
        """
        if not self.isBreak:
            self._formatter.generateBreakContent()
        self._formatter.insertHorizontalRule()
        self._formatter.generateBreakContent()
        self.isBreak = True                
                
    def __write_pre(self, tag, deep):
        """ Inserta un texto tal cual
        """
        if len(tag.contents) != 1:
            self.logger.error('No existe contenido en el tag pre, cuyo tag padre es "%s".' % tag.parent)
            return                
        if not self.isBreak:
            self._formatter.generateBreakContent()
        self._formatter.insertBorderText(self.__escape_text(tag.contents[0]))
        self._formatter.generateBreakContent()
        self.isBreak = True            
                
            
    def __write_img(self, tag, deep):
        """ Inserta una imagen.
        """
        if not tag.has_key('src'):
            self.logger.warn('No existe enlace de la imagen que tiene como padre "%s".' % tag.parent)
            return
        if not self.isBreak:
            self._formatter.generateBreakContent()
        imgurl = tag['src']
        if self._user:
            imgurl = imgurl.replace('http://', 'http://%s:%s@' % (self._user, self._passwd))           
        self.logger.debug('URL Imagen "%s"' % imgurl)
        self._formatter.insertImage(imgurl)
        self.isBreak = True
               
    def __write_h(self, tag, deep):
        """ Escribe una cabecera, dependiendo del anidamiento.
        """
        if not self.isBreak:
            self._formatter.generateBreakContent()
        text, intag, link = self.__analize_tag(tag)
        level = int(self.HEADER.match(tag.name).group(1))
        self._formatter.insertHeader(text.strip(), level)
        self._formatter.generateBreakContent()
        self.isBreak = True
            

    def __write_dt(self, tag, deep):
        """ Procesa el término a definir.
        """
        if not self.isBreak:
            self._formatter.generateBreakContent()
            self.isBreak = True
        self.__write_text(tag, deep)        
        if not self.isBreak:
            self._formatter.generateBreakContent()
            self.isBreak = True
                
    def __write_p(self, tag, deep):
        """ Procesa el contenido de un párrafo
        """
        for element in tag.contents:
            self.__parser_tag(element, deep)
        if not self.isBreak:
            self._formatter.generateBreakContent()
            self.isBreak = True
        
    def __write_li(self, tag, deep):
        """ Procesa un elemento de una lista
        """
        first = False
        if not tag.previousSibling:
            first = True                  # es el primero si no tiene hermanos previos.
        f = self._formatter.insertBulletSymbol
        if tag.parent and tag.parent.name == 'ol':
            f = self._formatter.insertNumberingSymbol
        for element in tag.contents:
            f(deep)
            if first:
                self._formatter.initNumbering()
                first = False
            self.__parser_tag(element, deep)
        if not self.isBreak:
            self._formatter.generateBreakContent()
            self.isBreak = True
                        
    def __write_ulol(self, tag, deep):
        """ Procesa el contenido de un listado de topos o numerado.
        """        
        if not self.isBreak:
            self._formatter.generateBreakContent()
            self.isBreak = True
        for element in tag.contents:
            if type(element) == NavigableString and self.__clean_text(element) == '':
                continue
            self.__parser_tag(element, deep)
        self._formatter.deleteNumbering()
        
    # -------------------------------------------------------------------------
    # ---------------------------------------------------------- helper methods
    # -------------------------------------------------------------------------                    

    def __analize_tag(self, tag):
        """Obtiene el texto de tags, anidados.
        
        Devuelve una tupla con el texto obtenido y una lista de tags 
        recorridos
           
        """
        text, tname, link = '', (), ''
        
        if tag.name == 'a' and tag.has_key('href'):
            link = tag['href']
            if tag.has_key('class') and 'closed' in tag['class']:
                tname += ('del', )

        for element in tag.contents:
            if type(element) == NavigableString:
                text += self.__clean_text(element)
                continue
            if tag.name == 'a': 
                if element.name == 'span':
                    if element.has_key('class') and 'underline' in element['class']:
                        tname += ('underline', )
                    continue
            tname += (element.name, )
            a, b, c = self.__analize_tag(element)
            text += a
            tname += b
            if c:
                link = c
        return text, tname, link
    
    def __escape_text(self, text):
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        text = text.replace("&hellip;", "...")
        
        return text
    
    def __clean_text(self, text):
        """ Limpia el texto de \n y de trasforma entidades html a símbolos
        """
        text = self.__escape_text(text)

        m = self.NO_EOL.match(text)
        if not m:
            return text.replace('\n', '')
        return text.replace(m.group(0), '').replace('\n', '')

