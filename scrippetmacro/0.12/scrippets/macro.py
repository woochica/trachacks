# vim: expandtab
import re, time
from StringIO import StringIO

from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import format_to_html
from trac.util import TracError
from trac.util.text import to_unicode
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.wiki.api import parse_args, IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

class ScrippetMacro(WikiMacroBase):
    """A macro to add scrippets to a page. Usage:
    """
    implements(IWikiMacroProvider, ITemplateProvider)

    def expand_macro(self, formatter, name, content, args):
#        self.log.debug("ARGUMENTS: %s " % args)
#        self.log.debug("INITIAL CONTENT: %s" % content)
        req = formatter.req
        if args != {} and args != None and args['mode'] == "full":
            add_stylesheet(req, 'scrippets/css/scrippets-full.css')
            mode = "-full"
        else:
            add_stylesheet(req, 'scrippets/css/scrippets.css')
            mode = ""
        #Sceneheaders must start with INT, EXT, or EST
        sceneheader_re = re.compile('\n(INT|EXT|[^a-zA-Z0-9]EST)([\.\-\s]+?)(.+?)([A-Za-z0-9\)\s\.])\n')
        #Transitions
        transitions_re = re.compile('\n([^<>\na-z]*?:|FADE TO BLACK\.|FADE OUT\.|CUT TO BLACK\.)[\s]??\n')
        #action blocks
        actions_re = re.compile('\n{2}(([^a-z\n\:]+?[\.\?\,\s\!]*?)\n{2}){1,2}')
        #character cues
        characters_re = re.compile('\n([^<>a-z\s][^a-z:\!\?]*?[^a-z\(\!\?:,][\s]??)\n{1}')
        #parentheticals
        parentheticals_re = re.compile('(\([^<>]*?\)[\s]??)\n')
        #dialog
        dialog_re = re.compile('(<p class="character">.*<\/p>|<p class="parenthetical">.*<\/p>)\n{0,1}(.+?)\n')
        #default
        default_re = re.compile('([^<>]*?)\n')
        #clean up
        cleanup_re = re.compile('<p class="action">[\n\s]*?<\/p>')
        #styling
        bold_re = re.compile('(\*{2}|\[b\])(.*?)(\*{2}|\[\/b\])')
        italic_re = re.compile('(\*{1}|\[i\])(.*?)(\*{1}|\[\/i\])')
        underline_re = re.compile('(_|\[u\])(.*?)(_|\[\/u\])')
        
        theoutput = tag.div(class_="scrippet"+mode)        
        _content = content
#        self.log.debug("BEFORE SCENE: %s" % _content)
        _content = sceneheader_re.sub(r'<p class="sceneheader">\1\2\3\4</p>' + "\n",_content)
#        self.log.debug("BEFORE TRANSITIONS: %s" % _content)
        _content = transitions_re.sub(r'<p class="transition">\1</p>' + "\n",_content)
#        self.log.debug("BEFORE ACTIONS: %s" % _content)
        _content = actions_re.sub("\n" + r'<p class="action">\2</p>' + "\n",_content)
#        self.log.debug("BEFORE CHARACTERS: %s" % _content)
        _content = characters_re.sub(r'<p class="character">\1</p>',_content)
        _content = parentheticals_re.sub(r'<p class="parenthetical">\1</p>',_content)
        _content = dialog_re.sub(r'\1' + "\n" + r'<p class="dialogue">\2</p>' + "\n",_content)
        _content = default_re.sub(r'<p class="action">\1</p>' + "\n",_content)
        _content = cleanup_re.sub("",_content)
        _content = bold_re.sub(r'<b>\2</b>',_content)
        _content = italic_re.sub(r'<i>\2</i>',_content)
        _content = underline_re.sub(r'<u>\2</u>',_content)
        para_re = re.compile(r'<p class="(?P<_class>.*?)">(?P<_body>.*?)</p>')
        for line in _content.splitlines():
#            self.log.debug("LINE: %s" % line)
            m = para_re.search(line)
            if m != None:
#                self.log.debug("BODY: %s" % m.group('_body'))
#                self.log.debug("CLASS: %s" % m.group('_class'))
                if "FADE IN" in m.group('_body') and m.group('_class') == "transition":
                    theoutput.append(tag.p(m.group('_body'),class_="action"+mode))
                else:
                    theoutput.append(tag.p(m.group('_body'),class_=m.group('_class')+mode))
#        self.log.debug("OUTPUT: %s" % theoutput)
        return theoutput
    
    ## ITemplateProvider
            
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('scrippets', resource_filename(__name__, 'htdocs'))]
                                      
    def get_templates_dirs(self):
        return []
                                        
