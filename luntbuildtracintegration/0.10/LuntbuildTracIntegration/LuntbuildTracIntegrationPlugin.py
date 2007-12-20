
import MySQLdb
import time
import datetime
from trac.core import *
from trac.config import Option
from trac.util import Markup
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.Timeline import ITimelineEventProvider

class LuntbuildTracIntegrationPlugin(Component):

    implements(INavigationContributor, ITimelineEventProvider, ITemplateProvider)
    
    # Options
    
    
    db_host = Option('luntbuild', 'db_host', 'localhost', """The MySQL database host to connect to""")
    db_name = Option('luntbuild', 'db_name', 'luntbuild', """The MySQL database instance to connect to""")
    db_user = Option('luntbuild', 'db_user', 'luntbuild', """The user to connect as""")
    db_password = Option('luntbuild', 'db_password', 'luntbuild', """The password for the user""")
    base_url = Option('luntbuild', 'base_url', '/luntbuild', """The Base URL to luntbuild""")
    
    
    # INavigationContributor methods

    def get_active_navigation_item(self, req):
        return 'builds'

    def get_navigation_items(self, req):
        return []
        
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [self.env.get_templates_dir(),
                self.config.get('trac', 'templates_dir')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('LuntTrac', resource_filename(__name__, 'htdocs'))]        
        
    # ITimelineEventProvider methods
        
    def get_timeline_filters(self, req):
        if req.perm.has_permission('CHANGESET_VIEW'):
            yield ('build', 'Builds')

    def get_timeline_events(self, req, start, stop, filters):
        if 'build' in filters:
            add_stylesheet(req, 'LuntTrac/lunttrac.css')
            
            format = req.args.get('format')
            
            # connect to MySQL
            connection = MySQLdb.connect(host=self.config.get('luntbuild', 'db_host'), 
                                         user=self.config.get('luntbuild', 'db_user'), 
                                         passwd=self.config.get('luntbuild', 'db_password'), 
                                         db=self.config.get('luntbuild', 'db_name') )
        
        
            cursor = connection.cursor()
            query =  """
                SELECT p.name, b.status, b.version, b.id, b.end_date, b.start_date
                FROM lb_project p,
                     lb_build b,
                     lb_schedule s
                WHERE p.id = s.fk_project_id
                  AND s.id = b.fk_schedule_id
                  AND end_date > '%s'
                  AND end_date < '%s'
                ORDER BY end_date DESC;
                """ % (self.float2datetime(start).isoformat(' '), 
                       self.float2datetime(stop).isoformat(' '))
            cursor.execute(query)
            
            base_url = self.config.get('luntbuild', 'base_url')
                        
            for build in cursor:
                
                success = ''
                if build[1] == 1:
                    success = 'build successful'  
                    kind = 'build-successful'
                elif build[1] == 3:
                    success = 'build in progress'  
                    kind = 'build-inprogress'
                else:
                    success = 'build failed'  
                    kind = 'build-failed'
                
                href = base_url + "/app.do?service=direct/1/Home/builds.buildListComponent.$DirectLink$1&sp=l%d" % build[3]
                title = Markup("<em>%s</em>" % (build[2]))
                comment = success + ", took " + str(build[4] - build[5])
                completed = build[4]
                
                #if format == 'rss':
                #else:
                
                yield kind, href, title, self.datetime2float(completed), None, comment

    def datetime2float(self, thedatetime):
        return  time.mktime(thedatetime.timetuple()) + thedatetime.microsecond / 1e6
        
    def float2datetime(self, thetime):
        return  datetime.datetime.fromtimestamp(thetime)