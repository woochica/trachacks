# -*- coding: utf-8 -*-
""" Movie plugin for Trac.
    
    Embeds various online movies.
"""
from urlparse import urlparse, urlunparse
from genshi.builder import tag
from trac.core import *
from trac.resource import Resource, get_resource_url
from trac.web.chrome import ITemplateProvider, add_script
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.macros import WikiMacroBase

EMBED_COUNT = '_moviemacro_embed_count'
FLOWPLAYER_EMBEDDED = '_moviemacro_flowplayer_embedded'

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

def xform_query(query):
    """ Convert between a query-string and a query-dictionary.
    """
    if isinstance(query, dict):
        result = '&'.join(['%s=%s' % (k, v) for k, v in query.items()])
    else:
        result = query.split('&')
        while '' in result:
            result.remove('')
        
        result = dict((s.strip() for s in i.split('=', 1)) for i in result)
    
    return result


class MovieMacro(WikiMacroBase):
    """ Embed online movies from YouTube, GoogleVideo and MetaCafe, and local
        movies via FlowPlayer.
    """
    
    implements(ITemplateProvider)
    
    # IWikiMacroProvider methods
    def expand_macro(self, formatter, name, content):
        args, kwargs = parse_args(content, strict=True)
        kwargs = string_keys(kwargs)
        
        if len(args) >= 1:
            url = args[0]
        elif len(args) == 0:
            raise TracError('URL to a movie at least required.')
        
        embed_count = getattr(formatter, EMBED_COUNT, 0)
        embed_count += 1
        setattr(formatter, EMBED_COUNT, embed_count)
        
        flowplayer_embedded = getattr(formatter, FLOWPLAYER_EMBEDDED, False)
        
        url = self._get_absolute_url(formatter.req, url)
        src = self._get_absolute_url(formatter.req, kwargs.pop('splash', 'htdocs://movie/img/black.jpg'))
        
        scheme, netloc, path, params, query, fragment = urlparse(url)
        
        try:
            style_dict = xform_style(kwargs.get('style', ''))
        except:
            raise TracError('Double check the `style` argument.')
        
        style = {
            'display': 'block',
            'border': style_dict.get('border', 'none'),
            'margin': style_dict.get('margin', '0 auto'),
            'clear': 'both'
        }
        
        if netloc == 'www.youtube.com' or netloc == 'www.youtube-nocookie.com':
            query_dict = xform_query(query)
            video = query_dict.get('v')
            
            url = urlunparse((scheme, netloc, '/v/%s' % video, '', '', ''))
            
            width = kwargs.pop('width', style_dict.get('width', '425px'))
            height = kwargs.pop('height', style_dict.get('height', '344px'))
            
            style.update({
                'width': width,
                'height': height,
            })
            
            return tag.object(tag.param(name='movie', value=url),
                              tag.param(name='allowFullScreen', value='true'),
                              tag.embed(src=url, type='application/x-shockwave-flash', allowfullscreen='true', width=width, height=height),
                              style=xform_style(style))
        
        if netloc == 'video.google.com':
            query_dict = xform_query(query)
            query_dict['hl'] = 'en'
            query_dict['fs'] = 'true'
            
            query = xform_query(query_dict)
            
            url = urlunparse((scheme, netloc, '/googleplayer.swf', '', query, ''))
            
            width = kwargs.pop('width', style_dict.get('width', '400px'))
            height = kwargs.pop('height', style_dict.get('height', '326px'))
            
            style.update({
                'width': width,
                'height': height,
            })
            
            return tag.embed(src=url,
                             allowFullScreen='true',
                             allowScriptAccess='always',
                             type='application/x-shockwave-flash',
                             style=xform_style(style))
        
        if netloc == 'www.metacafe.com':
            parts = path.split('/')
            try:
                path = '/fplayer/%s/%s.swf' % (parts[2], parts[3])
            except:
                raise TracError("Non-standard URL, don't know how to process it, file a ticket please.")
            
            url = urlunparse((scheme, netloc, path, '', '', ''))
            
            width = kwargs.pop('width', style_dict.get('width', '400px'))
            height = kwargs.pop('height', style_dict.get('height', '345px'))
            
            style.update({
                'width': width,
                'height': height,
            })
            
            return tag.embed(src=url,
                             wmode='transparent',
                             pluginspage='http://www.macromedia.com/go/getflashplayer',
                             type='application/x-shockwave-flash',
                             style=xform_style(style))
        
        # Requested by Zach, #4188.
        if netloc in ('vimeo.com', 'www.vimeo.com'):
            parts = path.split('/')
            
            while '' in parts:
                parts.remove('')
            
            path = '/moogaloop.swf?clip_id=%s&amp;server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=0&amp;color=&amp;fullscreen=1' % parts[0]
            url = urlunparse((scheme, netloc, path, '', '', ''))
            
            width = kwargs.pop('width', style_dict.get('width', '640px'))
            height = kwargs.pop('height', style_dict.get('height', '401px'))
            
            style.update({
                'width': width,
                'height': height,
            })
            
            return tag.object(tag.param(name='movie', value=url),
                              tag.param(name='allowfullscreen', value='true'),
                              tag.param(name='allowscriptaccess', value='always'),
                              tag.embed(src=url, type='application/x-shockwave-flash', allowfullscreen='true', allowscriptaccess='always', width=width, height=height),
                              style=xform_style(style))
        
        # Local movies.
        tags = []
        
        if not flowplayer_embedded:
            add_script(formatter.req, 'movie/js/flashembed.min.js')
            add_script(formatter.req, 'movie/js/flow.embed.js')
            
            script = '''
                $(function() {
                
                    $("a.flowplayer").flowembed("%s",  {initialScale:'scale'});
                });
            ''' % self._get_absolute_url(formatter.req, 'htdocs://movie/swf/FlowPlayerDark.swf')
            
            tags.append(tag.script(script))
            
            setattr(formatter, FLOWPLAYER_EMBEDDED, True)
        
        width = kwargs.pop('width', style_dict.get('width', '320px'))
        height = kwargs.pop('height', style_dict.get('height', '320px'))
        
        style.update({
            'width': width,
            'height': height,
        })
        
        if kwargs.pop('clear', None) == 'none':
            style.pop('clear')
        
        kwargs = {'style': xform_style(style)}
        
        tags.append(tag.a(tag.img(src=src, **kwargs), class_='flowplayer', href=url, **kwargs))
        
        return ''.join([str(i) for i in tags])

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        """ Makes the 'htdocs' folder inside the egg available.
        """
        from pkg_resources import resource_filename
        return [('movie', resource_filename('movie', 'htdocs'))]

    def get_templates_dirs(self):
        return []

    def _get_absolute_url(self, req, url):
        """ Generate an absolute url from the url with the special schemes
        {htdocs,chrome,ticket,wiki,source} simply return the url if given with
        {http,https,ftp} schemes.
        
        Examples:
            http://example.com/filename.ext
                ie. http://www.google.com/logo.jpg
            
            chrome://site/filename.ext
            htdocs://img/filename.ext
                note: `chrome` is an alias for `htdocs`
            
            ticket://number/attachment.pdf
                ie. ticket://123/specification.pdf
            
            wiki://WikiWord/attachment.jpg
            
            source://changeset/path/filename.ext
                ie. source://1024/trunk/docs/README
        """

        scheme, netloc, path, query, params, fragment = urlparse(url)

        if scheme in ('htdocs', 'chrome'):
            return req.abs_href.chrome(netloc + path)

        if scheme in ('source',):
            return req.abs_href.export(netloc + path)

        if scheme in ('wiki','ticket'):
            resource = Resource(scheme, netloc).child('attachment', path)
            return get_resource_url(self.env, resource, req.abs_href, format='raw')

        return url
