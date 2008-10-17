""" Freemind plugin for Trac.
    
    Embeds Freemind mindmaps.
    
    Contributers:
      * Martin Scharrer <martin@scharrer-online.de>
        FreemindRenderer reference implementation.
"""
from genshi.builder import tag
from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.web.chrome import ITemplateProvider, add_script
from trac.wiki.macros import WikiMacroBase
from trac.mimeview.api import IHTMLPreviewRenderer


__version__ = '$Id$'[14:18]

EMBED_COUNT = '_freemindmacro_embed_count'

def get_absolute_url(base, url):
    """ Generate an absolute url from the url with the special schemes
        {htdocs,chrome,ticket,wiki,source} simply return the url if given with
        {http,https,ftp} schemes.
        
        Examples:
            http://example.com/filename.ext
                ie. http://www.google.com/logo.jpg
            
            htdocs://site/filename.ext
            htdocs://plugin/dir/filename.ext
                note: `chrome` is an alias for `htdocs`
            
            ticket://number/attachment.pdf
                ie. ticket://123/specification.pdf
            
            wiki://WikiWord/attachment.jpg
            
            source://changeset/path/filename.ext
                ie. source://1024/trunk/docs/README
    """
    def ujoin(*parts):
        """ Remove double slashes.
        """
        parts = [part.strip('/') for part in parts]
        return '/' + '/'.join(parts)
    
    if url.startswith(('ftp', 'http', 'https')):
        return url
    
    if url.startswith('chrome:'):
        url = url[7:]
        return ujoin(base, 'chrome', url)
    
    if url.startswith('htdocs:'):
        url = url[7:]
        return ujoin(base, 'chrome', url)
    
    if url.startswith('source:'):
        url = url[7:]
        return ujoin(base, 'export', url)
    
    if url.startswith('ticket:'):
        url = url[7:]
        return ujoin(base, 'raw-attachment/ticket', url)
    
    if url.startswith('wiki:'):
        url = url[5:]
        return ujoin(base, 'raw-attachment/wiki', url)
    
    return url

def string_keys(d):
    """ Convert unicode keys into string keys, suiable for func(**d) use.
    """
    sdict = {}
    for key, value in d.items():
        sdict[str(key)] = value
    
    return sdict

def xform_style(style):
    """ Convert between a style-string and a style-dictionary.
    """
    if isinstance(style, dict):
        result = '; '.join(['%s: %s' % (k, v) for k, v in style.items()])
        if result:
            result += ';'
    else:
        result = style.split(';')
        while '' in result:
            result.remove('')
        
        result = dict((s.strip() for s in i.split(':', 1)) for i in result)
    
    return result

def deslash(s):
    """ Temporarily fix issues with flashobject.js, maybe I should rewite
        it in a proper jQuery kind of way.
    """
    if s.startswith('/'):
        return s[1:]
    else:
        return s


class FreemindMacro(WikiMacroBase):
    
    implements(IWikiMacroProvider, ITemplateProvider)
    
    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content, strict=True)
        try:
            kwargs = string_keys(kwargs)
        except:
            raise TracError('Error #3922, content: %s, args: %s, kwargs: %s', (str(content), str(args), kwargs))
        
        if len(args) >= 1:
            url = args[0]
        elif len(args) == 0:
            raise TracError('URL to the mindmap at least required.')
        
        embed_count = getattr(formatter, EMBED_COUNT, 0)
        embed_count += 1
        setattr(formatter, EMBED_COUNT, embed_count)
        
        if embed_count == 1:
            add_script(formatter.req, 'freemind/js/flashobject.js')
        
        url = get_absolute_url(formatter.href.base, url)
        base = url[:url.rfind('/')+1]
        
        script = '''\
            $(document).ready(function() {
                $("#flashcontent%(count)02d").mouseover(function() {
                    document.visorFreeMind%(count)02d.focus();
                });
                
                var fo = new FlashObject("%(visor)s", "visorFreeMind%(count)02d", "100%%", "100%%", 6, "#9999ff");
                
                fo.addParam("quality","high");
                fo.addParam("bgcolor","#a0a0f0");
                fo.addVariable("openUrl","_blank");
                fo.addVariable("startCollapsedToLevel","3");
                fo.addVariable("maxNodeWidth","200");
                fo.addVariable("mainNodeShape","elipse");
                fo.addVariable("justMap","false");
                fo.addVariable("initLoadFile","%(file)s");
                fo.addVariable("defaultToolTipWordWrap",200);
                fo.addVariable("offsetX","left");
                fo.addVariable("offsetY","top");
                fo.addVariable("buttonsPos","top");
                fo.addVariable("min_alpha_buttons",20);
                fo.addVariable("max_alpha_buttons",100);
                fo.addVariable("scaleTooltips","false");
                fo.addVariable("baseImagePath","%(base)s");
                fo.addVariable("CSSFile","%(css)s");
                //fo.addVariable("toolTipsBgColor","0xa0a0f0");
                //fo.addVariable("genAllShots","true");
                //fo.addVariable("unfoldAll","true");
                fo.write("flashcontent%(count)02d");
            });
        ''' % {
            'count': embed_count,
            'visor': get_absolute_url(formatter.href.base, 'htdocs://freemind/swf/visorFreemind.swf'),
            'file': url,
            'base': base,
            'css': get_absolute_url(formatter.href.base, 'htdocs://freemind/css/flashfreemind.css'),
        }
        
        # Debugging.
        if 'debug' in args:
            import os
            import datetime
            
            output = "FreemindMacro Debug Log\n"\
                     "=======================\n\n"\
                     "system: %(system)s\n"\
                     "time: %(time)s\n"\
                     "version: %(version)s\n"\
                     "content: %(content)s\n"\
                     "args: %(args)s\n"\
                     "kwargs: %(kwargs)s\n"\
                     "formatter.href.base: %(base)s\n"\
                     "script: \n\n"\
                     "%(script)s" % {
                
                'system': str(os.uname()),
                'time': datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'),
                'version': __version__,
                'content': content,
                'args': str(args),
                'kwargs': str(kwargs),
                'base': str(formatter.href.base),
                'script': script
            }
            
            return tag.pre(output, style='border: 2px dashed red; padding: 5px; background: #eee;')
        
        
        style_dict = xform_style(kwargs.get('style', ''))
        
        width = kwargs.pop('width', style_dict.get('width', '800px'))
        height = kwargs.pop('height', style_dict.get('height', '600px'))
        
        style_dict['border'] = style_dict.get('border', '1px solid #cccccc;')
        style_dict['margin'] = style_dict.get('margin', '0 auto')
        style_dict['width'] = width
        style_dict['height'] = height
        
        kwargs['style'] = xform_style(style_dict)
        
        # You can't touch this...
        kwargs.pop('id', None)
        
        if 'class' in kwargs:
            kwargs['class_'] = kwargs.pop('class')
        
        tags = []
        tags.append(tag.div('Flash plugin or JavaScript are turned off. Activate both and reload to view the mindmap.',
                            id='flashcontent%02d' % embed_count, **kwargs))
        tags.append(tag.script(script))
        
        return ''.join([str(i) for i in tags])
    
    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """ Makes the 'htdocs' folder inside the egg available.
        """
        from pkg_resources import resource_filename
        return [('freemind', resource_filename('freemind', 'htdocs'))]
    
    def get_templates_dirs(self):
        return []  # must return an iterable


class FreemindRenderer(Component):
    """ Preview mindmaps when browsing the repository or attachments.
    """
    implements(IHTMLPreviewRenderer)
    
    expand_tabs = False
    returns_source = False
    
    def get_quality_ratio(self, mimetype):
        if mimetype in ('text/x-freemind', 'text/freemind', 'application/x-freemind', 'application/freemind'):
            return 8
        return 0
    
    def render(self, context, mimetype, content, filename=None, url=None):
        """ HTML preview mindmaps in svn-browse and attachment views.
        """
        base = url[:url.rfind('/')+1]
        
        tags = []
        #add_script(contex.req, 'freemind/js/flashobject.js')
        #tags.append(tag.script(src=get_absolute_url(context.href.base, 'htdocs://freemind/js/flashobject.js')))
        tags.append('<script src="%s"></script>' % get_absolute_url(context.href.base, 'htdocs://freemind/js/flashobject.js'))
        
        script = '''
            $(document).ready(function() {
                $("#flashcontent").mouseover(function() {
                    document.visorFreeMind.focus();
                });
                
                var fo = new FlashObject("%(visor)s", "visorFreeMind", "100%%", "100%%", 6, "#9999ff");
                
                fo.addParam("quality","high");
                fo.addParam("bgcolor","#a0a0f0");
                fo.addVariable("openUrl","_blank");
                fo.addVariable("startCollapsedToLevel","3");
                fo.addVariable("maxNodeWidth","200");
                fo.addVariable("mainNodeShape","elipse");
                fo.addVariable("justMap","false");
                fo.addVariable("initLoadFile","%(file)s");
                fo.addVariable("defaultToolTipWordWrap",200);
                fo.addVariable("offsetX","left");
                fo.addVariable("offsetY","top");
                fo.addVariable("buttonsPos","top");
                fo.addVariable("min_alpha_buttons",20);
                fo.addVariable("max_alpha_buttons",100);
                fo.addVariable("scaleTooltips","false");
                fo.addVariable("baseImagePath","%(base)s");
                fo.addVariable("CSSFile","%(css)s");
                //fo.addVariable("toolTipsBgColor","0xa0a0f0");
                //fo.addVariable("genAllShots","true");
                //fo.addVariable("unfoldAll","true");
                fo.write("flashcontent");
            });
        ''' % {
            'visor': get_absolute_url(context.href.base, 'htdocs://freemind/swf/visorFreemind.swf'),
            'file': url,
            'base': base,
            'css': get_absolute_url(context.href.base, 'htdocs://freemind/css/flashfreemind.css'),
        }
        
        tags.append(tag.script(script))
        tags.append(tag.div('Flash plugin or JavaScript are turned off. Activate both and reload to view the mindmap.',
                            id='flashcontent',
                            style='border: 1px solid #cccccc; height: 600px; width: 100%;'))
        
        return ''.join([str(i) for i in tags])
