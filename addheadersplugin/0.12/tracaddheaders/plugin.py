# -*- coding: utf-8 -*-
""" Copyright (c) 2008-2011 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $HeadURL$

    This is Free Software under the GPL v3!
""" 

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + r"$Rev$"[6:-2])
__date__     = r"$Date$"[7:-2]

from  trac.core        import  *
from  trac.web.api     import  IRequestFilter
from  trac.web.chrome  import  add_link, add_stylesheet, add_script
try:
    from trac.web.chrome import add_meta
except:
    pass

from  trac.config      import  Option, ListOption


class AddHeadersPlugin(Component):
    """ Provides a plugin to insert header tags into trac pages.

        This plugin is limited to the features of the methods
        add_link, add_stylesheet and add_script from trac.web.chrome,
        so not all valid (X)HTML attributes can be set.
    """
    implements(IRequestFilter)

    section = 'addheaders'

    default_base        = Option(section, 'default_base', 'site/')
    default_script_base = Option(section, 'default_script_base', default_base)
    default_style_base  = Option(section, 'default_style_base',  default_base)
    default_meta_lang   = Option(section, 'default_meta_lang',  None)

    links         = ListOption(section, 'add_links')
    stylesheets   = ListOption(section, 'add_styles')
    scripts       = ListOption(section, 'add_scripts')
    metas         = ListOption(section, 'add_metas')

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        get = self.env.config.get

        for link in self.links:
            rel       = get(self.section, link + '.rel'   )
            href      = get(self.section, link + '.href'  )
            title     = get(self.section, link + '.title' )
            mimetype  = get(self.section, link + '.type'  )
            classname = get(self.section, link + '.class' )

            if rel and href:
                add_link(req, rel, href, title or None, mimetype or None, classname or None)


        for stylesheet in self.stylesheets:
            filename  = get(self.section, stylesheet + '.filename', unicode(self.default_style_base) + stylesheet + '.css' )
            mimetype  = get(self.section, stylesheet + '.mimetype', 'text/css')

            if filename:
                add_stylesheet(req, filename, mimetype)


        for script in self.scripts:
            filename  = get(self.section, script     + '.filename', unicode(self.default_script_base) + script + '.js' )
            mimetype  = get(self.section, script     + '.mimetype', 'text/javascript')

            if filename:
                add_script(req, filename, mimetype)

        for meta in self.metas:
            http_equiv = get(self.section, meta      + '.http_equiv', None )
            name       = get(self.section, meta      + '.name', meta )
            scheme     = get(self.section, meta      + '.scheme', None )
            lang       = get(self.section, meta      + '.lang', self.default_meta_lang )
            content    = get(self.section, meta      + '.content', u'' )

            if http_equiv or name or scheme:
                try:
                    add_meta(req, content, http_equiv, name, scheme, lang)
                except:
                    pass

        return (template, data, content_type)

