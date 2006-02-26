# -*- coding: iso8859-1 -*-
# TinyMCE Wiki plugin sub module
#

import os
import re
import htmlentitydefs


#from trac.core import *
from StringIO import StringIO

# for Prosesser
from HTMLParser import HTMLParser
from trac.wiki.api import  WikiSystem# 
from trac.wiki.formatter import Formatter,WikiProcessor,OneLinerFormatter,wiki_to_html,wiki_to_oneliner
from trac.util import escape,unescape


class WikiToEditorHtmlFormatter(Formatter):
    """
    This is the formatter which convert wiki to trachtml.(and wrap wiki discription )
    layout discripttion -> html
    [[BR]]              -> <br />
    definition          -> <p>word</p><blockquote>discription</blockquote>
    escaping links '!'  -> <span class="tmtrac_cancel">discription </span>
    macro               -> <span class="tmtrac">macro discription </span>
    traclink            -> <span class="tmtrac">traclink discription </span>
    wikiprocesser       -> <pre class="tmtrac">processer dicsription</pre> (without htmltag. and doesn't execute processer.)
    """
    
    flavor = 'wiki2trachtml'
    
    # Override a few formatters to disable some wiki syntax 
    #def _list_formatter(self, match, fullmatch): return match
    #def _definition_formatter(self, match, fullmatch): return match
    
    #def _bolditalic_formatter(self, match, fullmatch): return match
    def _shref_formatter(self, match, fullmatch):
        return self.addTmtracStyle(match+' ') #add tmtrac style
    def _lhref_formatter(self, match, fullmatch):
        return self.addTmtracStyle(match+' ') #add tmtrac style
    def _make_link(self, ns, target, match, label): return match
    def _make_ext_link(self, url, text, title=''): return match
    def _make_relative_link(self, url, text): return match
    #def _bold_formatter(self, match, fullmatch): return match
    #def _italic_formatter(self, match, fullmatch): return match
    #def _underline_formatter(self, match, fullmatch): return match
    #def _strike_formatter(self, match, fullmatch): return match
    #def _subscript_formatter(self, match, fullmatch): return match
    #def _superscript_formatter(self, match, fullmatch): return match
    #def _inlinecode_formatter(self, match, fullmatch): return match
    #def _inlinecode2_formatter(self, match, fullmatch): return match
    #def _htmlescapeentity_formatter(self, match, fullmatch): return match
    def _macro_formatter(self, match, fullmatch):
        name = fullmatch.group('macroname')
        if name in ['br', 'BR']:
            return '<br />'
        elif name in ['html']: 
            args = fullmatch.group('macroargs')
            args = unescape(args)
            try:
                macro = WikiProcessor(self.env, name)
                return macro.process(self.req, args, 1)
            except Exception, e:
                self.env.log.error('Macro %s(%s) failed' % (name, args),
                                   exc_info=True)
                return system_message('Error: Macro %s(%s) failed' % (name, args), e)

            return match
        return self.addTmtracStyle(match)

    def _heading_formatter(self, match, fullmatch):
        match = match.strip()
        self.close_table()
        self.close_paragraph()
        self.close_indentation()
        self.close_list()
        self.close_def_list()

        depth = min(len(fullmatch.group('hdepth')), 5)
        heading = match[depth + 1:len(match) - depth - 1]

        text = unescape(heading)
        sans_markup = re.sub(r'</?\w+(?: .*?)?>', '', text)

        anchor = self._anchor_re.sub('', sans_markup.decode('utf-8'))
        if not anchor or not anchor[0].isalpha():
            # an ID must start with a letter in HTML
            anchor = 'a' + anchor
        i = 1
        anchor = anchor_base = anchor.encode('utf-8')
        while anchor in self._anchors:
            anchor = anchor_base + str(i)
            i += 1
        self._anchors.append(anchor)
        self.out.write('<h%d id="%s">%s</h%d>' % (depth, anchor, text, depth))
    #def _indent_formatter(self, match, fullmatch): return match
    #def _last_table_cell_formatter(self, match, fullmatch): return match
    #def _table_cell_formatter(self, match, fullmatch): return match

    def _definition_formatter(self, match, fullmatch):
        tmp = self.in_def_list and '</blockquote>' or ''
        tmp += '<p>%s</p><blockquote>' % wiki_to_oneliner(match[1:-2], self.env,
                                                    self.db)
        self.in_def_list = True
        return tmp

    def close_def_list(self):
        if self.in_def_list:
            self.out.write('</blockquote>')
        self.in_def_list = False


    def open_paragraph(self):
        if not self.paragraph_open:
            self.out.write('<p>' )
            self.paragraph_open = 1

    def close_paragraph(self):
        if self.paragraph_open:
            while self._open_tags != []:
                self.out.write(self._open_tags.pop()[1])
            self.out.write('</p>' )
            self.paragraph_open = 0



    def replace(self, fullmatch):
        wiki = WikiSystem(self.env)        
        for itype, match in fullmatch.groupdict().items():
            if match and not itype in wiki.helper_patterns:
                # Check for preceding escape character '!'
                if match[0] == '!':
                    return self.addTmtracCancelStyle(match ) #add tmtrac_cancel style
                if itype in wiki.external_handlers:
                    return self.addTmtracStyle(match ) #add tmtrac style
                    #return wiki.external_handlers[itype](self, match, fullmatch)
                else:
                    return getattr(self, '_' + itype + '_formatter')(match, fullmatch)

    def handle_code_block(self, line):
        if line.strip() == '{{{':
            self.in_code_block += 1
            if self.in_code_block == 1:
                self.code_text = ''
            else:
                self.code_text += line + os.linesep
        elif line.strip() == '}}}':
            self.in_code_block -= 1
            if self.in_code_block == 0 :
                self.close_paragraph()
                self.close_table()
                self.out.write('<pre class="tmtrac">' + escape(self.code_text) + '</pre>\n')
            else:
                self.code_text += line + os.linesep
        else:
            self.code_text += line + os.linesep


    def addTmtracStyle(self,text):
        if text == None:
            return None
        else:
            return '<span class="tmtrac">'+text+'</span>'

    def addTmtracCancelStyle(self,text):
        if text == None:
            return None
        else:
            return '<span class="tmtrac_cancel">'+text+'</span>'



class TracHtmlToHtmlFormatter(Formatter):
    """
    This is the formatter which convert trachtml to html .
    layout discripttion -> not convert
    [[BR]]              -> not convert
    definition          -> not convert
    escaping links '!'  -> process trac wiki 
    macro               -> process trac macro
    traclink            -> process traclink
    wikiprocesser       -> process processer
    """

    flavor = 'trachtml2html'
    


    # Override a few formatters to disable some wiki syntax in "oneliner"-mode
    def _list_formatter(self, match, fullmatch): return match
    def _definition_formatter(self, match, fullmatch): return match
    def close_def_list(self): pass

    def _bolditalic_formatter(self, match, fullmatch): return match
    #def _shref_formatter(self, match, fullmatch): return match
    #def _lhref_formatter(self, match, fullmatch): return match
    #def _make_link(self, ns, target, match, label): return match
    #def _make_ext_link(self, url, text, title=''): return match
    #def _make_relative_link(self, url, text): return match
    def _bold_formatter(self, match, fullmatch): return match
    def _italic_formatter(self, match, fullmatch): return match
    def _underline_formatter(self, match, fullmatch): return match
    def _strike_formatter(self, match, fullmatch): return match
    def _subscript_formatter(self, match, fullmatch): return match
    def _superscript_formatter(self, match, fullmatch): return match
    def _inlinecode_formatter(self, match, fullmatch): return match
    def _inlinecode2_formatter(self, match, fullmatch): return match
    def _htmlescapeentity_formatter(self, match, fullmatch): return match
    #def _macro_formatter(self, match, fullmatch): return match
    def _heading_formatter(self, match, fullmatch): return match
    def _indent_formatter(self, match, fullmatch): return match
    def _last_table_cell_formatter(self, match, fullmatch): return match
    def _table_cell_formatter(self, match, fullmatch): return match

    def open_paragraph(self): pass
    def close_paragraph(self): pass



class TracHtmlWrapFormatter(WikiToEditorHtmlFormatter):
    """
    This is the formatter which wrap wiki discription.
    layout discripttion -> not convert
    [[BR]]              -> not convert
    definition          -> not convert
    escaping links '!'  -> <span class="tmtrac_cancel">discription </span>
    macro               -> <span class="tmtrac">macro discription </span>
    traclink            -> <span class="tmtrac">traclink discription </span>
    wikiprocesser       -> <pre class="tmtrac">processer dicsription</pre> (without htmltag. and doesn't execute processer.)
    """
    flavor = 'wraphtrachtml'

    def _list_formatter(self, match, fullmatch): return match
    def _definition_formatter(self, match, fullmatch): return match
    def close_def_list(self): pass

    def _bolditalic_formatter(self, match, fullmatch): return match
    #def _shref_formatter(self, match, fullmatch): return match
    #def _lhref_formatter(self, match, fullmatch): return match
    #def _make_link(self, ns, target, match, label): return match
    #def _make_ext_link(self, url, text, title=''): return match
    #def _make_relative_link(self, url, text): return match
    def _bold_formatter(self, match, fullmatch): return match
    def _italic_formatter(self, match, fullmatch): return match
    def _underline_formatter(self, match, fullmatch): return match
    def _strike_formatter(self, match, fullmatch): return match
    def _subscript_formatter(self, match, fullmatch): return match
    def _superscript_formatter(self, match, fullmatch): return match
    def _inlinecode_formatter(self, match, fullmatch): return match
    def _inlinecode2_formatter(self, match, fullmatch): return match
    def _htmlescapeentity_formatter(self, match, fullmatch): return match
    #def _macro_formatter(self, match, fullmatch): return match
    def _heading_formatter(self, match, fullmatch): return match
    def _indent_formatter(self, match, fullmatch): return match
    def _last_table_cell_formatter(self, match, fullmatch): return match
    def _table_cell_formatter(self, match, fullmatch): return match

    def open_paragraph(self): pass
    def close_paragraph(self): pass

    def format(self, text, out, escape_newlines=False):
        self.out = out
        self._open_tags = []
        self._list_stack = []

        self.in_code_block = 0
        self.in_table = 0
        self.in_def_list = 0
        self.in_table_row = 0
        self.in_table_cell = 0
        self.indent_level = 0
        self.paragraph_open = 0

        for line in text.splitlines():
            # Throw a bunch of regexps on the problem
            result = re.sub(self.rules, self.replace, line)
            out.write(result )



class TracHTMLParser(HTMLParser):
    """
    This is the html parser for trachtml.
    """

    texts = ['',]
    output = ['',]
    mode = 3
    MODE_A = 1
    MODE_PRE = 2
    MODE_TEXT = 3
    MODE_H = 4
    head_tag = 'h1'
    need_end_flag = True

    env = None
    db = None
    req = None
    log = None

    spans = ['',]
    
    can_process = False # True: process traclinks and so on. False: not change
    can_wrap = False    # True: wrap traclink and so on.     False: not chage

    # set parse mode
    def set_traclink_mode(self,arg_can_process,arg_can_wrap):
        self.can_process = arg_can_process
        self.can_wrap = arg_can_wrap

    # clear data
    # for gard double output when feed twice
    def clear(self):
        
        self.output = ['',]
        self.texts = ['',]
        self.spans = ['',]
        self.mode = 3

    
    def handle_starttag(self, tag, attrs):
        self.need_end_flag = True
        if self.mode == self.MODE_A:
            self.texts.append(self.get_starttag_text())
        elif self.mode == self.MODE_PRE:
            if tag=='br':
                if self.can_process == True:
                    self.texts.append(os.linesep )
                if self.can_process == False:
                    self.texts.append('<br />')

        elif self.mode == self.MODE_TEXT:
            if tag == 'span':
                for key,value in attrs:
                    if key=='class' and value in ['tmtrac','tmtrac_cancel']:
                        self.spans.append('hit')
                        return
                self.spans.append('not')
            
            self.output_texts()
            if tag=='a' :
                self.mode = self.MODE_A
                self.output.append(self.get_starttag_text())
            elif tag in ('h1','h2','h3','h4','h5','h6') :
                self.head_tag = tag
                self.mode = self.MODE_H
                #self.output.append(self.get_starttag_text())
            elif tag=='pre' :
                self.mode = self.MODE_PRE
                if self.can_process == True:
                    self.texts.append(os.linesep + '{{{' + os.linesep)
                else :
                    self.output.append(self.get_starttag_text())
            elif tag == 'table' :
                attrtext = ['',]
                has_class = False
                for key,val in attrs:
                    attrtext.append(" %s=%s" % (key,val))
                    if key == 'class':
                        has_class = True
                if has_class == False :
                    attrtext.append(' class="wiki"')
                self.output.append("<table %s >" % ''.join(attrtext))
            else:
                self.output.append(self.get_starttag_text())
        
    def handle_endtag(self, tag): 
        if self.need_end_flag == True:
            data = '</' + tag + '>'
        else:
            data = ''
        
        if self.mode == self.MODE_A:
            if tag == 'a':
                self.output_texts()
                self.output.append(data)
                self.mode = self.MODE_TEXT
                
            else:
                self.texts.append(data)
        if self.mode == self.MODE_H:
            if tag in ('h1','h2','h3','h4','h5','h6') :
                self.output_texts()
                data = self.output.pop()
                id = self.output.pop()
                self.output.append('<%s id="%s">%s</%s>' %
                     (self.head_tag,id,unescape(data),self.head_tag))
                self.mode = self.MODE_TEXT
                

        elif self.mode == self.MODE_PRE:
            if tag == 'pre':
                if self.can_process == True:
                    self.texts.append('}}}'+os.linesep)
                    self.output_texts()
                else:
                    self.output_texts()
                    self.output.append(data)
                self.mode = self.MODE_TEXT
            else:
                pass
        else:
            if tag == 'span':
                if self.spans.pop() == 'hit':
                    return
            self.output_texts()
            self.output.append(data)
        
    def handle_startendtag(self, tag,attrs):
        self.handle_starttag( tag, attrs)
        self.need_end_flag = False
        self.handle_endtag( tag)
        self.need_end_flag = True

    def handle_data(self, data):
        datas = data.splitlines() #delete linesep.
        if self.mode != self.MODE_PRE:
            # delete linehead space,
            datas2 = datas[:1]
            for line in datas[1:]:
                while line.startswith(' '):
                    line = line[1:]
                datas2.append(line)
            datas = datas2
        self.texts.extend(datas) 
        

    def handle_charref(self, ref):
        data = unicode('\\u%04x' % int(ref),'Unicode-Escape').encode('utf-8')
        #self.texts.append('&#'+ref+';')
        self.texts.append(data)

    def handle_entityref(self, name):
        data = unicode('\\u%04x' % htmlentitydefs.name2codepoint[name],'Unicode-Escape').encode('utf-8')
        if self.mode == self.MODE_PRE  and self.can_wrap == True:
            data = '&' + name + ';'
        #if self.mode != self.MODE_PRE  and self.can_process == True :
        #    data = '&' + name + ';'
        if  self.can_wrap == False and self.can_process == False:
            data = '&' + name + ';'
        
        self.texts.append(data)
        
    def handle_comment(self, data):
        pass
        
    def handle_decl(self, decl):
        self.texts.append(decl)

    def handle_pi(self, data):
        pass

    def output_texts(self):
        data = ''.join(self.texts)
        if self.mode == self.MODE_H:
            self.output.append(data) # for attribute 'id'
        
        self.texts = ['',]
        if self.mode == self.MODE_A:
            self.output.append(data)
        elif self.mode == self.MODE_PRE:
            if self.can_process == True:
                data = wiki_to_html(data, self.env, self.req, self.db, 0, False)
            self.output.append(data)
        else:
            if self.can_process == True:
                out = StringIO()
                TracHtmlToHtmlFormatter(self.env, self.req, 0, self.db).format(data, out, False)
                data = out.getvalue()
                out.close()
            elif self.can_wrap == True:
                out = StringIO()
                TracHtmlWrapFormatter(self.env, self.req, 0, self.db).format(data, out, False)
                data = out.getvalue()
                out.close()
            self.output.append(data)
    
    def get_outputs(self):
        self.output_texts()
        return self.output
