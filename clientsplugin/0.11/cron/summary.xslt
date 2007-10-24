<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE xsl:stylesheet [ <!ENTITY nbsp "&#160;"> ]>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:dt="http://xsltsl.org/date-time"
  xmlns:str="http://xsltsl.org/string"
  xmlns:hack='http://hack.com/hack'
  xsl:exclude-result-prefixes='hack'
  version="1.0">

  <xsl:import href="xsltsl/stdlib.xsl"/>
  <xsl:output method="xml" indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
  <xsl:decimal-format name="GBP" decimal-separator="." grouping-separator=","/>
  
  <!-- Disabled until http://bugzilla.gnome.org/show_bug.cgi?id=489854 is fixed
  <xsl:param name="view" /> -->
  <xsl:variable name="view" select="hack:hack()"/>
  
  <!-- Match the root of the XML render the three views -->
  <xsl:template match="/">
    <xsl:choose>
      <xsl:when test="$view='html'">
        <!-- Should return HTML as you see fit -->
        <xsl:call-template name="html"/>
      </xsl:when>
      <xsl:when test="$view='images'">
        <!--
        Should return a list of images to embed in the following format:
        
        <images>
          <img id="myimage" src="/local/path/to/image"/>
        </images>
        
        Where "myimage" is references in your HTML image as <img src="cid:myimage" />
        -->
        <xsl:call-template name="images"/>
      </xsl:when>
      <xsl:otherwise>
        <!-- The plain text portion of the email -->
        <xsl:call-template name="plain"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  
  <!-- Simple (cop-out) implementation of a plain text message -->
  <xsl:template name="plain">
    <xsl:text>
This message contains HTML content for a rich display.

Please enable the HTML view or use an HTML compatible email client.
    </xsl:text>
  </xsl:template>
  
  <!-- This HTML version does not contain any images -->
  <xsl:template name="images"/>
  
  <xsl:template name="html">
    <!-- The root element needs to be created with xsl:element to prevent namespaces sneaking in. -->
    <xsl:element name="div">
      <xsl:for-each select="accommodation">
    
      </xsl:for-each>
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>