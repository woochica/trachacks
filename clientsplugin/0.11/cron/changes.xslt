<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE xsl:stylesheet [ <!ENTITY nbsp "&#160;"> ]>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0">
  
  <xsl:output method="html" indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
  <xsl:decimal-format name="GBP" decimal-separator="." grouping-separator=","/>
  
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
    <xsl:element name="html">
      <head>
        <title>Ticket Summary for <xsl:value-of select="/clientsplugin/client/name"/></title>
        <style type="text/css">
        body {
          background: #f3f3f3;
        }
        .ticket {
          background: #eee;
          padding: 0;
          margin: 2px;
          margin-bottom: 20px;
          border: 1px solid #222;
        }
        .id {
          float: left;
          margin: 0;
          padding: 5px;
          text-align: center;
          background: #222;
          color: #eee;
          width: 5em;
          font-weight: bold;
        }
        .summary {
          float: left;
          margin: 0 0 0 1em;
          padding: 5px;
          font-style: italic;
        }
        .description {
          clear: both;
          margin: 2em;
          margin-top: 3em;
          padding: 1em;
          border: 1px solid #222;
          background: #fff;
        }
        .due {
          clear: both;
          float: right;
          margin: 4px;
          padding: 0;
          font-variant: small-caps;
        }
        .due:before {
          content: "Expected Delivery Date: ";
        }
        .fin {
          clear: both;
        }
        </style>
      </head>
      <body>
        <h1>Ticket Summary for <xsl:value-of select="/clientsplugin/client/name"/></h1>
        <xsl:choose>
          <xsl:when test="/clientsplugin/changes/ticket">
            <xsl:for-each select="/clientsplugin/changes/ticket">
              <div class="ticket">
                <div class="id">#<xsl:value-of select="id"/></div>
                <div class="summary"><xsl:value-of select="summary"/></div>
                <div class="description">
                  <xsl:if test="description!=''">
                    <xsl:copy-of select="description"/>
                  </xsl:if>
                  <xsl:for-each select="changelog/detail">
                    <hr />
                    <xsl:copy-of select="."/>
                  </xsl:for-each>
                </div>
                <div class="due"><xsl:value-of select="due"/></div>
                <div class="fin"></div>
              </div>
            </xsl:for-each>
          </xsl:when>
          <xsl:otherwise>
            <p>You do not currently have any active tickets</p>
          </xsl:otherwise>
        </xsl:choose>
      </body>
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>
