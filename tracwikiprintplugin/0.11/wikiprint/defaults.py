"""
Author: Alvaro Iradier <alvaro.iradier@polartech.es>
"""

#Default CSS to use for xhtml2pdf
CSS = """
html {
    font-family: Helvetica; 
    font-size: 10px; 
    font-weight: normal;
    color: #000000; 
    background-color: transparent;
    margin: 0; 
    padding: 0;
    line-height: 150%;
    border: 1px none;
    display: inline;
    width: auto;
    height: auto;
    white-space: normal;
}

b, 
strong { 
    font-weight: bold; 
}

i, 
em { 
    font-style: italic; 
}

u, .underline {
    text-decoration: underline;
}

s,
strike {
    text-decoration: line-through;
}

a {
    text-decoration: underline;
    color: blue;
}

ins {
    color: green;
    text-decoration: underline;
}

del {
    color: red;
    text-decoration: line-through;
}

pre,
code,
kbd,
samp,
tt {
    font-family: "Courier New";
}

h1,
h2,
h3,
h4,
h5,
h6 {
    font-weight:bold;
    /* xhtml2 specific, include headers in outline */
    -pdf-outline: true;    
    -pdf-outline-open: false;
}

h1 {
    /*18px via YUI Fonts CSS foundation*/
    font-size:138.5%; 
    -pdf-outline-level: 0;
}

pdftoc.pdftoclevel0 {
    font-weight: bold;    
}

h2 {
    /*16px via YUI Fonts CSS foundation*/
    font-size:123.1%;
    -pdf-outline-level: 1;
}

h3 {
    /*14px via YUI Fonts CSS foundation*/
    font-size:108%;
    -pdf-outline-level: 2;
}

h4 {
    -pdf-outline-level: 3;
}

h5 {
    -pdf-outline-level: 4;
}

h6 {
    -pdf-outline-level: 5;
}

/* xhtml2 specific, margin for outline items */
pdftoc.pdftoclevel1 {
   margin-left: 1.0em;
   font-weight: normal;
}
pdftoc.pdftoclevel2 {
   margin-left: 2.0em;
}
pdftoc.pdftoclevel3 {
   margin-left: 3.0em;
}
pdftoc.pdftoclevel4 {
   margin-left: 4.0em;
}
pdftoc.pdftoclevel5 {
   margin-left: 5.0em;
}


h1,
h2,
h3,
h4,
h5,
h6,
p,
pre,
hr {
    margin:1em 0;
}

address,
blockquote,
body,
center,
dl,
dir,
div,
fieldset,
form,
h1,
h2,
h3,
h4,
h5,
h6,
hr,
isindex,
menu,
noframes,
noscript,
ol,
ul,
p,
pre,
table,
th,
tr,
td,
dd,
dt,
pdftoc {
    display: block;
}

table {
     -pdf-keep-in-frame-mode: shrink;
}

tr,
th,
td {
    vertical-align: middle;
    width: auto;
    padding: 2px;
}

th {
    text-align: center;
    font-weight: bold;
}

center {
    text-align: center;
}

big {
    font-size: 125%;
}

small {
    font-size: 75%;
}


li {
    /* Ugly fix for PISA? It won't line break instead... but this breaks display in Printable HTML */
    display: block;
}


ul {
    margin-left: 1.5em;
    list-style-type: disc;
}

ul ul {
    margin-left: 1.5em;
    /* Looks like stly is ignored in PISA */
    list-style-type: circle;
}

ul ul ul {
    margin-left: 1.5em;
    /* Looks like stly is ignored in PISA */
    list-style-type: square;
}


ol {
    list-style-type: decimal;
    margin-left: 1.5em;
}

ol.loweralpha {
    margin-left: 1.5em;
    /* Looks like stly is ignored in PISA */
    list-style-type: lower-latin;
}


ol.lowerroman, ol {
    margin-left: 1.5em;
    /* Looks like stly is ignored in PISA */
    list-style-type: lower-roman;
}

dd {
    margin-left: 2.0em;
}

pre {
    white-space: pre;
}

blockquote {
    margin-left: 1.5em;
    margin-right: 1.5em;
}

blockquote.citation {
    margin-left: 1.5em;
    margin-right: 1.5em;
    border-left-style: solid;
    border-left-color: #a0a0a0;
    border-left-width: 2px;
    padding-left: 1em;
}


/* Add a border on code bocks */
div.code pre, pre.wiki {
    border: 1px solid black;
    padding: 5px;
}

/* Hide border for images */
img {
    border: 0px;
}

/* Add a border on wiki tables */
table.wiki {
    border: 1px solid gray;
}

"""

#This CSS is included when creating Books. Default @page style is not specified,
#so front page has no header or footer. After front_page, 'standard' template
#must be selected using <div><pdf:nexttemplate name="standard"/><pdf:nextpage /></div>
BOOK_EXTRA_CSS = """
/* Set options when using 'standard' template */
@page standard {
    margin: 1.5cm;
    margin-top: 2.5cm;
    margin-bottom: 2.5cm;
    
    @frame header {
        /* -pdf-frame-border: 1; */
        -pdf-frame-content: headerContent;
        margin-left: 1.5cm;
        margin-right: 1.5cm;
        top: 1cm;
        height: 0.5cm;
    }
    
    @frame footer {
        /* -pdf-frame-border: 1; */
        -pdf-frame-content: footerContent;
        margin-left: 1.5cm;
        margin-right: 1.5cm;
        bottom: 1cm;
        height: 0.5cm;
    }

}
"""

#This CSS is included when creating PDF articles, not of book type
ARTICLE_EXTRA_CSS = """
/* Set default styles por all pages */ 
@page {
    margin: 1.5cm;
    margin-top: 2.5cm;
    margin-bottom: 2.5cm;
    
    /* Define a header frame. Frame contents will be taken from 'headerContent' element (<div>) */
    @frame header {
        /* -pdf-frame-border: 1; */
        -pdf-frame-content: headerContent;
        margin-left: 1.5cm;
        margin-right: 1.5cm;
        top: 1cm;
        height: 0.5cm;
    }
    
    /* Define a footer frame. Frame contents will be taken from 'footerContent' element (<div>) */
    @frame footer {
        /* -pdf-frame-border: 1; */
        -pdf-frame-content: footerContent;
        margin-left: 1.5cm;
        margin-right: 1.5cm;
        bottom: 1cm;
        height: 0.5cm;
    }

}
"""


# Example front page, just use plain HTML, without <html> </html> or <body> tags
FRONTPAGE = """
<!-- Use H1 style, but without including in outline (-pdf-outline: false) -->
<h1 style="-pdf-outline: false;">Wikiprint Book</h1>
<h2 style="-pdf-outline: false;">Title: #TITLE</h2>
<h2 style="-pdf-outline: false;">Subject: #SUBJECT</h2>
<h2 style="-pdf-outline: false;">Version: #VERSION</h2>
<h2 style="-pdf-outline: false;">Date: #DATE</h2>
<div><pdf:nexttemplate name="standard"/><pdf:nextpage /></div>
"""

EXTRA_CONTENT = """
<div id="headerContent" style="text-align: right;">
WikiPrint - from Polar Technologies
</div>
<div id="footerContent" style="text-align: center;">
<pdf:pagenumber/>
</div>
"""