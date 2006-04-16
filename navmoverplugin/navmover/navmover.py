from trac.core import *
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.util import Markup

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
                        and unicode(item[2]).startswith('<a '):
                    meta_items.append((move_to, item[1], item[2]))

        # Add custom items
        for item, title in [o for o in self.env.config.options('navmover')
                            if '.' not in o[0] and o[0] not in ('move_items', 'move_to')]:
            url = self.env.config.get('navmover', '%s.url' % item)
            perm = self.env.config.get('navmover', '%s.permission' % item)
            if perm and not req.perm.has_permission(perm):
                continue
            meta_items.append((move_to, item, Markup('<a href="%s">%s</a>' % (url, title))))
        return meta_items

    # ITemplateProvider methods
    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('navmover', resource_filename(__name__, 'htdocs'))]

    def get_templates_dirs(self):
        return []
