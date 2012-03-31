# vim: expandtab
import re, time
from StringIO import StringIO

from genshi.builder import tag

from trac.core import *
from trac.wiki.formatter import format_to_html, format_to_oneliner
from trac.util import TracError
from trac.util.text import to_unicode
from trac.web.chrome import add_stylesheet, ITemplateProvider
from trac.wiki.api import parse_args, IWikiMacroProvider
from trac.wiki.macros import WikiMacroBase
from trac.wiki.model import WikiPage
from trac.wiki.web_ui import WikiModule

import xml.etree.ElementTree as ElementTree
import xml.etree.cElementTree as cElementTree

class ScrippetMacro(WikiMacroBase):
    """A macro to add scrippets to a page. Usage:
    """
    implements(IWikiMacroProvider, ITemplateProvider)

    def render_inline_content(self, _env, _context, _content,mode):
        #Sceneheaders must start with INT, EXT, or EST
        sceneheader_re = re.compile('\n(INT|EXT|[^a-zA-Z0-9]EST)([\.\-\s]+?)(.+?)([A-Za-z0-9\)\s\.])\n')
        #Transitions
        transitions_re = re.compile('\n([^<>\na-z]*?:|FADE TO BLACK\.|FADE OUT\.|CUT TO BLACK\.)[\s]??\n')
        #action blocks
        actions_re = re.compile('\n{2}(([^a-z\n\:]+?[\.\?\,\s\!]*?)\n{2}){1,2}')
        #character cues    
        characters_re = re.compile('\n{1}(\w+[\.-]*[\s]*\w+?[^\!\)\?\.\s])\n{1}')
#        characters_re = re.compile('\n([^<>a-z\s][^a-z:\!\?]*?[^a-z\(\!\?:,][\s]??)\n{1}')
        #parentheticals
        parentheticals_re = re.compile('(\([^<>]*?\)[\s]??)\n')
        #dialog
        dialog_re = re.compile('(<p class="character">.*<\/p>|<p class="parenthetical">.*<\/p>)\n{0,1}(.+?)\n')
        #default
        default_re = re.compile('([^<>]*?)\n')
        #clean up
        cleanup_re = re.compile('<p class="action">[\n\s]*?<\/p>')
        #styling
#        bold_re = re.compile('(\*{2}|\[b\])(.*?)(\*{2}|\[\/b\])')
#        italic_re = re.compile('(\*{1}|\[i\])(.*?)(\*{1}|\[\/i\])')
#        underline_re = re.compile('(_|\[u\])(.*?)(_|\[\/u\])')
        
        theoutput = tag.div(class_="scrippet"+mode)        
#        self.log.debug("BEFORE SCENE: %s" % _content)
        _content = sceneheader_re.sub(r'<p class="sceneheader">\1\2\3\4</p>' + "\n",_content)
#        self.log.debug("BEFORE TRANSITIONS: %s" % _content)
        _content = transitions_re.sub(r'<p class="transition">\1</p>' + "\n",_content)
#        self.log.debug("BEFORE ACTIONS: %s" % _content)
        _content = actions_re.sub("\n" + r'<p class="action">\2</p>' + "\n",_content)
#        self.log.debug("BEFORE CHARACTERS: %s" % _content)
#        self.log.debug(_content);
        _content = characters_re.sub(r'<p class="character">\1</p>',_content)
#        self.log.debug(characters_re.sub(r'<p class="character">\1</p>',_content));
        _content = parentheticals_re.sub(r'<p class="parenthetical">\1</p>',_content); #format_to_oneliner(_env, _context, _content))
        _content = dialog_re.sub(r'\1' + "\n" + r'<p class="dialogue">\2</p>' + "\n",_content); #format_to_oneliner(_env, _context, _content))
        _content = default_re.sub(r'<p class="action">\1</p>' + "\n",_content)
        _content = cleanup_re.sub("",_content)
#        _content = bold_re.sub(r'<b>\2</b>',_content)
#        _content = italic_re.sub(r'<i>\2</i>',_content)
#        _content = underline_re.sub(r'<u>\2</u>',_content)
        para_re = re.compile(r'<p class="(?P<_class>.*?)">(?P<_body>.*?)</p>')
        for line in _content.splitlines():
#            self.log.debug("LINE: %s" % line)
            m = para_re.search(line)
            if m != None:
#                self.log.debug("BODY: %s" % m.group('_body'))
#                self.log.debug("CLASS: %s" % m.group('_class'))
                if "FADE IN" in m.group('_body') and m.group('_class') == "transition":
                    theoutput.append(tag.p(format_to_oneliner(_env, _context,m.group('_body')),class_="action"+mode))
                else:
                    theoutput.append(tag.p(format_to_oneliner(_env, _context,m.group('_body')),class_=m.group('_class')+mode))
        return theoutput
    
    def render_fdx_subset(self,fdx,start_with_scene,end_with_scene,mode,formatter):
        theoutput = tag.div(class_="scrippet"+mode)
#        self.log.debug("FDX: %s START: %d END %d" % (fdx,start_with_scene,end_with_scene))
        fdx_obj = self._get_src(self.env, formatter.req, *fdx)
        fd_doc = cElementTree.fromstring(fdx_obj.getStream().read())
        renderParagraphs = False
        for fd_content in fd_doc.findall("Content"):
            for fd_paragraph in fd_content.findall("Paragraph"):
                ptype = fd_paragraph.get('Type')
                if ptype == "Action":
                    ptype = "action"
                elif ptype == "Character":
                    ptype = "character"
                elif ptype == "Dialogue":
                    ptype = "dialogue"
                elif ptype == "Parenthetical":
                    ptype = "parenthetical"
                elif ptype == "Shot":
                    ptype = "shot"
                elif ptype == "Scene Heading":
                    if int(fd_paragraph.get('Number')) == start_with_scene:
                        renderParagraphs = True
                    if int(fd_paragraph.get('Number')) == end_with_scene:
                        renderParagraphs = False
                    ptype = "sceneheader"
                elif ptype == "Transition":
                    ptype = "transition"
                elif ptype == "Teaser/Act One":
                    ptype = "header"
                elif ptype == "New Act":
                    ptype = "header"
                elif ptype == "End Of Act":
                    ptype = "header"
                else:
                    ptype = "action"
                #UNHANDLED FOR THE MOMENT
                #Show/Ep. Title
                ptext = []
                for fd_text in fd_paragraph.findall("Text"):
                    text_style = fd_text.get('Style')
                    if fd_text.text != None:
                        if "FADE IN:" in fd_text.text.upper():
                            fd_text.text = fd_text.text.upper()
                        if ptype in ["character","transition","sceneheader","header","shot"]:
                            fd_text.text = fd_text.text.upper()
                        #clean smart quotes
                        fd_text.text = fd_text.text.replace(u"\u201c", "\"").replace(u"\u201d", "\"") #strip double curly quotes
                        fd_text.text  = fd_text.text.replace(u"\u2018", "'").replace(u"\u2019", "'").replace(u"\u02BC", "'") #strip single curly quotes
                        ptext.append({"style":text_style,"text":fd_text.text})
                content = []
                for block in ptext:
                    if block["style"] == "Italic":
                        
                        content.append(tag.i(block["text"]))
                    elif block["style"] == "Underline":
                        content.append(tag.u(block["text"]))
                    elif block["style"] == "Bold":
                        content.append(tag.b(block["text"]))
                    elif block["style"] == "Bold+Underline":
                        content.append(tag.b(tag.u(block["text"])))
                    else:
                        content.append(block["text"])
                if renderParagraphs:
                    theoutput.append(tag.p(content,class_=ptype+mode))
        return theoutput

    def expand_macro(self, formatter, name, content, args):
        fdx = False
        start_with_scene = False
        end_with_scene = False
#        self.log.debug("EXPAND ARGUMENTS: %s " % args)
#        self.log.debug("EXPAND INITIAL CONTENT: %s" % content)
        req = formatter.req
        if content:
            args2,kw = parse_args(content)
#            self.log.debug("RENDER ARGUMENTS: %s " % args2)
#            self.log.debug("RENDER KW: %s " % kw)
            if 'fdx' in kw:
                fdx = self._parse_filespec(kw['fdx'].strip(), formatter.context, self.env)
            if 'start_with_scene' in kw:
                start_with_scene = int(kw['start_with_scene'])
            if 'end_with_scene' in kw:
                end_with_scene = int(kw['end_with_scene'])
            elif 'start_with_scene' in kw:
                end_with_scene = int(kw['start_with_scene']) + 1
                
        if args != {} and args != None and args['mode'] == "full":
            add_stylesheet(req, 'scrippets/css/scrippets-full.css')
            mode = "-full"
        elif kw != {} and fdx:
            add_stylesheet(req, 'scrippets/css/scrippets.css')
            mode = ""
            return self.render_fdx_subset(fdx,start_with_scene,end_with_scene,mode,formatter)
        else:
            add_stylesheet(req, 'scrippets/css/scrippets.css')
            mode = ""
            return self.render_inline_content(self.env, formatter.context, content,mode)
    
    ## ITemplateProvider
            
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('scrippets', resource_filename(__name__, 'htdocs'))]
                                      
    def get_templates_dirs(self):
        return []

    def _parse_filespec(self, filespec, context, env):
        # parse filespec argument to get module and id if contained.
        if filespec[:5] == 'http:' or filespec[:6] == 'https:':
            parts = [ 'url', '', filespec ]
        else:
            parts = filespec.split(':', 2)

        if len(parts) == 3:                 # module:id:attachment
            if parts[0] in ['wiki', 'ticket', 'browser', 'file', 'url']:
                module, id, file = parts
            else:
                raise Exception("unknown module %s" % parts[0])

        elif len(parts) == 2:
            from trac.versioncontrol.web_ui import BrowserModule
            try:
                browser_links = [link for link,_ in
                                 BrowserModule(env).get_link_resolvers()]
            except Exception:
                browser_links = []

            id, file = parts
            if id in browser_links:         # source:path
                module = 'browser'
            elif id and id[0] == '#':       # #ticket:attachment
                module = 'ticket'
                id = id[1:]
            elif id == 'htdocs':            # htdocs:path
                module = 'file'
            else:                           # WikiPage:attachment
                module = 'wiki'

        elif len(parts) == 1:               # attachment
            # determine current object
            module = context.resource.realm or 'wiki'
            id     = context.resource.id
            file   = filespec
            if module not in ['wiki', 'ticket']:
                raise Exception('Cannot reference local attachment from here')
            if not id:
                raise Exception('unknown context id')

        else:
            raise Exception('No filespec given')

        return module, id, file

    def _get_src(env, req, module, id, file):
        # check permissions first
        if module == 'wiki'    and 'WIKI_VIEW' not in req.perm   or \
           module == 'ticket'  and 'TICKET_VIEW' not in req.perm or \
           module == 'file'    and 'FILE_VIEW' not in req.perm   or \
           module == 'browser' and 'BROWSER_VIEW' not in req.perm:
            raise Exception('Permission denied: %s' % module)

        if module == 'browser':
            return BrowserSource(env, req, file)
        if module == 'file':
            return FileSource(env, id, file)
        if module == 'wiki' or module == 'ticket':
            return AttachmentSource(env, module, id, file)
        if module == 'url':
            return UrlSource(file)

        raise Exception("unsupported module '%s'" % module)

    _get_src = staticmethod(_get_src)
    
class TransformSource(object):
    """Represents the source of an input (stylesheet or xml-doc) to the transformer"""

    def __init__(self, module, id, file, obj):
        self.module = module
        self.id     = id
        self.file   = file
        self.obj    = obj

    def isFile(self):
        return False

    def getFile(self):
        return None

    def getUrl(self):
        return "%s://%s/%s" % (self.module, str(self.id).replace("/", "%2F"), self.file)

    def get_last_modified(self):
        return to_datetime(None)

    def __str__(self):
        return str(self.obj)

    def __del__(self):
        if self.obj and hasattr(self.obj, 'close') and callable(self.obj.close):
            self.obj.close()

    class CloseableStream(object):
        """Implement close even if underlying stream doesn't"""

        def __init__(self, stream):
            self.stream = stream

        def read(self, len=None):
            return self.stream.read(len)

        def close(self):
            if hasattr(self.stream, 'close') and callable(self.stream.close):
                self.stream.close()    

class BrowserSource(TransformSource):
    def __init__(self, env, req, file):
        from trac.versioncontrol import RepositoryManager
        from trac.versioncontrol.web_ui import get_existing_node

        if hasattr(RepositoryManager, 'get_repository_by_path'): # Trac 0.12
            repo, file = RepositoryManager(env).get_repository_by_path(file)[1:3]
        else:
            repo = RepositoryManager(env).get_repository(req.authname)
        obj = get_existing_node(req, repo, file, None)

        TransformSource.__init__(self, "browser", "source", file, obj)

    def getStream(self):
        return self.CloseableStream(self.obj.get_content())

    def __str__(self):
        return self.obj.path

    def get_last_modified(self):
        return self.obj.get_last_modified()

class FileSource(TransformSource):
    def __init__(self, env, id, file):
        file = re.sub('[^a-zA-Z0-9._/-]', '', file)     # remove forbidden chars
        file = re.sub('^/+', '', file)                  # make sure it's relative
        file = os.path.normpath(file)                   # resolve ..'s
        if file.startswith('..'):                       # don't allow above doc-root
            raise Exception("illegal path '%s'" % file)

        if id != 'htdocs':
            raise Exception("unsupported file id '%s'" % id)

        obj = os.path.join(env.get_htdocs_dir(), file)

        TransformSource.__init__(self, "file", id, file, obj)

    def isFile(self):
        return True

    def getFile(self):
        return self.obj

    def getStream(self):
        import urllib
        return urllib.urlopen(self.obj)

    def get_last_modified(self):
        return to_datetime(os.stat(self.obj).st_mtime)

    def __str__(self):
        return self.obj

class AttachmentSource(TransformSource):
    def __init__(self, env, module, id, file):
        from trac.attachment import Attachment
        obj = Attachment(env, module, id, file)

        TransformSource.__init__(self, module, id, file, obj)

    def getStream(self):
        return self.obj.open()

    def get_last_modified(self):
        return to_datetime(os.stat(self.obj.path).st_mtime)

    def __str__(self):
        return self.obj.path

class UrlSource(TransformSource):
    def __init__(self, url):
        import urllib
        try:
            obj = urllib.urlopen(url)
        except Exception, e:
            raise Exception('Could not read from url "%s": %s' % (file, e))

        TransformSource.__init__(self, "url", None, url, obj)

    def getStream(self):
        return self.obj

    def getUrl(self):
        return self.file

    def get_last_modified(self):
        lm = self.obj.info().getdate('Last-modified')
        if lm:
            from datetime import datetime
            from util.datefmt import FixedOffset
            return datetime(lm[0], lm[1], lm[2], lm[3], lm[4], lm[5], 0,
                            FixedOffset(lm[9], 'custom'))
        return to_datetime(None)

    def __str__(self):
        return self.obj.url

