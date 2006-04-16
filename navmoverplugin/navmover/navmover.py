from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet

class NavMover(Component):
    """ Moves meta navigation items into the main navigation bar. """
    implements(INavigationContributor, ITemplateProvider)

    nav_contributors = ExtensionPoint(INavigationContributor)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return ''
                
    def get_navigation_items(self, req):
        # Hide meta nav items
        add_stylesheet(req, 'navmover/css/navmover.css')
        move_items = self.env.config.get('navmover', 'meta_to_main', ''). \
                     replace(',', ' ').split()
        # Find meta nav items
        meta_items = []
        for contributor in self.nav_contributors:
            if contributor == self: continue
            for item in contributor.get_navigation_items(req):
                if (not move_items or item[1] in move_items) and item[0] == 'metanav' \
                        and not unicode(item[2]).startswith('logged in as'):
                    meta_items.append(('mainnav', item[1], item[2]))

        return meta_items

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('navmover', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
