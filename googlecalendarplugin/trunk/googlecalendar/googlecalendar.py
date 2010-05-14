from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider
from pkg_resources import resource_filename

class GoogleCalendar(Component):
    implements(INavigationContributor, IRequestHandler, ITemplateProvider)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'calendar'
    def get_navigation_items(self, req):
        yield ('mainnav', 'calendar',
            html.A('Calendar', href= req.href.calendar()))

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == "/calendar"

    def process_request(self, req):
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

