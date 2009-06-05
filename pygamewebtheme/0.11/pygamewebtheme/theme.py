# Created by Noah Kantrowitz on 2009-06-02.
# Copyright (c) 2007 Noah Kantrowitz. All rights reserved.

from trac.core import *

from themeengine.api import ThemeBase

class PygamewebTheme(ThemeBase):
    """A theme for Trac based on the new http://pygame.org/."""

    template = htdocs = css = screenshot = True
    
    colors = [
        ('text', 'color', 'body, .milestone .info h2 *:link, .milestone .info h2 *:visited'),
        ('menubar_bg', 'background-color', '#menubar'),
        ('menubar_text', 'color', '#menubar a'),
        ('menubar_hover', 'color', '#menubar a:hover'),
        ('submenu_bg', 'background-color', '#submenu, #menubar a.active'),
        ('submenu_text', 'color', '#submenu a'),
        ('submenu_hover', 'color', '#submenu a:hover'),
        ('submenu_active', 'color', '#submenu .active :link, #submenu .active :visited')
    ]
    
    schemes = [
        ('default', {
            'text': '#000000',
            'menubar_bg': '#2E2E2E',
            'menubar_text': '#CCFF00',
            'menubar_hover': '#FFFFFF',
            'submenu_bg': '#4CCC00',
            'submenu_text': '#FFFFFF',
            'submenu_hover': '#666666',
            'submenu_active': '#000000',
        }),
    ]

class PygamewebRetroTheme(ThemeBase):
    """A theme for Trac based on the new http://pygame.org/."""
    
    template = htdocs = css = True
    
    #disable_trac_css = True