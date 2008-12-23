#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
 Copyright (C) 2008 General de Software de Canarias.
 
 Author: Claudio Manuel Fernández Barreiro <claudio.sphinx@gmail.com>
'''
  
import uno
import unohelper
import ImageFile
import urllib
import Image, tempfile, ImageFile

import os

from com.sun.star.text.ControlCharacter  import PARAGRAPH_BREAK, APPEND_PARAGRAPH, LINE_BREAK
from com.sun.star.beans import PropertyValue
from com.sun.star.text.TextContentAnchorType import AS_CHARACTER
from com.sun.star.awt import Size, Point
from com.sun.star.awt.FontWeight import BOLD,NORMAL
from com.sun.star.awt.FontSlant import ITALIC,NONE

from com.sun.star.io import IOException, XOutputStream


class Service():
    
    URL = "private:factory/swriter"
    DEFAULT = 0
    BULLET = 0
    NUMBER = 0
    ROMAN = 3
    ALPHA = 2
    num = 18  
    
    PIX_CONST = 26.46   
    
    def __init__(self,config,template=None):
        self.desktop = self.__connectOpenOfficeService(config.get('openOffice-exporter','host','localhost'),config.get('openOffice-exporter','port','8100'))
        self.__STYLES = config.get('openOffice-exporter','styles','Predeterminado, Encabezado 1, Encabezado 2, Encabezado 3, Encabezado 4, Encabezado 5').split(', ')
        self.__ENUMSTYLES = config.get('openOffice-exporter','enum-styles','Enumeración 1, Enumeración 2, Enumeración 3, Enumeración 4, Enumeración 5').split(', ')
        self.__NUMSTYLES = config.get('openOffice-exporter','num-styles','Numeración 1, Numeración 2, Numeración 3, Numeración 4, Numeración 5').split(', ')
        if template == None:
            self.document = self.__createDocument()
        else:
            self.document = self.__createTemplate(template)
        self.text = self.document.Text
        self.cursor = self.text.getEnd()
        self.enumStyles = self.document.getStyleFamilies().getByName('NumberingStyles')
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
                    
    def __connectOpenOfficeService(self,host,puerto):
        localContext = uno.getComponentContext()
        resolver = localContext.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", uno.getComponentContext())
        smgr = resolver.resolve( "uno:socket,host=" + host + ",port=" + puerto + ";urp;StarOffice.ServiceManager")
        remoteContext = smgr.getPropertyValue("DefaultContext")
        return smgr.createInstanceWithContext("com.sun.star.frame.Desktop", remoteContext)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
                        
    def __createDocument(self):
        return self.desktop.loadComponentFromURL(self.URL,"_blank",0,())
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def __createTemplate(self,url):
        prop = PropertyValue()
        prop.Name = "AsTemplate"
        prop.Value = True
        return self.desktop.loadComponentFromURL(url,"_blank", 0, (prop, ))

        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def makePoint(self, nX, nY ):
        oPoint = Point()
        oPoint.X = nX
        oPoint.Y = nY
        return oPoint
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def makeSize(self, nWidth, nHeight ):
        oSize = Size()
        oSize.Width = nWidth
        oSize.Height = nHeight
        return oSize
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def loadGraphicIntoDocument(self, oDoc , cUrl , cInternalName):
        oBitmaps = oDoc.createInstance( "com.sun.star.drawing.BitmapTable" )
        oBitmaps.insertByName( cInternalName, cUrl )
        cNewUrl = oBitmaps.getByName( cInternalName )   
        return cNewUrl
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
   
    def makeGraphicObjectShape(self, oDoc, oPosition = None, oSize = None):
        oShape = oDoc.createInstance( "com.sun.star.drawing.GraphicObjectShape" )
        if (oPosition != None):
            oShape.Position = oPosition
        if (oSize != None ):
            oShape.Size = oSize
        return oShape 
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
 
    def __insertNumeringSymbol(self,estilo, nivel=0, listaNueva = False):
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        self.cursor.ParaStyleName = self.__STYLES[self.DEFAULT]
        self.cursor.NumberingRules = self.enumStyles.getByName(estilo).NumberingRules
        self.cursor.NumberingLevel = nivel

#---------------------------------------------------------------------------------------------------------------------------------------------------            
    
    def updateTable(self, content, tableName, row, column):
        table = self.document.TextTables.getByName(tableName)
        table.getCellByPosition(column, row).setString(content)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
        
    def insertTableCol(self,nombre):
        table = self.document.TextTables.getByName(nombre)
        table.Columns.insertByIndex(table.Columns.Count,1)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------                
    def insertTableRow(self,nombre):
        table = self.document.TextTables.getByName(nombre)
        table.Rows.insertByIndex(table.Rows.Count,1)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------                 
        
    def updateUserInfo(self, content, i):
        self.document.DocumentInfo.setUserFieldValue(i, content)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------                

    def generateBreakContent(self):
        self.deleteNumbering()
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        self.cursor.setAllPropertiesToDefault()
        self.cursor.ParaStyleName = self.__STYLES[self.DEFAULT]
            
#---------------------------------------------------------------------------------------------------------------------------------------------------            
    
    def insertBold(self,content):
        self.cursor.setPropertyValue("CharWeight",BOLD)
        self.insertText(content)
        self.cursor.setPropertyValue("CharWeight",NORMAL)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
    
    def insertItalic(self,content):
        self.cursor.setPropertyValue("CharPosture",ITALIC)
        self.insertText(content)
        self.cursor.setPropertyValue("CharPosture",NONE)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
    
    def insertItalicBold(self,content):
        self.cursor.setPropertyValue("CharWeight",BOLD)
        self.insertItalic(content)
        self.cursor.setPropertyValue("CharWeight",NORMAL)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
      
    def insertHeader(self,content,header):
        self.cursor.ParaStyleName = self.__STYLES[header]
        self.text.insertString(self.cursor, content, 0)   
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
     
    def insertText(self,content):
        self.text.insertString(self.cursor, content, 0)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def insertImage(self,url,comentario_imagen=""):
        data = urllib.urlopen(url).read()
        f = tempfile.NamedTemporaryFile()
        f.write(data)
        f.flush()
        f.seek(0)
        img = Image.open(f)
        f.seek(0)
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        fich = "file://" + f.name
        cUrl = self.loadGraphicIntoDocument( self.document, fich, "Image"+str(self.num))
        self.num = self.num + 1
        oShape = self.makeGraphicObjectShape(self.document, self.makePoint(100, 100),self.makeSize(img.size[0] * self.PIX_CONST, img.size[1] * self.PIX_CONST))
        oShape.GraphicURL = cUrl
        self.text.insertTextContent(self.cursor, oShape,False)
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        
        self.cursor.ParaStyleName = self.__STYLES[self.DEFAULT]
        self.text.insertString(self.cursor, comentario_imagen, 0)
        f.close()
         
#---------------------------------------------------------------------------------------------------------------------------------------------------            
   
    def insertBulletSymbol(self,nivel = 0):
        self.__insertNumeringSymbol(self.__ENUMSTYLES[self.BULLET], nivel)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
   
    def insertNumberingSymbol(self,nivel = 0):
        self.__insertNumeringSymbol(self.__NUMSTYLES[self.NUMBER], nivel)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
          
    def insertRomanSymbol(self,texto,nivel = 0):
        self.__insertNumeringSymbol(self.__NUMSTYLES[self.ROMAN], nivel) 
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
        
    def insertAlphabeticSymbol(self,texto, nivel = 0):
        self.__insertNumeringSymbol(self.__NUMSTYLES[self.ALPHA], nivel)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def insertTableData(self,tableName,row,col,texto):
        table = self.document.TextTables.getByName(tableName)
        table.getCellByPosition(col,row).setString(texto)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def insertDinamicTable(self,nombre):
        table = self.document.createInstance("com.sun.star.text.TextTable")
        table.initialize(1,1)
        table.setPropertyValue("BackTransparent",False)
        table.setName(nombre)
        self.text.insertTextContent(self.cursor,table,0)
        rows = table.Rows
        row = rows.getByIndex(0);
        row.setPropertyValue("BackTransparent", False)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
    
    def insertTable(self,nombre,filas,columnas,data):
        table = self.document.createInstance("com.sun.star.text.TextTable")
        table.initialize(filas, columnas)
        h = table.getPropertySetInfo()
        table.setPropertyValue("BackTransparent",False)
        table.setPropertyValue("BackColor",13421823)
        
        table.setName(nombre.replace(" ","_"))

        self.text.insertTextContent(self.cursor,table,0)
        rows = table.Rows
        row = rows.getByIndex(0)
        row.setPropertyValue("BackTransparent",False)
        row.setPropertyValue("BackColor",6710932)
        
        fila = 0
        col = 0
        for element in data:
            if col == columnas:
                col = 0
                fila = fila + 1
            table.getCellByPosition(col,fila).setString(element)
            col = col + 1
        
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK, 0)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------                    

    def deleteNumbering(self):
        self.text.insertControlCharacter(self.cursor, PARAGRAPH_BREAK,0)
        self.cursor.setPropertyValue("NumberingRules", None)
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            

    def environment(self,env):
        self.env = env
        
#---------------------------------------------------------------------------------------------------------------------------------------------------            
        
    def saveContent(self,formato):
        p = os.path.join(tempfile.gettempdir(), 'tracExportCache')
        if not os.path.exists(p):
            os.mkdir(p)

        fd = os.path.split(tempfile.mktemp(suffix=formato, dir='tracExportCache'))[1]
        
        if (formato == '.pdf'):            
            filterName = "writer_pdf_Export"
            extension  = "pdf"
            outProps = (
                PropertyValue( "FilterName" , 0, filterName , 0 ),
            )
            pathDocumento = os.path.join(p, fd)
            self.document.storeToURL('file://' + pathDocumento,outProps)
        elif (formato == '.doc'):
            filterName = "MS Word 97"
            extension = "doc"
            outProps = (
                PropertyValue("FilterName", 0, filterName, 0),
            )
            pathDocumento = os.path.join(p, fd)
            self.document.storeToURL('file://' + pathDocumento,outProps)
        else:
            pathDocumento = os.path.join(p, fd)
            self.document.storeToURL('file://' + pathDocumento,()) 
        self.document.close(True)          
        return pathDocumento