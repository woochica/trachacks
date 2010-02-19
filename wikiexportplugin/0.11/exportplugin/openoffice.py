#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Claudio Manuel Fernández Barreiro <claudio.sphinx@gmail.com>
         Carlos López Pérez <carlos.lopezperez@gmail.com>
           * 09-12-2009         
               - Intento de añadir enlaces. No se consigue, se simula con formato.
               - Adición de frames.
               - Adición de quotas.
               - Sangrado de los listados.
               - Cambio del uso de negritas e itálicas (por incompatibilidades en el listado)
               - Posibilidad de cambiar el color del texto.
               - Se refactoriza la inserción de imágenes
               - Se añade soporte docx
               - Se añade soporte de subrayado
               - Se añade soporte de tachado
               - Se añade soporte de pre
               
"""

import os
import sys
import tempfile
import logging
import urllib

import Image

import uno
import unohelper

from com.sun.star.awt import Size, Point

from com.sun.star.awt.FontStrikeout import NONE as STRIKE_NONE
from com.sun.star.awt.FontStrikeout import SINGLE as STRIKE_SINGLE

from com.sun.star.awt.FontSlant import NONE as SLANT_NONE
from com.sun.star.awt.FontSlant import ITALIC as SLANT_ITALIC 

from com.sun.star.awt.FontWeight import NORMAL as WEIGHT_NORMAL 
from com.sun.star.awt.FontWeight import BOLD as WEIGHT_BOLD 

from com.sun.star.awt.FontUnderline import NONE as UNDERLINE_NONE
from com.sun.star.awt.FontUnderline import SINGLE as UNDERLINE_SINGLE

from com.sun.star.beans import PropertyValue

from com.sun.star.text.ControlCharacter import PARAGRAPH_BREAK
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
from com.sun.star.text.WrapTextMode import NONE as WRAP_NONE
from com.sun.star.style.ParagraphAdjust import CENTER as PA_CENTER


class Formatter():
    
    URL = "private:factory/swriter"
    TMPDIR = "wikiexport-cache"

    FILTER = {
        '.pdf':  ("writer_pdf_Export", "pdf"),
        '.doc':  ("MS Word 97", "doc"),
        '.docx': ("MS Word 2007 XML", "docx"),
        '.rtf': ("Rich Text Format", "rtf")
    }
    
    def __init__(self, url='localhost', port='8100', logger=None):
        
        self.__personalField = False
        self.__PARASTYLES = 'Cuerpo de texto, Texto preformateado, Encabezado 1, Encabezado 2, Encabezado 3, Encabezado 4, Encabezado 5, Encabezado 6, Encabezado 7, Encabezado 8, Encabezado 9, Encabezado 10'.split(', ')
        self.__CHARSTYLES = 'Predeterminado, Texto fuente, Vínculo Internet'.split(', ')
        self.__NUMSTYLES = 'Enumeración 1, Numeración 1, Numeración 2, Numeración 3'.split(', ')
                
        self.logger = logger        
        if not logger:
            self.logger = logging.getLogger()
        
        self._url = url
        self._port = port
        
        self.isEnabled = self.__connect()        

    def __connect(self):
        """ Realiza la conexión con el openoffice
        """
        # conexión con el servidor openoffice
        try:
            self.desktop = self.__connectOpenOfficeService(self._url, self._port)
        except Exception:
            self.logger.error('No se pudo realizar la conexion con el openoffice "%s:%s"' % (self._url, self._port))
            return False
        return True

    def setStyles(self, para, char, list, personalField=False):
        if not self.isEnabled:
            self.logger.warn('No se puede actualizar los estilos ya que el servidor openoffice no esta activo.')
            return        
        self.__PARASTYLES = para
        self.logger.debug('Estilos de parrafos %s' % str(self.__PARASTYLES))
        self.__CHARSTYLES = char
        self.logger.debug('Estilos de caracteres %s' % str(self.__CHARSTYLES))
        self.__NUMSTYLES = list
        self.logger.debug('Estilos de numeros %s' % str(self.__NUMSTYLES))
        self.__personalField = personalField

    def setTemplate(self, t=None):
        """ Carga la plantilla o un documento en blanco. Inicializa las estructuras
        """
        self.logger.debug('Actualizando la plantilla "%s"' % t)
        self.isEnabled = self.__connect()
        if not self.isEnabled:
            return
        if not t:
            self.document = self.__createDocument()
        else:
            self.document = self.__createTemplate(t)

        self.text = self.document.Text
        self.cursor = self.text.getEnd()
            
        #self.createIndex()
        
        self.enumStyles = self.document.getStyleFamilies().getByName('NumberingStyles')
        self.imageCounter = 18
        self.footCounter = 1  
        
        self.logger.debug('Inicializado elementos "%s"' % t)
        
    # -------------------------------------------------------------------------    
    # -------------------------------------------------------- document methods
    # -------------------------------------------------------------------------
            
    def saveContent(self, formato):
        if not self.isEnabled:
            return        

        if self.document.DocumentIndexes.getCount() > 0:        # se actualiza el primer índice
            index = self.document.DocumentIndexes.getByIndex(0)
            index.update()
            
        p = os.path.join(tempfile.gettempdir(), self.TMPDIR)
        if not os.path.exists(p):
            os.mkdir(p)
        fd = os.path.split(tempfile.mktemp(suffix=formato, dir=self.TMPDIR))[1]
        pathDocumento = os.path.join(p, fd)
        
        outProps = ()
        if self.FILTER.has_key(formato):
            filterName = self.FILTER[formato][0]
            extension = self.FILTER[formato][1]
            outProps = (PropertyValue("FilterName" , 0, filterName , 0),)

        self.document.storeToURL('file://' + pathDocumento, outProps)
        self.logger.info('Almancenando documento "%s"' % pathDocumento) 
        #self.document.close(True)
        return pathDocumento
    
    def updateUserInfo(self, title, author='Autor', version='0.1'):
        if not self.isEnabled:
            #self.logger.error('No se puede actualizar la informacion, ya que el servidor openoffice no esta activo.')
            return        
        if self.__personalField:
            self.document.DocumentProperties.UserDefinedProperties.Autor = author
            self.document.DocumentProperties.UserDefinedProperties.Version = version
        self.document.DocumentInfo.Author = author
        self.document.DocumentInfo.Title = title
        #self.document.DocumentInfo.Revision = version
    
    # -------------------------------------------------------------------------    
    # ---------------------------------------------------------- format methods
    # -------------------------------------------------------------------------
    
    def generateBreakContent(self):
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        self.cursor.setAllPropertiesToDefault()
        self.cursor.ParaStyleName = self.__PARASTYLES[0]
        
    def insertText(self, text, bold=False, italic=False, quoted=False, underline=False, strike=False, url=False, color=None):
        char_color = self.cursor.CharColor        
        self.cursor.ParaStyleName = self.__PARASTYLES[0]
        if quoted:
            self.cursor.CharStyleName = self.__CHARSTYLES[1]  
        if url:
            self.cursor.CharStyleName = self.__CHARSTYLES[2]
        if bold:
            #self.cursor.CharStyleName = self.__CHARSTYLES[3]  # arreglar los principios en negrita de los listados
            self.cursor.CharWeight = WEIGHT_BOLD
        if italic:
            #self.cursor.CharStyleName = self.__CHARSTYLES[4]  # otra forma (¿útil para las tablas?)
            self.cursor.CharPosture = SLANT_ITALIC
        if underline:
            self.cursor.CharUnderline = UNDERLINE_SINGLE       # puede que sea inneceario
        if strike:
            self.cursor.CharStrikeout = STRIKE_SINGLE          # puede que sea inneceario
        
        self.text.insertString(self.cursor, text, 0)
        
        self.cursor.CharStrikeout = STRIKE_NONE
        self.cursor.CharUnderline = UNDERLINE_NONE
        self.cursor.CharPosture = SLANT_NONE
        self.cursor.CharWeight = WEIGHT_NORMAL
        self.cursor.CharStyleName = self.__CHARSTYLES[0]
        self.cursor.CharColor = char_color
        if url:
            self.insertFootnoteURL(url)

    def insertHeader(self, content, header):
        if header > 10:
            self.logger.warn('Se ha superado el limite de encabezado a parmitido. Se recorta a %s -> 10' % str(header))
            header = 10
        self.cursor.ParaStyleName = self.__PARASTYLES[header + 1]
        self.text.insertString(self.cursor, content, 0)   
        
    def insertBorderText(self, content):
        self.cursor.ParaStyleName = self.__PARASTYLES[1]
        self.text.insertString(self.cursor, content, 0)
        
    def insertTextBullet(self, text=None):
        bullet = self.document.createInstance("com.sun.star.text.NumberingRules")
        self.text.insertTextContent(self.cursor, bullet, 0)
        self.text.insertString(self.cursor, text, 0)
        
    def insertHorizontalRule(self):        
        self.cursor.CharStrikeout = STRIKE_SINGLE
        back = self.cursor.ParaAdjust
        self.cursor.ParaAdjust = PA_CENTER
        self.text.insertString(self.cursor, " "*100, 0)
        self.cursor.CharStrikeout = STRIKE_NONE
        #self.cursor.ParaAdjust = back

    # -------------------------------------------------------------------------    
    # ------------------------------------------------------------------ others
    # -------------------------------------------------------------------------

    def insertFootnoteURL(self, content):
        footnote = self.document.createInstance("com.sun.star.text.Footnote")
        footnote.setLabel(str(self.footCounter));
        self.text.insertTextContent (self.cursor, footnote.Text, False);
        footnote.Text.insertString(footnote.createTextCursor(), content, False)
        self.footCounter += 1                
    
    def insertFootnote(self, text, content):
        self.insertText(text)
        footnote = self.document.createInstance("com.sun.star.text.Footnote")
        footnote.setLabel(str(self.footCounter));
        #footnote.setString(content);
        self.text.insertTextContent (self.cursor, footnote.Text, False);
        
        footnote.Text.insertString(footnote.createTextCursor(), content, False)
        self.footCounter += 1
        
    def insertTextLink(self, url, text=None):
        if not text:
            text = url
        link = self.document.createInstance("com.sun.star.text.TextField.URL")
        link.URL = url
        link.Representation = text
        self.cursor.CharStyleName = self.__CHARSTYLES[2]
        self.text.insertTextContent(self.cursor, link, False)   
        
        
    def insertFrame(self):
        textFrame = self.document.createInstance("com.sun.star.text.TextFrame")
        textFrame.setSize(Size(150000, 1))
        textFrame.setPropertyValue("AnchorType" , AS_CHARACTER)
 
        self.text.insertTextContent(self.cursor, textFrame, 0)
 
        textInTextFrame = textFrame.getText()
        cursorInTextFrame = textInTextFrame.createTextCursor()
        textInTextFrame.insertString(cursorInTextFrame, "The first line in the newly created text frame.", 0)
        textInTextFrame.insertString(cursorInTextFrame, "\nWith this second line the height of the rame raises.", 0)
        text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        #self.text.insertString(self.cursor, " Después de", 0)
        
    
    # -------------------------------------------------------------------------    
    # ------------------------------------------------------------ image methods
    # -------------------------------------------------------------------------
    
    def insertImage(self, url):
        try:
            data = urllib.urlopen(url).read()
        except Exception:
            self.logger.error('No se pudo recuperar la imagen ubicada en la url "%s".' % url)
            return
        if 'Error' in data:
            self.logger.warn('No se permite acceder a la localizacion de la imagen ubicada en la url "%s".' % url)
            return
        
        f = tempfile.NamedTemporaryFile()
        f.write(data)
        f.flush()
        f.seek(0)
        
        oBitmaps = self.document.createInstance("com.sun.star.drawing.BitmapTable")
        iname = 'imagen_%i' % self.imageCounter
        oBitmaps.insertByName(iname, "file://%s" % f.name)
        
        oShape = self.document.createInstance('com.sun.star.text.GraphicObject')
        #self.__optimizeSize(f, oShape)        
        oShape.GraphicURL = oBitmaps.getByName(iname)
        
        self.__optimizeSize(f, oShape)
        #oShape.setSize(oShape.Graphic.Size100thMM)
        self.text.insertTextContent(self.cursor, oShape, True)
        oShape.TextWrap = WRAP_NONE
        
        #self.__optimizeSize(f, oShape)
        #oShape.setSize(oShape.Graphic.Size100thMM)
        
        #self.logger.debug('Nuevo tamaño %s' % str((oShape.Graphic.SizePixel.Width, oShape.Graphic.SizePixel.Height)))        
        self.imageCounter += 1
        f.close()
        
    # -------------------------------------------------------------------------        
    # ------------------------------------------------------------ list methods        
    # -------------------------------------------------------------------------
    
    def insertNumberingSymbol(self, estilo, nivel=1, listaNueva=False):
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        self.cursor.ParaStyleName = self.__PARASTYLES[0]
        self.cursor.NumberingRules = self.enumStyles.getByName(estilo).NumberingRules
        self.cursor.NumberingLevel = nivel     
    
    def insertBulletSymbol(self, nivel=1):
        self.__insertNumberingSymbol(self.__NUMSTYLES[0], nivel)
        
    def insertNumberingSymbol(self, nivel=0):
        self.__insertNumberingSymbol(self.__NUMSTYLES[1], nivel)
        
    def insertRomanSymbol(self, texto, nivel=0):
        self.__insertNumberingSymbol(self.__NUMSTYLES[2], nivel) 
        
    def insertAlphabeticSymbol(self, texto, nivel=0):
        self.__insertNumberingSymbol(self.__NUMSTYLES[3], nivel)
        
    def initNumbering(self):
        #self.cursor.setPropertyValue("ParaIsNumberingRestart", True)
        #self.cursor.setPropertyValue("OutlineLevel", 0)
        #self.cursor.setPropertyValue("ParaIsNumberingRestart", True)
        self.cursor.setPropertyValue("NumberingStartValue", 1)
        
    def deleteNumbering(self):
        self.cursor.setPropertyValue("NumberingStartValue", 1)
        self.cursor.setPropertyValue("NumberingRules", None)
        self.cursor.setPropertyValue("NumberingStyleName", "")
#        self.cursor.setAllPropertiesToDefault()
#        self.cursor.ParaStyleName = self.__PARASTYLES[0]
        
        #self.cursor.setPropertyValue("NumberingStartValue", -1)
        
    
    # -------------------------------------------------------------------------    
    # ----------------------------------------------------------- table methods
    # -------------------------------------------------------------------------
    
    def updateTable(self, content, tableName, row, column):
        table = self.document.TextTables.getByName(tableName)
        table.getCellByPosition(column, row).setString(content)
        
    def insertTableCol(self, nombre):
        table = self.document.TextTables.getByName(nombre)
        table.Columns.insertByIndex(table.Columns.Count, 1)
        
    def insertTableRow(self, nombre):
        table = self.document.TextTables.getByName(nombre)
        table.Rows.insertByIndex(table.Rows.Count, 1)
        
    def insertTableData(self, tableName, row, col, texto):
        table = self.document.TextTables.getByName(tableName)
        table.getCellByPosition(col, row).setString(texto)
        
    def insertDinamicTable(self, nombre):
        table = self.document.createInstance("com.sun.star.text.TextTable")
        table.initialize(1, 1)
        table.setPropertyValue("BackTransparent", False)
        table.setName(nombre)
        self.text.insertTextContent(self.cursor, table, 0)
        rows = table.Rows
        row = rows.getByIndex(0);
        row.setPropertyValue("BackTransparent", False)
        
    def insertTable(self, nombre, filas, columnas, data):
        table = self.document.createInstance("com.sun.star.text.TextTable")
        table.initialize(filas, columnas)
        h = table.getPropertySetInfo()
        table.setPropertyValue("BackTransparent", False)
        table.setPropertyValue("BackColor", 13421823)
        
        table.setName(nombre.replace(" ", "_"))

        self.text.insertTextContent(self.cursor, table, 0)
        rows = table.Rows
        row = rows.getByIndex(0)
        row.setPropertyValue("BackTransparent", False)
        row.setPropertyValue("BackColor", 6710932)
        
        fila = 0
        col = 0
        for element in data:
            if col == columnas:
                col = 0
                fila = fila + 1
            table.getCellByPosition(col, fila).setString(element)
            col = col + 1
        
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        
    # -------------------------------------------------------------------------
    # ----------------------------------------------------------- utils methods
    # -------------------------------------------------------------------------
    
    def __optimizeSize(self, f, shape):
        f.flush()
        f.seek(0)
        im = Image.open(f)
        f.seek(0)
        h_prop = float(im.size[1]) / float(im.size[0])
        newsize = [im.size[0], im.size[1]]
        if im.size[0] > 800:
            newsize[0] = 800
            newsize[1] = int(newsize[0] * h_prop)
        w_prop = float(newsize[0]) / float(newsize[1])
        if newsize[1] > 700:
            newsize[1] = 700
            newsize[0] = int(newsize[1] * w_prop)        
        size = Size()
        size.Width = newsize[0] * 20
        size.Height = newsize[1] * 20
        shape.setSize(size)
        self.logger.debug('Nuevo tamaño %s -> %s -> %s' % (str(im.size), str(newsize), str((size.Width, size.Height))))
         
    def __optimizeSize2(self, f):
        f.flush()
        f.seek(0)
        im = Image.open(f)
        h_prop = float(im.size[1]) / float(im.size[0])
        newsize = [im.size[0], im.size[1]]
        if im.size[0] > 800:
            newsize[0] = 800
            newsize[1] = int(newsize[0] * h_prop)
        w_prop = float(newsize[0]) / float(newsize[1])
        if newsize[1] > 700:
            newsize[1] = 700
            newsize[0] = int(newsize[1] * w_prop)
        
        newim = im.resize(newsize, Image.ANTIALIAS)
        self.logger.debug('Cambio el tamano de la imagen a %s' % str(newim.size))
        f.seek(0)
        newim.save(f, "PNG")
        f.flush()
        f.seek(0)
        
    def __insertNumberingSymbol(self, estilo, nivel=0, listaNueva=False):
        self.cursor.ParaStyleName = self.__PARASTYLES[0]
        self.cursor.NumberingRules = self.enumStyles.getByName(estilo).NumberingRules
        self.cursor.NumberingLevel = nivel
    
    def __convertToURL(self, cPathname):
        if len(cPathname) >= 1:
            if cPathname[1:2] == ":":
                cPathname = "/" + cPathname[0] + "|" + cPathname[2:]
        cPathname = cPathname.replace("\\", "/")
        cPathname = "file://" + cPathname
        return cPathname  
        
    def __connectOpenOfficeService(self, host, puerto):
        localContext = uno.getComponentContext()
        resolver = localContext.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", uno.getComponentContext())
        
        #self.dispatchHelper = localContext.ServiceManager.createInstanceWithContext("com.sun.star.frame.DispatchHelper", uno.getComponentContext())

        smgr = resolver.resolve("uno:socket,host=" + host + ",port=" + puerto + ";urp;StarOffice.ServiceManager")
        remoteContext = smgr.getPropertyValue("DefaultContext")
        return smgr.createInstanceWithContext("com.sun.star.frame.Desktop", remoteContext)

                        
    def __createDocument(self):
        return self.desktop.loadComponentFromURL(self.URL, "_blank", 0, ())
        
    def __createTemplate(self, url):
        prop = PropertyValue()
        prop.Name = "AsTemplate"
        prop.Value = True
        return self.desktop.loadComponentFromURL(self.__convertToURL(url), "_blank", 0, (prop,))
    
    def __createIndex(self):
        """ Permite la creación de un index dinámicamente. Debería llamarse 
            posterior a la actualización de la plantilla.
            
        """
        self.index = self.document.createInstance("com.sun.star.text.ContentIndex");
        self.index.setPropertyValue("CreateFromOutline",True);
        
        self.text.insertTextContent(self.cursor, self.index, False);
