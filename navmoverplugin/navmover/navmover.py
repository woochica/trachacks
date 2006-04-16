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
        move_to = self.env.config.get('navmover', 'move_to') or 'metanav'
        move_items = self.env.config.get('navmover', 'move_items', ''). \
                     replace(',', ' ').split()
        self.env.log.debug(move_items)
        # Ensure sanity
        if move_to not in ('mainnav', 'metanav'):
            move_to = 'mainnav'
        if move_to == 'mainnav':
            move_from = 'metanav'
        else:
            move_from = 'mainnav'
        # Hide the appropriate nav block
        add_stylesheet(req, 'navmover/css/hide_%s.css' % move_from)
        # Find meta nav items
        meta_items = []
        for contributor in self.nav_contributors:
            if contributor == self: continue
            for item in contributor.get_navigation_items(req):
                if (not move_items or item[1] in move_items) and item[0] == move_from \
                        and not unicode(item[2]).startswith('logged in as'):
                    meta_items.append((move_to, item[1], item[2]))

        return meta_items

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('navmover', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
