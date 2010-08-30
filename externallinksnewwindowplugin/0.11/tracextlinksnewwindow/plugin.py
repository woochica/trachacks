# -*- coding: utf-8 -*-
""" Copyright (c) 2008-2009 Martin Scharrer <martin@scharrer-online.de>
    $Id$
    $URL$

    This is Free Software under the GPL v3!
"""

__url__      = ur"$URL$"[6:-2]
__author__   = ur"$Author$"[9:-2]
__revision__ = int("0" + ur"$Rev$"[6:-2])
__date__     = ur"$Date$"[7:-2]

from  trac.core        import  Component, implements
from  trac.web.api     import  IRequestFilter
from  trac.web.chrome  import  ITemplateProvider, add_stylesheet, add_script

class ExtLinksNewWindowPlugin(Component):
    """Opens external links in new window

       `$Id$`
    """
    implements ( IRequestFilter, ITemplateProvider )

    # ITemplateProvider#get_htdocs_dirs
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('extlinksnewwindow', resource_filename(__name__, 'htdocs'))]

    # ITemplateProvider#get_templates_dirs
    def get_templates_dirs(self):
        return []


    # IRequestFilter#pre_process_request
    def pre_process_request(self, req, handler):
        return handler

    # IRequestFilter#post_process_request
    def post_process_request(self, req, template, data, content_type):
        add_script(req, 'extlinksnewwindow/extlinks.js')
        return (template, data, content_type)

