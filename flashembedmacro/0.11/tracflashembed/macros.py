# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Alexey Kinyov <rudy@05bit.com>
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution.
#

from StringIO import StringIO
from genshi.builder import tag
from trac.wiki.api import IWikiMacroProvider, parse_args
from trac.wiki.formatter import format_to_oneliner, extract_link
from trac.wiki.macros import WikiMacroBase


__all__ = ['EmbedMacro',]


class EmbedMacro(WikiMacroBase):
    """
    Macro produces html code for embedding flash content from certain
    service, by it's 'key' and content id. It also can embed simple SWF
    by it's URL.

    Syntax and examples:
    {{{
     [[Embed(youtube=emYqURahUKI)]]
     [[Embed(vimeo=3840952,w=400,h=300)]]
     [[Embed(swf=http://media.nadprof.org/flash/rudy/flowers/flowers.swf,w=500,h=400)]]
    }}}

    Available keys:
     * ''youtube'': video from !YouTube http://youtube.com
     * ''vimeo'': video from Vimeo http://vimeo.com
     * ''swf'': SWF by URL

    Optional parameters:
     * ''w'' and ''h'': width and height of embedded flash object
    """
    
    revision = "$Rev$"
    
    url = "$URL$"

    def expand_macro(self, formatter, name, content):
        """ Produces html code by 'key' and content id.
        """
        args, params = parse_args(content, strict=False)
        
        if 'youtube' in params:
            return embed_youtube(params['youtube'], params)
        elif 'vimeo' in params:
            return embed_vimeo(params['vimeo'], params)
        elif 'swf' in params:
            return embed_swf(formatter, params)
            
        return '<!-- Unknown content type! -->'


def embed_youtube(id, params):
    """
    Produces embedding code for YouTube.
    """
    code = '<object width="%(w)d" height="%(h)d">\
<param name="movie" value="http://www.youtube.com/v/%(#)s&hl=ru&fs=1"></param>\
<param name="allowFullScreen" value="true"></param><param name="allowscriptaccess" value="always"></param>\
<embed src="http://www.youtube.com/v/%(#)s&hl=ru&fs=1" type="application/x-shockwave-flash"\
allowscriptaccess="always" allowfullscreen="true" width="%(w)d" height="%(h)d"></embed>\
</object>' % {'#': id, 'w': int(params.get('w', 480)), 'h': int(params.get('h', 385))}
    return code


def embed_vimeo(id, params):
    """
    Produces embedding code for Vimeo.
    """
    code = '<object width="%(w)d" height="%(h)d"><param name="allowfullscreen" value="true" />\
<param name="allowscriptaccess" value="always" />\
<param name="movie" value="http://vimeo.com/moogaloop.swf?clip_id=%(#)s&amp;\
server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=0&amp;\
color=&amp;fullscreen=1" />\
<embed src="http://vimeo.com/moogaloop.swf?clip_id=%(#)s&amp;\
server=vimeo.com&amp;show_title=1&amp;show_byline=1&amp;show_portrait=0&amp;\
color=&amp;fullscreen=1" type="application/x-shockwave-flash" allowfullscreen="true"\
allowscriptaccess="always" width="%(w)d" height="%(h)d"></embed>\
</object>' % {'#': id, 'w': int(params.get('w', 500)), 'h': int(params.get('h', 375))}
    return code


def embed_swf(formatter, params):
    """
    Produces embedding code for SWF by url.
    """
    url = params['swf']
    
    # url for attachment
    if url[0] != '/' and url[0:7] != 'http://' and url[0:8] != 'https://':
        if url[:11] != 'attachment:':
            url = 'attachment:%s' % url
        url = extract_link(formatter.env, formatter.context, '[%s attachment]' % url)
        url = '/raw-' + url.attrib.get('href')[1:]
    
    # embed code
    code = '<object width="%(w)s" height="%(h)s">\
<param name="movie" value="%(url)s"></param>\
<param name="allowFullScreen" value="false"></param><param name="allowscriptaccess" value="always"></param>\
<embed src="%(url)s" type="application/x-shockwave-flash"\
allowscriptaccess="always" allowfullscreen="false" width="%(w)s" height="%(h)s"></embed>\
</object>' % {'url': url, 'w': params.get('w', '100%'), 'h': params.get('h', '100%')}

    return code