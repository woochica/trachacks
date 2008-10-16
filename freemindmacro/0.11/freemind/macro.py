""" Freemind plugin for Trac.
    
    Embeds Freemind mindmaps.
"""
from genshi.builder import tag
from trac.core import *
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.web.chrome import ITemplateProvider, add_script
from trac.wiki.macros import WikiMacroBase


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


class FreemindMacro(WikiMacroBase):
    
    implements(IWikiMacroProvider, ITemplateProvider)
    
    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content, strict=False)
        kwargs = string_keys(kwargs)
        
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
        
        script = '''
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
