��          �               �      �      �                %  
   *     5     <     B     G     P     f  �  v               0  	   C     M  
   U     `     g     t  
   x  �  �     >   Add a new row Budget Estimation Budget in hours Comment Cost Estimation Person State Type in hours report_description_90 report_title_90 Project-Id-Version: XMail 0.0.x
Report-Msgid-Bugs-To: EMAIL@ADDRESS
POT-Creation-Date: 2010-05-04 01:38+0200
PO-Revision-Date: 2011-03-18 12:11+0100
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language-Team: de_DE <trac-dev@googlegroups.com>
Plural-Forms: nplurals=2; plural=(n != 1)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 0.9.6
 Neue Zeile hinzufügen Aufgabenverteilung Aufwand in Stunden Kommentar Aufwand Schätzung Person Status in %% Typ in Stunden {{{#!th width='50%'
'''Beschreibung'''
}}}
{{{#!th width='50%'
'''Beispiel'''
}}}
|----------------
{{{#!td width='50%'
Alle Tickets mit Aufwandsschätzungen werden gefiltert nach Meilenstein, Komponente und Ersteller 
(standardmäßig werden für Meilenstein und Komponente die Werte '%' (alle) verwendet; als Ersteller (OWNER) der angemeldete Benutzer). 
Die Ergebnisse werden nach Meilensteinen sortiert. Tickets mit höheren Aufwand als Schätzung werden orange hinterlegt.

MILESTONE, COMPONENT and OWNER können mit Platzhaltern  (%) gefiltert werden.Variable OWNER sucht auch in den Aufwandsschätzungen.
}}}
{{{#!td width='50%'
{{{
COMPONENT: %
MILESTONE: 4.%
OWNER:     unassigned
}}}
}}}
 [budget] Alle Tickets 