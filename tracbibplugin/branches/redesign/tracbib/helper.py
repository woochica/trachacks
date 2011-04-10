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




