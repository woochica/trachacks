"""
 tracbib/helper.py

 Copyright (C) 2011 Roman Fenkhuber

 Tracbib is a trac plugin hosted on trac-hacks.org. It brings support for
 citing from bibtex files in the Trac wiki from different sources.

 This File mostly bases on the version offered by Vidar Bronken Gundersen 
 and Sara Sprenkle. See the copyright notices below. It provides helper
 functions for their bibtexparer.
 
 tracbib is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
 (at your option) any later version.
 
 tracbib is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 
 You should have received a copy of the GNU General Public License
 along with tracbib.  If not, see <http://www.gnu.org/licenses/>.
"""

"""
  Yet another Parser for bibtex files
  Usage: python bibtexparse.py bibfile.bib 
         output will be bibfile.xml

  Reuse approved as long as this notification is kept.
  Licence: GPL.

         
  This is a version cannibalized from bibtexml.py by Vidar Bronken Gundersen 
  and modified by Sara Sprenkle (See Original copyright note below.)


  1. The main change is that we parse the bibtex file and put the list in
     a python dictionary, making very easy any post-processing. For an example
     look at the main routine, where author are selected.

     It can also be imported as a module from a script for a more complex 
     processing or conversion

  2. Conversion to xml is simply a write of a python object (dictionary)

  3. Added handling of accents and some other latex tags (incomplete) through a translation table
  4. Handling of a few LaTeX math constructions.

  5. There were some small bugs, when one of the fields (I found them in url or abstract) 
     have an equal sign "=" in the data.
  6. Entries like:
     author = {{Author1}, R.~O. and {Author2}, J. and {Author3}, P.},
     were not correcly handled. 
  Points 3 and 4 arised when bibtex entries were downloaded from 
     http://adsabs.harvard.edu/physics_service.html

  7. Added a tag <bibxml:authors>  around all <bibxml:author> and the same for


  ----------------------------------------------------------------------
  ----------------------------------------------------------------------
  ----------------------------------------------------------------------
  Original copyright notice
  ----------------------------------------------------------------------
  (c)2002-06-23 Vidar Bronken Gundersen
  http://bibtexml.sf.net/
  Reuse approved as long as this notification is kept.
  Licence: GPL.

  Contributions/thanks to:
  Egon Willighagen, http://sf.net/projects/jreferences/
  Richard Mahoney (for providing a test case)

  Editted by Sara Sprenkle to be more robust and handle more bibtex features.  (c) 2003-01-15
  1.  Changed bibtex: tags to bibxml: tags.
  2.  Use xmlns:bibxml="http://bibtexml.sf.net/"
  3.  Allow spaces between @type and first {
  4.  "author" fields with multiple authors split by " and "
      are put in separate xml "bibxml:author" tags.
  5.  Option for Titles: words are capitalized
      only if first letter in title or capitalized inside braces
  6.  Removes braces from within field values
  7.  Ignores comments in bibtex file (including @comment{ or % )
  8.  Replaces some special latex tags, e.g., replaces ~ with '&#160;'
  9.  Handles bibtex @string abbreviations
        --> includes bibtex's default abbreviations for months
        --> does concatenation of abbr # " more " and " more " # abbr
  10. Handles @type( ... ) or @type{ ... }
  11. The keywords field is split on , or ; and put into separate xml
      "bibxml:keywords" tags
  12. Ignores @preamble

  Known Limitations
  1.  Does not transform Latex encoding like math mode and special latex symbols.
  2.  Does not parse author fields into first and last names.
      E.g., It does not do anything special to an author whose name is in the form LAST_NAME, FIRST_NAME
      In "author" tag, will show up as <bibxml:author>LAST_NAME, FIRST_NAME</bibxml:author>
  3.  Does not handle "crossref" fields other than to print <bibxml:crossref>...</bibxml:crossref>
  4.  Does not inform user of the input's format errors.  You just won't be able to
      transform the file later with XSL

  You will have to manually edit the XML output if you need to handle
  these (and unknown) limitations.

  ----------------------------------------------------------------------
"""




import re
import string

def_strings = [
  ('jan', 'January'),
  ('feb', 'February'),
  ('mar', 'March'),
  ('apr', 'April'),
  ('may', 'May'),
  ('jun', 'June'),
  ('jul', 'July'),
  ('aug', 'August'),
  ('sep', 'September'),
  ('oct',  'October'),
  ('nov', 'November'),
  ('dec', 'December'),
  ]


xml_tags= [  # xml/html entities
  ('&', '&amp;'),
  ('<', '&lt;'),
  ('>', '&gt;'),
  ('---', '&#8212;'),
  ('--', '&#8211;'),
]

accent_tags= [  # Accents and other latin symbols
  (r'\"a', "&#228;"),
  (r"\`a", "&#224;"),
  (r"\'a", "&#225;"),
  (r"\~a", "&#227;"),
  (r"\^a", "&#226;"),
  (r'\"e', "&#235;"),
  (r"\`e", "&#232;"),
  (r"\'e", "&#233;"),
  (r"\^e", "&#234;"),
  (r'\"\i', "&#239;"),
  (r"\`\i", "&#236;"),
  (r"\'\i", "&#237;"),
  (r"\^\i", "&#238;"),
  (r'\"i', "&#239;"),
  (r"\`i", "&#236;"),
  (r"\'i", "&#237;"),
  (r"\^i", "&#238;"),
  (r'\"o', "&#246;"),
  (r"\`o", "&#242;"),
  (r"\'o", "&#243;"),
  (r"\~o", "&#245;"),
  (r"\^o", "&#244;"),
  (r'\"u', "&#252;"),
  (r"\`", "&#249;"),
  (r"\'", "&#250;"),
  (r"\^", "&#251;"),
  (r'\"A', "&#196;"),
  (r"\`A", "&#192;"),
  (r"\'A", "&#193;"),
  (r"\~A", "&#195;"),
  (r"\^A", "&#194;"),
  (r'\"E', "&#203;"),
  (r"\`E", "&#200;"),
  (r"\'E", "&#201;"),
  (r"\^E", "&#202;"),
  (r'\"I', "&#207;"),
  (r"\`I", "&#204;"),
  (r"\'I", "&#205;"),
  (r"\^I", "&#206;"),
  (r'\"O', "&#214;"),
  (r"\`O", "&#210;"),
  (r"\'O", "&#211;"),
  (r"\~O", "&#213;"),
  (r"\^O", "&#212;"),
  (r'\"U', "&#220;"),
  (r"\`", "&#217;"),
  (r"\'", "&#218;"),
  (r"\^", "&#219;"),
  (r"\~n", "&#241;"),
  (r"\~N", "&#209;"),
  (r"\c c", "&#231;")
  ,(r"\c C", "&#199;")
  ,(r"\circ", "o")
  ]

other_tags=[
  ('([^\\\\])~','\g<1> ') # Remove tilde (used in LaTeX for spaces)
  ,(r'\[^ {]+{(.+)}','\g<1> ') # Remove other commands
]

def replace_tags(strng, what='All'):
  ww=what.lower()
  if ww == 'all' or ww == 'xml':
    # encode character entities
    for i,o in xml_tags:
      strng = string.replace(strng, i, o )

  if ww == 'all' or ww == 'accents':
    # latex-specific character replacements
    for i,o in accent_tags:
      strng = string.replace(strng, i, o )

  if ww == 'all' or ww == 'other':
    # Other LaTeX tags, handled by regexps
    for i,o in other_tags:
      strng= re.sub(i,o,strng)

  return strng


def filter_bib(biblist, filter_options):
  delete=[]
  for ident,item in biblist.iteritems():
    valid = True
    for k,v,cond in filter_options :
      valid= item.has_key(k) and valid
      if valid:
        if type(item[k]) == list:
          data=''
          for d in item[k]:
            data += d.lower() + ', '
        else:
          data= item[k].lower()

        valid = valid and ((v in data) == cond)
        if not valid:
          delete.append(ident)
          break
      else:
        delete.append(ident)
        break

  # Collect all matching and return them
  bib={}
  for ident in biblist.keys():
    if ident not in delete:
      bib[ident]= biblist[ident].copy()

  return bib


def match_pair(expr, pair=(r'{',r'}')):
  """ 
  Find the outermost pair enclosing a given expresion
  
  pair is a 2-tuple containing (begin, end) where both may be characters or strings
  for instance:
    pair= ('[',']')  or
    pair= ('if','end if') or
    pair= ('<div>','</div>') or ...
    
    """

  beg=pair[0]
  fin=pair[1]


  #   find first opening
  start= expr.find(beg)
  count= 0

  if beg == fin:
    end= expr.find(fin,start+1)
    return start,end

  p= re.compile('('+beg +'|' + fin+')', re.M)
  ps= re.compile(beg, re.M)

  iterator = p.finditer(expr)

  for match in iterator:
    if ps.match(match.group()):
      count+= 1
    else:
      count+= -1
        
    if count == 0:
      return start, match.end()

  return None

def remove_braces(value):
    return value.replace("{","").replace("}","")



