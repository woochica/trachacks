from datetime import date
from genshi.builder import tag

from trac.core import *
from trac.config import BoolOption, Option
from trac.resource import Resource
from trac.ticket import Version
from trac.util.datefmt import get_datetime_format_hint, parse_date
from trac.util.translation import _
#from trac.web.chrome import add_link, add_notice, add_stylesheet, add_warning
from trac.web.chrome import add_stylesheet

### interfaces:  
from trac.web.api import IRequestHandler
from trac.web.chrome import INavigationContributor

from version import VisibleVersion


class ReleasesModule(Component):
    implements(INavigationContributor, IRequestHandler)

    navigation = BoolOption('extended_version', 'roadmap_navigation', 'false',
        doc="""Whether to add a link to the main navigation bar.""")
    navigation_item = Option('extended_version', 'navigation_item', 'roadmap',
        doc="""The name for the navigation item to highlight.
        
        May be set to 'roadmap' to highlight the navigation provided by the core
        ticket module. If roadmap_navigation is also set to true, this completely
        replaces the main navigation for the core roadmap.""")
    show_tickets_in_overview = BoolOption('extended_version', 'show_tickets_in_overview', True,
        """whether to display the ticket bars in the version overview page.""")
    show_milestones_in_overview = BoolOption('extended_version', 'show_milestones_in_overview', False,
        """whether to display milestone information in the overview page.""")
        

    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return self.navigation_item

    def get_navigation_items(self, req):
        if self.navigation and 'VERSION_VIEW' in req.perm:
            yield ('mainnav', self.navigation_item,
                               tag.a(_('Versions'), href=req.href.versions()))

    # IRequestHandler methods

    def match_request(self, req):
        return '/versions' == req.path_info
        #match = re.match(r'/versions$', req.path_info)
        #if match:
        #    return True

    def process_request(self, req):
        req.perm.require('VERSION_VIEW')

        showall = req.args.get('show') == 'all'
        version_component = self.env[VisibleVersion]
        milestone_stats_provider = version_component.milestone_stats_provider
        version_stats_provider = version_component.version_stats_provider

        db = self.env.get_db_cnx()
        versions = []
        resources = []
        is_released = []
        version_datasets = []
        for v in Version.select(self.env, db):
            r = Resource('version', v.name)
            ir = v.time and v.time.date() < date.today()

            # apply more visibility
            if (showall or not ir) and 'VERSION_VIEW' in req.perm(r):
                versions.append(v)
                resources.append(r)
                is_released.append(v.time and v.time.date() < date.today())
                
                version_data = version_component.get_version_data(req, db, v)
                version_datasets.append(version_data)
                

        versions.reverse(),
        resources.reverse(),
        is_released.reverse(),
        version_datasets.reverse(),

        add_stylesheet(req, 'extendedversion/css/extendedversion.css')

        data = {
            'versions': versions,
            'resources': resources,
            'is_released': is_released,
            'showall': showall,
            'show_tickets_in_overview' : self.show_tickets_in_overview,
            'show_milestones_in_overview' : self.show_milestones_in_overview,
            'version_datasets' : version_datasets,
        }
        return 'versions.html', data, None
