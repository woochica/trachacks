<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE xsl:stylesheet [ <!ENTITY nbsp "&#160;"> ]>
<xsl:stylesheet
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  version="1.0">
  
  <xsl:output method="xml" indent="yes" encoding="UTF-8" omit-xml-declaration="yes"/>
  
  <!-- Match the root of the XML render the three views -->
  <xsl:template match="/">
    <entry>
      <body>
        &lt;table class=&quot;tracTicketSummary&quot; style=&quot;border-collapse:collapse; width:100%&quot;&gt;
          &lt;tr&gt;
          &lt;th&gt;&lt;/th&gt;
          &lt;th style=&quot;text-align:center;&quot; &gt;Estimated Hours&lt;/th&gt;
          &lt;th style=&quot;text-align:center;&quot; &gt;Hours Worked&lt;/th&gt;
          &lt;th style=&quot;text-align:center;&quot; &gt;Release&lt;/th&gt;
          &lt;th style=&quot;text-align:center;&quot; &gt;Status&lt;/th&gt;
          &lt;/tr&gt;
          <xsl:for-each select="/clientsplugin/summary/ticket">
            &lt;tr style=&quot;<xsl:if test="position() mod 2 = 0">background-color: #B6E3EC</xsl:if>&quot;&gt;
              &lt;td style=&quot;padding:5px;&quot;&gt;          
              <xsl:value-of select="./summary" />
              &lt;/td&gt;                        
              &lt;td style=&quot;text-align:center;padding:5px;&quot; &gt;          
              <xsl:value-of select="./estimatedhours" />
              &lt;/td&gt;              
              &lt;td style=&quot;text-align:center;padding: 5px;&quot; &gt;          
              <xsl:value-of select="./totalhours" />
              &lt;/td&gt; 
              &lt;td style=&quot;text-align:center;padding: 5px;&quot; &gt;          
              <xsl:value-of select="./milestone" />
              &lt;/td&gt;   
              &lt;td style=&quot;text-align:center;padding: 5px;&quot; &gt;          
              <xsl:value-of select="./status" />
              &lt;/td&gt;   
            &lt;/tr&gt;
          </xsl:for-each>
        &lt;/table&gt;        
      </body>
    </entry>
  </xsl:template>
</xsl:stylesheet>