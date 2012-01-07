#!/usr/bin/env python
"""
 tracbib/bibtexparser.py

 Copyright (C) 2011 Roman Fenkhuber

 Tracbib is a trac plugin hosted on trac-hacks.org. It brings support for
 citing from bibtex files in the Trac wiki from different sources.


 This File mostly bases on the version offered by Vidar Bronken Gundersen 
 and Sara Sprenkle. See the copyright notices below. I just provide the function
 authors(data) which returns correctly split author strings, as described on 
 http://artis.imag.fr/~Xavier.Decoret/resources/xdkbibtex/bibtex_summary.html.

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

import sys
import string, re
from helper import match_pair, filter_bib, replace_tags, def_strings



# set of valid name characters
valid_name_chars = '[\w\-:]'

#
# define global regular expression variables
#
author_rex = re.compile('\s+and\s+')
rembraces_rex = re.compile('[{}]')
capitalize_rex = re.compile('({\w*})')
 
# used by bibtexkeywords(data)
keywords_rex = re.compile('[,;]')

# split on {, }, or " in verify_out_of_braces
delimiter_rex = re.compile('([{}"])',re.I)

field_rex = re.compile('\s*(\w*)\s*=\s*(.*)')
data_rex = re.compile('\s*(\w*)\s*=\s*([^,]*),?')


def handle_math(str):
  mathexp= [ (r'\^([^{]+){',r'<sup>\1</sup>')
            ,(r'\^{([^{]+)}',r'<sup>\1</sup>')
            ,(r'_([^{]+){',r'<sub>\1</sub>')
            ,(r'_{([^{]+)}',r'<sub>\1</sub>')
             ]
#   mathmarker= ('<math>','</math>')
  mathmarker= ('','')

  # Find math substrings
  p= re.compile(r'\$([^\$]+)\$')
  if p.search(str):
    ini=0
    linecontent=''
    iterator = p.finditer(str)
    for match in iterator:
      strmath= match.group()[1:-1]
      linecontent += str[ini:match.start()]
      for i,o in mathexp:
        strmath= re.sub(i,o,strmath)
      linecontent += mathmarker[0] + strmath + mathmarker[1]
      ini= match.end()
    linecontent += str[ini:]
  else:
    return str
  return linecontent

# return the string parameter without braces
#
def removebraces(str):
  return rembraces_rex.sub('',str) 

# fix author so that it creates multiple authors, 
# split by "and"
def bibtexauthor(data):
  bibtex = []
  author_list = author_rex.split(data)
  for author in author_list:
    author = author.strip()
    bibtex.append(removebraces(author).strip())
  return bibtex
	

# @return the bibtex for the title
# @param data --> title string
# braces are removed from title
def bibtextitle(data):
#   title = removebraces(data).strip()
  title = data.strip()
  return title


# @return the bibtex for the keyword
# keywords are assumed to be delimited by , or ;
def bibtexkeyword(data):
  bibtex = []
  keyword_list = keywords_rex.split(data)
  for keyword in keyword_list:
    keyword = keyword.strip()
    bibtex.append(removebraces(keyword).strip())
  return bibtex
   
# @return an array containing a dictionary for each author, split into 'first',
# 'last', 'von' and 'jr'
# @param data -> The 'authors' BibTex field
def authors(data):

    tokenized = []
    a = []
    sticky = (None,"")
    #determine the case of the word
    for i in re.finditer("(?P<caseless>[{\\\][^,\s]*)|(?P<separator>,)|(?P<word>[^\s,]+)|(?P<space>\s)",data):

        if not sticky[0] and re.search("{",i.group(0)) and not match_pair(i.group(0)): #brace not closed?
            if i.group("caseless"):
                sticky = ("caseless",i.group(0))
            elif i.group("word"):
                sticky = ("word",i.group(0))
            continue
        elif sticky[0] and not match_pair(sticky[1] + i.group(0)): 
            sticky = (sticky[0],sticky[1] + i.group(0))
            continue

        if sticky[0]:
            match = sticky[1] + i.group(0)
            token = sticky[0]
            sticky = (None,"")
        else:
            match=i.group(0)
            if i.group("caseless"):
                token = "caseless"
            if i.group("word"):
                token = "word"
            if i.group("separator"):
                a.append("separator") 
                token = "separator"
            if i.group("space"):
                token = "space"

        if token == "caseless":
            m = (0,0)
            caseless = match
            while m: 
                m= match_pair(caseless)
                if m and m[0] == 0: 
                    caseless = caseless[m[1]:]
                else:
                    break
            w = re.search("[\w]",caseless)
            if len(caseless) > 0 and w:
                if w.group(0).islower() or w.group(0).isdigit():
                    a.append(("lowercase",match))
                else:
                    a.append(("uppercase",match))
            else:
                a.append(("caseless",match)) 

        elif token == "word":
            if match == "and":
                tokenized.append(a)
                a = []
            elif match[0].islower() or match[0].isdigit():
                a.append(("lowercase",match))
            else:
                a.append(("uppercase",match))

    if sticky[0]:
        pass
        #raise Exception("Brace error!")


    tokenized.append(a)

    #determine the cite structure

    ret = []
    for author in tokenized:
        count = author.count("separator")
        a = { "first" : "", "von":"", "last":"", "jr" : ""  }

        #First von Last
        if count == 0:
            index = 0
            
            #first
            for index,word in enumerate(author):
                if index+1 < len(author) and word[0] != "lowercase":
                    a["first"] += " " + word[1]
                else:
                    author = author[index:]
                    break;

            #von
            caseless = []
            for index,word in enumerate(author):
                if index+1 < len(author) and word[0] != "uppercase":
                    if word[0] == "caseless":
                        caseless.append(word[1]) 
                    elif word[0] == "lowercase":
                        for w in caseless:
                            a["von"] += " " + w
                        caseless = []
                        a["von"] += " " + word[1]
                else:
                    author = author[index:]

            #last
            for word in caseless:
                a["last"] += " " + word
            for index,word in enumerate(author):
                a["last"] += " " + word[1]

        #von Last, [jr ,] First
        elif count > 0:

            #von
            upper = []
            for index,word in enumerate(author):
                if author[index+1] == "separator":
                    upper.append(word[1])
                    author = author[index+2:]
                    break
                if word == "uppercase":
                    upper.append(word)
                elif word != "separator":
                    for w in upper:
                        a["von"] += " " + w
                    upper= []
                    a["von"] += " " + word[1]
                else:
                    author = author[index+1:]
                    break;

            #last
            for word in upper:
                a["last"] += " " + word
            
            #jr
            if count > 1:
                for index,word in enumerate(author):
                    if word != "separator":
                        a["jr"] += " " + word[1]
                    else:
                        author = author[index+1:]
                        break

            #first
            for index,word in enumerate(author):
                if word != "separator":
                    a["first"] += " " + word[1]
                else:
                    a["first"] += ","

        elif count > 1:
            pass
        
        for k,v in a:
            a[k] = a[k].lstrip()
            if len(v) == 0:
                del a[k]
                continue

        ret.append(a)

    return ret

# data = title string
# @return the capitalized title (first letter is capitalized), rest are capitalized
# only if capitalized inside braces
def capitalizetitle(data):
  title_list = capitalize_rex.split(data)
  title = ''
  count = 0
  for phrase in title_list:
    #print phrase
    check = string.lstrip(phrase)

	 # keep phrase's capitalization the same
    if check.find('{') == 0:
      title = title + removebraces(phrase)
    else:
      # first word --> capitalize first letter (after spaces)
      if count == 0:
        title = title + check.capitalize() 
      else:
        title = title + phrase.lower() 
      count = count + 1

  return title



def no_outer_parens(filecontents):

  # do checking for open parens
  # will convert to braces
  paren_split = re.split('([(){}])',filecontents)

  open_paren_count = 0
  open_type = 0
  look_next = 0

  # rebuild filecontents
  filecontents = ''

  at_rex = re.compile('@\w*')

  for phrase in paren_split:
    if look_next == 1:
      if phrase == '(':
        phrase = '{'
        open_paren_count = open_paren_count + 1
      else:
        open_type = 0
      look_next = 0

    if phrase == '(':
      open_paren_count = open_paren_count + 1

    elif phrase == ')':
      open_paren_count = open_paren_count - 1
      if open_type == 1 and open_paren_count == 0:
        phrase = '}'
        open_type = 0

    elif at_rex.search( phrase ):
      open_type = 1
      look_next = 1

    filecontents = filecontents + phrase

  return filecontents
    
def get_fields(strng):
  f=strng.find('=')
  braces_rex=re.compile(r'\s*[{]')
  comilla_rex=re.compile(r'\s*["]')
  start=0
  fields=[]
  end= len(strng)

  # start holds the current position in the strng
  # f :  position of equal sign
  # s :  position of {, opening " or first line after the equal sign
  # e :  position of closing }, " or next comma
  while f != -1 and start < end:
    name= string.strip(strng[start:f]).lower()

    if name != '':
      ss= strng[ f+1 : ]
      if braces_rex.match(ss):
        s,e= match_pair(ss)
        data= ss[s+1:e-1].strip()
      elif comilla_rex.match(ss):
        s= string.find(ss,r'"')
        e= string.find(ss,r'"',s+1)
        data= ss[s+1:e].strip()
      else:
        s= 1
        e= ss.find(',')
        data= ss[s:e].strip()
      
      fields.append((name,data))

      #  There is trailing comma, we should take it out
      e=ss.find(',',e)+1

    start =  f+ e+2
    f= string.find(strng,'=',start)
  return fields

# make all whitespace into just one space
# format the bibtex file into a usable form.
# Bug: Does not handle "=" inside a field data (for instance in url)
def bibtexload(filecontents_source):
  space_rex = re.compile('\s+')
  pub_rex = re.compile('\W?@(\w*)\s*{')

  filecontents = []

  # remove trailing and excessive whitespace
  # ignore comments
  for line in filecontents_source:
    line = string.strip(line)
    line = space_rex.sub(' ', line)
    # ignore comments
    filecontents.append(' '+ line)
  filecontents = string.join(filecontents, '')

  # the file is in one long string
  filecontents = no_outer_parens(filecontents)
  # character encoding, reserved latex characters
  filecontents = re.sub('{\\\&}', '&', filecontents)
  filecontents = re.sub('\\\&', '&', filecontents)
  filecontents= filecontents.strip()
  # 
  # Find entries
  # 
  strings=[]
  preamble=[]
  comment=[]
  entries={}
  s=0
  e=0
  start= 0
  final=len(filecontents)-1

  while start < final:
    entry={}
    m= pub_rex.search(filecontents[start:])

    if m:
      start+= m.start()
      arttype = string.lower(pub_rex.sub('\g<1>',m.group()))

      d= match_pair(filecontents[start:])
      if d:
        s,e=d

      s+= start + 1
      e+= (start - 1)
      # current has the currently analyzed entry
      current= filecontents[s:e]

      if arttype == 'string':
        name, defin = string.split(current, "=")
        defin= defin.replace('"','').replace('  ',' ')
        strings.append((name.strip(),defin.strip()))
      elif arttype == 'comment' or arttype == 'preamble':
        pass
#         print '# '+ arttype
      else:
        p = re.match('([^,]+),', current )
        artid= p.group()[:-1]
        entry['type']=arttype
        entry['id']= artid
        current= current[p.end():]
        ff= get_fields(current)
        for n,d in ff:
          entry[n]=d
        
        entries[artid]= entry

      start= e
    else:
      return strings,entries

  return strings, entries



def bibtex_to_xml(bibtexlist,xmlhead=None, xmlfoot=None):
  if not xmlhead:
    xmlhead= """<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE bibxml:file SYSTEM "bibtexml-strict.dtd" >
<bibxml:file xmlns:bibxml="http://bibtexml.sf.net/">\n
"""
  if not xmlfoot:
    xmlfoot="\n</bibxml:file>"
  
  sp=1
  spd='  '
  blist=bibtexlist.copy()
  entry=''

  for Id,bib in blist.iteritems():


    tipo= bib['type']
    entry += sp*spd + '<bibxml:entry id="' + Id + '">\n' 
    sp+=1
    entry += sp*spd + '<bibxml:' + tipo + '>\n'
    del(bib['id'])
    del(bib['type'])
    sp+=1

    for k,e in bib.iteritems():
      if k == 'author' or k == 'keywords':
        entry += sp*spd + '<bibxml:' + k + 's>\n'
        if k == 'author':
          e= e.replace(',','')
          e=string.split(e,' and ')
        else:
          e=string.split(e,',')
        field= k
        sp+=1
        for val in e:
          v= replace_tags(val,'xml')
          v= handle_math(v)
          v= removebraces(v)
          v= replace_tags(v,'accents')
          v= replace_tags(v,'other')
          entry += sp*spd + '<bibxml:' + field + '>' + v + '</bibxml:' + field + '>\n'

        sp-=1
        entry += sp*spd + '</bibxml:' + k + 's>\n'
      else:
        v= replace_tags(e,'xml')
        v= handle_math(v)
        v= removebraces(v)
        v= replace_tags(v,'accents')
        v= replace_tags(v,'other')
        entry += sp*spd + '<bibxml:' + k + '>' + v + '</bibxml:' + k + '>\n'

    sp-=1
    entry += sp*spd + '</bibxml:' +  tipo + '>\n'
    sp-=1
    entry += sp*spd + '</bibxml:entry>\n\n'
  return xmlhead + entry + xmlfoot


def replace_abbrev(bibtexentry,strings):
  for k,v in bibtexentry.iteritems():
    for s,d in strings:
      if s in v:
        if s == v.strip() or  '#' in v:
          v= v.replace(s,d)
    if '#' in v:
      ss=v.split('#')
      v=string.join(ss,' ')
    bibtexentry[k]=v
      


def bibteximport(filepath):
  # Reads a BibTeX File and returns a dictionary where each entry is a dictionary
  #   
  try:
    fd = open(filepath, 'r')
    filecontents_source = fd.readlines()
    fd.close()
  except:
    print 'Could not open file:', filepath
    sys.exit(2)
  strings, outdata = bibtexload(filecontents_source)
  
  for k,bib in outdata.iteritems():
    replace_abbrev(bib, def_strings)
    replace_abbrev(bib,strings)

  return outdata


def filehandler(filepath):
  outdata= bibteximport(filepath)
  
  xmldata = bibtex_to_xml(outdata)
  return len(outdata.keys()),xmldata


# main program
def main():

  if sys.argv[1:]:
    filepath = sys.argv[1]
  else:
    print "No input file"
    print "USAGE:  "+sys.argv[0]+ " FILE.bib\n\n  It will output the XML file: FILE.xml"
      
    sys.exit(2)


  nentries, xmldata= filehandler(filepath)
  outfile= filepath[:filepath.rfind('.')]+'.xml'
  mensaje='Written '+ str(nentries) + ' entries to ' + outfile + '\n'
  sys.stderr.write(mensaje)
  fo= open(outfile,'w')
  fo.write(xmldata)
  fo.close()


if __name__ == "__main__": main()


# end python script
