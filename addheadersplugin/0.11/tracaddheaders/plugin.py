# -*- coding: utf-8 -*-
""" Copyright (c) 2008 Martin Scharrer <martin@scharrer-online.de>
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
from  trac.web.chrome  import  add_link,add_stylesheet,add_script

class AddHeadersPlugin(Component):
    implements(IRequestFilter)
    """ Provides a plugin to insert header tags into trac pages.

        This plugin is limited to the features of the methods
        add_link, add_stylesheet and add_script from trac.web.chrome,
        so not all valid (X)HTML attributes can be set.
    """

    def pre_process_request(self, req, handler):
        return handler

    def post_process_request(self, req, template, data, content_type):
        config        = self.env.config
        section       = 'addheaders'

        default_base        = config.get(section, 'default_base', 'site/')
        default_script_base = config.get(section, 'default_script_base', default_base)
        default_style_base  = config.get(section, 'default_style_base',  default_base)

        links         = config.getlist(section, 'add_links')
        stylesheets   = config.getlist(section, 'add_styles')
        scripts       = config.getlist(section, 'add_scripts')


        for link in links:
            rel       = config.get(section, link       + '.rel'   )
            href      = config.get(section, link       + '.href'  )
            title     = config.get(section, link       + '.title' )
            mimetype  = config.get(section, link       + '.type'  )
            classname = config.get(section, link       + '.class' )

            if rel and href:
                add_link(req, rel, href, title or None, mimetype or None, classname or None)


        for stylesheet in stylesheets:
            filename  = config.get(section, stylesheet + '.filename', default_style_base + stylesheet + '.css' )
            mimetype  = config.get(section, stylesheet + '.mimetype', 'text/css')

            if filename:
                add_stylesheet(req, filename, mimetype)


        for script in scripts:
            filename  = config.get(section, script     + '.filename', default_script_base + script + '.js' )
            mimetype  = config.get(section, script     + '.mimetype', 'text/javascript')

            if filename:
                add_script(req, filename, mimetype)


        return (template, data, content_type)

