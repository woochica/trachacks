#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Claudio Manuel Fernández Barreiro <claudio.sphinx@gmail.com>
'''

from trac.core import *
from BeautifulSoup import BeautifulSoup, NavigableString
from trac.util import escape
from service import Service
from trac.mimeview.api import IContentConverter
from trac.wiki.formatter import wiki_to_html
from tempfile import mkstemp
import os
import re, string

import urllib, Image, tempfile, ImageFile

class Formatter():
    
    def __init__(self,config):
        self.exporter = Service(config)
        self.config = config
        self.row = -1
        self.col = -1
        self.tableNum = 0
        self.texto = ''

    def addUser(self,texto):
        if len(self.env.config.get('openOffice-exporter','user')) > 0:
            urlPattern = re.compile('http://(.*)')
            pagina = re.sub(urlPattern, r'http://%s:%s@\1' % (self.config.get('openOffice-exporter','user'),self.config.get('openOffice-exporter','psswrd')), texto)
            return pagina
        return texto

#---------------------------------------------------------------------------------------------------------------------------------------------------            
        
    def _limpiarLineas_(self,texto):
        cadena = texto
        if cadena == '\n':
            return ''
        if cadena[0] == '\n':
            cadena = cadena[1:]
        if cadena[-1] == '\n':
            cadena = cadena[:-1]
        return cadena    

#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def _concatenarTexto_(self,element):
        self.env.log.debug('++++ %s: ',element)
        for tok in element:
            if type(tok) == NavigableString:
                self.texto = self.texto + tok
            else:
                self._concatenarTexto_(tok)
        return self.texto

#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def writeElement(self,element,tipo):
        if ((tipo != None) and (tipo == 'strong')):
            self.exporter.insertBold(self._limpiarLineas_(element))
        elif ((tipo != None) and (tipo == 'i')):
            self.exporter.insertItalic(self._limpiarLineas_(element))
        elif ((tipo != None) and (tipo == 'italicbold')):
            self.exporter.insertItalicBold(self._limpiarLineas_(element))
        elif ((tipo != None) and (tipo == 'td') and (re.match('.*\w.*',self._limpiarLineas_(element)))):
            self.env.log.debug('entro en insertar datos tabla con el siguiente dato (%d,%d) : %s',self.row,self.col, self._limpiarLineas_(element))
            self.exporter.insertTableData('tabla' + str(self.tableNum),self.row, self.col,self._limpiarLineas_(element))
        elif ((tipo != None) and (re.match('h\d+',tipo))):
            escribir = re.match('h(\d+)',tipo)
            self.exporter.insertHeader(self._limpiarLineas_(element),int(escribir.group(1)))
            self.exporter.generateBreakContent()   
        else:
            self.exporter.insertText(self._limpiarLineas_(element))


#---------------------------------------------------------------------------------------------------------------------------------------------------            
    
    def preAction(self, element,nivel):
        #self.env.log.debug('Entro en pre Action con un elemento %s',element.name)
        if element.name == 'img':
            if re.match('http://.*',element['src']):
                imagen = self.addUser(element['src'])
            else:
                imagen = self.addUser(self.page) + element['src']
            self.env.log.debug('------------------------------------> %s',imagen)
            self.exporter.insertImage(imagen)    
                    
        #En caso de que encontremos un bullet o una enumeracion, insertamos el simbolo
        if element.name == 'li':
            if (element.parent.name == 'ul'):
                self.exporter.insertBulletSymbol(nivel-1)
            elif (element.parent.name == 'ol'):
                self.exporter.insertNumberingSymbol(nivel-1)

        if element.name == 'table':
            self.tableNum = self.tableNum + 1
            self.row = -1
            self.exporter.insertDinamicTable('tabla' + str(self.tableNum))

        if element.name == 'tr':
            self.row = self.row + 1
            self.env.log.debug 
            self.col = -1
            if self.row > 0:
                self.exporter.insertTableRow('tabla' + str(self.tableNum))
        
        if element.name == 'td':
            self.col = self.col + 1
            if self.col > 0 and self.row == 0:
                self.exporter.insertTableCol('tabla' + str(self.tableNum))                

#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def action(self,element,token,tipo,nivel):
        #Si es una enumeracion o una numeracion, incrementamos un nivel
        if element.name == 'td':
            self.procesarContent(self._concatenarTexto_(element), 'td', nivel)
            self.texto = ''
        elif element.name in ('ul','ol'):
            self.procesarContent(token, element.name, nivel + 1)

        elif element.name == 'span' and element.parent.parent.name == 'td' and type(token) == NavigableString:
            self.procesarContent(token, 'td', nivel)

        #Si detectamos un anidamiento de cursivas y negritas, marcamos el nuevo estilo
        elif element.name in ('i','strong') and tipo in ('strong','i'):
            self.procesarContent(token, 'italicbold',nivel)
        
        #En cualquier otro caso
        else:
            self.procesarContent(token, element.name,nivel)

#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def postAction(self,element,nivel):
        #Si hemos procesado una numeracion o enumeracion, y estamos en el nivel mas bajo, la desactivamos        
        if (nivel == 0 and element.name in ('ul','ol')):
            self.exporter.generateBreakContent()
            
        if element.name in ('p','table'):
            self.exporter.generateBreakContent()
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
                    
    def procesarContent(self,element, tipo=None, nivel=0):
        
        #En caso de que encontremos un string, lo insertamos con el estilo correspondiente        
        if type(element) == NavigableString or tipo == 'td':          
            self.writeElement(element, tipo)
            return
        
        self.preAction(element,nivel)
        
        #iteramos entre los distintos componentes de la estructura
        for token in element:
            self.action(element, token, tipo, nivel)
        
        self.postAction(element,nivel)

#---------------------------------------------------------------------------------------------------------------------------------------------------
            
    def write(self,environment,texto, page):
        self.page = re.sub('(/[A-Za-z0-9]*)*$','',page)
        environment.log.debug('La pagina que nos ocupa es %s',self.page)
        self.soup = BeautifulSoup(texto, fromEncoding='utf8')
        self.env = environment
        self.env.log.debug(self.soup.prettify())
        for element in self.soup.body:
            self.procesarContent(element)
                
    def returnDocument(self, formato):
        return self.exporter.saveContent(formato)
        