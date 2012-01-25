# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Franz Mayer <franz.mayer@gefasoft.de>
#
# "THE BEER-WARE LICENSE" (Revision 42):
# <franz.mayer@gefasoft.de> wrote this file.  As long as you retain this 
# notice you can do whatever you want with this stuff. If we meet some day, 
# and you think this stuff is worth it, you can buy me a beer in return. 
# Franz Mayer
#
# Author: Franz Mayer <franz.mayer@gefasoft.de>

from trac.core import Component, implements
from trac.util.translation import domain_functions
from trac.web.chrome import ITemplateProvider
from trac.prefs.api import IPreferencePanelProvider
from pkg_resources import resource_filename #@UnresolvedImport
from navigation import Navigation

_, tag_, N_, add_domain = \
    domain_functions('navigationplugin', '_', 'tag_', 'N_', 'add_domain')


class NavigationPreferences(Component):
    """This Component enables user to set her / his prefered navigation 
display."""
    implements(IPreferencePanelProvider, ITemplateProvider)

    def __init__(self):
        # bind the 'tracnav' catalog to the locale directory 
        locale_dir = resource_filename(__name__, 'locale') 
        add_domain(self.env.path, locale_dir)    
        
    ## IPreferencePanelProvider methods

    def get_preference_panels(self, req):
#        if req.authname and req.authname != 'anonymous':
            yield 'navigation', _("Navigation")

    def render_preference_panel(self, req, panel):
        nav = Navigation(self.env)
        if panel == 'navigation':
            nav.save(req)
        selected = {'display_nav': nav.get_display(req),
                    'wiki.href': nav.get_wiki_href(req)}
        nav_choices = nav.get_display_choices()
#        session_keys = nav.get_session_keys()
        system_defaults = {'display_nav': nav.get_system_default_display(), 
                           'wiki.href': nav.get_system_default_wiki_href()}
        
        data = {'selected': selected,
                'nav_choices': nav_choices,
#                'session_keys': session_keys,
                'system_defaults': system_defaults}
        return 'prefs_display.html', data
        

    # ITemplateProvider methods
    
    def get_htdocs_dirs(self):
        """Return the absolute path of a directory containing additional
        static resources (such as images, style sheets, etc).
        """
        return []

    def get_templates_dirs(self):
        """Return the absolute path of the directory containing the provided
        Genshi templates.
        """
        return [resource_filename(__name__, 'templates')]