from trac.core import *
from trac.util.html import html
from trac.perm import PermissionSystem, IPermissionRequestor
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from pkg_resources import resource_filename

class GoogleCalendar(Component):
    implements(INavigationContributor, IRequestHandler, IPermissionRequestor, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'calendar'
    def get_navigation_items(self, req):
	if 'GOOGLECALENDAR_VIEW' in req.perm:
		yield ('mainnav', 'calendar',
				html.A('Calendar', href= req.href.calendar()))


    # IPermissionRequestor methods
    def get_permission_actions(self):
        return ['GOOGLECALENDAR_VIEW']
	    
    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == "/calendar"

    def process_request(self, req):
	req.perm.require('GOOGLECALENDAR_VIEW')	
        req.hdf['title'] = 'Calendar'
	calendar_url = self.config.get('googlecalendar', 'calendar_url')
	if calendar_url == '':
		raise Exception('calendar_url must be defined')

	req.hdf['calendarurl'] = calendar_url

	return 'googlecalendar.cs', None


    # ITemplateProvider methods
    def get_templates_dirs(self):
        """Return a list of directories containing the provided ClearSilver
        templates.
        """
        return [resource_filename(__name__, 'templates')]


    def get_htdocs_dirs(self):
        return []

