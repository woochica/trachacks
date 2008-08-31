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
  fieldset.milestone {
    margin-top: 3em;
  }
  fieldset.ticket {
    margin-top: 2em;
    background: #eee;
  }
  .description {
    margin: 0.5em;
    padding: 0.5em;
    border: 1px solid #222;
    background: #fff;
  }
  .status {
    margin: 4px;
    padding: 0;
    font-variant: small-caps;
  }
  dl.milestone dt {
    float: left;
    margin-right: 0.5em;
    font-style: italic;
  }
  dl.milestone dt:after {
    content: ':';
  }
        </style>
      </head>
      <body>
        <h1>Ticket Summary for <xsl:value-of select="/clientsplugin/client/name"/></h1>
        <xsl:choose>
          <xsl:when test="/clientsplugin/summary/ticket">
            <xsl:for-each select="/clientsplugin/milestones/milestone">
              <xsl:sort select="duetimestamp" order="asscending"/>
              <xsl:variable name="ms" select="./name" />
              <xsl:if test="/clientsplugin/summary/ticket[milestone=$ms]">
                <fieldset class="milestone">
                  <legend class="milestone">
                    <xsl:text>Milestone: </xsl:text>
                    <xsl:value-of select="$ms" />
                  </legend>
                  <xsl:if test="./description!=''">
                    <div class="milestone description">
                      <xsl:value-of select="./description" />
                    </div>
                  </xsl:if>
                  <xsl:if test="./due">
                    <dl class="milestone">
                      <dt>Estimated delivery date</dt>
                      <dd><xsl:value-of select="./due" /></dd>
                      <xsl:if test="./completed">
                        <dt>Completed on</dt>
                        <dd><xsl:value-of select="./completed" /></dd>
                      </xsl:if>
                      <xsl:if test="./estimatedhours">
                        <dt>Total estimated development time</dt>
                        <dd><xsl:value-of select="./estimatedhours" /></dd>
                      </xsl:if>
                    </dl>
                  </xsl:if>
                  <xsl:for-each select="/clientsplugin/summary/ticket[milestone=$ms]">
                    <xsl:call-template name="print-ticket" />
                  </xsl:for-each>
                </fieldset>
              </xsl:if>
            </xsl:for-each>
            <xsl:variable name="ms" select="''" />
            <xsl:if test="/clientsplugin/summary/ticket[milestone=$ms]">
              <fieldset class="milestone">
                <legend class="milestone">
                  Tickets not allocated to specific milestones
                </legend>
                <div class="milestone description">
                  <p>The following tickets are not allocated to any specific milestone.</p>
                </div>
                <xsl:for-each select="/clientsplugin/summary/ticket[milestone=$ms]">
                  <xsl:call-template name="print-ticket" />
                </xsl:for-each>
              </fieldset>
            </xsl:if>
          </xsl:when>
          <xsl:otherwise>
            <p>You do not currently have any active tickets</p>
          </xsl:otherwise>
        </xsl:choose>
      </body>
    </xsl:element>
  </xsl:template>

  <xsl:template name="print-ticket">
    <fieldset class="ticket">
      <legend class="ticket">
        Ticket #<xsl:value-of select="id"/>: <xsl:value-of select="summary"/>
      </legend>
      <xsl:if test="description!=''">
        <div class="ticket description"><xsl:copy-of select="description"/></div>
      </xsl:if>
      <div class="status">Status: <xsl:value-of select="status"/></div>
      <xsl:if test="estimatedhours">
        <div class="estimate">Estimated development time: <xsl:value-of select="estimatedhours"/></div>
      </xsl:if>
      <!-- <div class="due"><xsl:value-of select="due"/></div> -->
    </fieldset>
  </xsl:template>
</xsl:stylesheet>
