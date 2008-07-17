<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="UTF-8" indent="yes"/>
	
<!-- Variablen -->
  <xsl:variable name="bezeichner_bildbeschriftung">Abbildung</xsl:variable>
  <xsl:variable name="bezeichner_tabellenbeschriftung">Tabelle</xsl:variable>
  <xsl:variable name="quelle_tabellenbeschriftung">Title</xsl:variable>
	
	<!-- Einstiegspunkt -->
	<xsl:template match="/">
		<html>
			<head>
				<meta http-equiv="Content-Type" content="text/html; charset=windows-1252"/>
				<meta name="Generator" content="Microsoft Word 11 (filtered)"/>
				<xsl:text disable-output-escaping="yes"><![CDATA[<style>
	<!--
	p.MsoNormal, li.MsoNormal, div.MsoNormal
	{margin:0cm;}
	-->
	</style>]]></xsl:text>
				
				
				
				

				<title></title>
			</head>
			<body>
				<!-- Beginn der eigentlichen Verarbeitung -->
				<!-- Wenn aus der gesamten Wiki-Seite extrahiert werden soll, dann muss die apply-templates-Anweisung folgende Eigenschaft beinhalten: select="//div[@id='content']"  -->
				<xsl:apply-templates />
			</body>
		</html>
	</xsl:template>


<!-- Überschriften -->
<xsl:template match="h1|h2|h3|h4|h5|h6|h7">
   <xsl:element name = "{name()}" >
		<a name="{@id}">
			<xsl:value-of select="normalize-space(text())"/>
		</a>	
   </xsl:element>
</xsl:template>

<!-- Formatierungen -->
<xsl:template match="strong|b|i|u">
   <xsl:element name = "{name()}" >
	   <!--<xsl:value-of select="normalize-space(text())"/>-->
	   	<xsl:apply-templates/>
   </xsl:element>
   <xsl:text> </xsl:text>
</xsl:template>

<!-- Bilder und Bildbeschriftungen -->
<xsl:template match="img">
	<img src="{@src}" alt="{@alt}"/>
	<p class="MsoCaption">
		<xsl:value-of select="$bezeichner_bildbeschriftung"/>
		<!-- Alles hier folgende ist Word-interner Code, der die Abbildungsnummer als Feld markiert -->
		<xsl:text disable-output-escaping="yes"><![CDATA[ <!--[if supportFields]><span style='mso-element:field-begin'></span><span style='mso-spacerun:yes'> </span>SEQ ]]></xsl:text>
		<xsl:value-of select="$bezeichner_bildbeschriftung"/>
		<xsl:text disable-output-escaping="yes"><![CDATA[ \* ARABIC <span style='mso-element:field-separator'></span><![endif]--><span style='mso-no-proof:yes'>]]></xsl:text>
		<xsl:number count="img"/>
		<xsl:text disable-output-escaping="yes"><![CDATA[</span><!--[if supportFields]><span style='mso-element:field-end'></span><![endif]-->: ]]></xsl:text>
		<!-- Bildbezeichnung, aus title-Tag lesen -->
		<xsl:value-of select="@title"/> 
	</p>
</xsl:template>

<!-- Tabellendefinition -->
<xsl:template match="table">
	<!-- Tabellenbeschriftung -->
		
		<xsl:if test="tbody/tr/td[substring-before(text()[1],':')=$quelle_tabellenbeschriftung] or tr/td[substring-before(text()[1],':')=$quelle_tabellenbeschriftung]">
		<p class="MsoCaption">
		<xsl:value-of select="$bezeichner_tabellenbeschriftung"/>
		<!-- Markierung als Feld -->
		<xsl:text disable-output-escaping="yes"><![CDATA[ <!--[if supportFields]><span style='mso-element:field-begin'></span><span style='mso-spacerun:yes'> </span>SEQ ]]></xsl:text>
		<xsl:value-of select="$bezeichner_tabellenbeschriftung"/>
		<xsl:text disable-output-escaping="yes"><![CDATA[ \* ARABIC <span style='mso-element:field-separator'></span><![endif]--><span style='mso-no-proof:yes'>]]></xsl:text>
		<xsl:number count="table"/>
		<xsl:text disable-output-escaping="yes"><![CDATA[</span><!--[if supportFields]><span style='mso-element:field-end'></span><![endif]-->: ]]></xsl:text>
		<!-- Bezeichnung -->
		<xsl:if test="tbody">
			<xsl:value-of select="substring-after(tbody/tr[1]/td[text()],':')"/>
		</xsl:if>
		<xsl:if test="tr">
			<xsl:value-of select="substring-after(tr[1]/td[text()],':')"/>
		</xsl:if>
			 
		</p>
	</xsl:if>
	<table>
		<xsl:apply-templates/>
	</table>
</xsl:template>

<!-- Tabellenzeilen -->
<xsl:template match="tr">
	<!-- Die Tabellenbeschriftung nicht nochmal als separate Tabellenzeile ausgeben -->
	<xsl:if test="td[substring-before(text()[1],':')!=$quelle_tabellenbeschriftung]">
		<tr>
			<xsl:apply-templates/>
		</tr>
	</xsl:if>
</xsl:template>

<!-- Tabellenspalten -->
<xsl:template match="td">
		<xsl:element name = "{name()}" >
		<xsl:apply-templates/>
			<!-- Leere Tabellenzellen mit einem Leerzeichen fuellen, damit sie dargestellt werden -->
		   <xsl:if test="not(string(.))">
		   &#160;
		   </xsl:if>
	   </xsl:element>
</xsl:template>

<!-- Absatz -->
<xsl:template match="p">
	<!-- MsoNormal bedeutet Formatvorlage "Standard" -->
	<p class="MsoNormal">
		<xsl:apply-templates/>
	</p>
</xsl:template>


<!-- Listen mit/ohne Nummerierung -->
<xsl:template match="ul|ol">
	<xsl:element name="{name()}">
		<xsl:apply-templates/>
	</xsl:element>
</xsl:template>

<!-- Listenelemente -->
<xsl:template match="li">
	<li class="MsoNormal">
		<xsl:apply-templates/>
	</li>
</xsl:template>


<!-- praeformatierter Text -->
<xsl:template match="pre|tt">
	<!-- WORKAROUND. Um den Urzustand herzustellen, in der folgenden Zeile tt durch {name()} ersetzen -->
	<xsl:element name="tt">
		<xsl:apply-templates/>
	</xsl:element>
</xsl:template>


<!-- blockquotes: Werden um die Ausgabe von IncludeMacros herum gelegt -->
<xsl:template match="blockquote">
	<!-- nichts tun, einfach ueberspringen -->
	<xsl:apply-templates/>
</xsl:template>


<!-- Links -->
<xsl:template match="a">
	<!-- Fuer interne Referenzen -->
	
	<xsl:if test="@class='wiki'">
		<!-- Erzeugung Link Word-Stil-->
		<!--<xsl:text disable-output-escaping="yes">
			<![CDATA[<span style='mso-field-code:" REF ]]>
		</xsl:text>
		<xsl:value-of select="substring-after(@href,'#')"/>
		<xsl:text disable-output-escaping="yes">
			<![CDATA[ \\h "'>]]>
		</xsl:text>
		<xsl:value-of select="text()"/>
		<xsl:text disable-output-escaping="yes">
				<![CDATA[</span>]]>
			</xsl:text>-->
			
		<!-- Erzeugung Link HTML-Stil -->
		<!--<a href="#{substring-after(@href,'#')}">
			<xsl:value-of select="text()"/>
		</a>-->
		<xsl:apply-templates/>	
	</xsl:if>
	
	<!-- Externe Links werden ausgeschrieben -->
	<xsl:if test="@class='ext-link'">
		<a href="{@href}">
			<xsl:value-of select="@href"/>
		</a>
	</xsl:if>
	
	<!-- Bilder sind zulaessig -->
	<xsl:if test="img">
		<xsl:apply-templates/>
	</xsl:if>
	
	
</xsl:template>	
	
</xsl:stylesheet>
