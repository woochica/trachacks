# Burndown plugin

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup

class BurndownComponent(Component):
    implements(IEnvironmentSetupParticipant, INavigationContributor, IRequestHandler, ITemplateProvider)
    
    # IEnvironmentSetupParticipant methods
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        result = False
        
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        # See if the burndown table exists, if not, return True
        cursor = db.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='burndown'")
        row = cursor.fetchone()
        if not row:
            result = True
            
        if handle_ta:
            db.commit()
            
        return result

    def upgrade_environment(self, db):
        cursor = db.cursor()
        
        sqlTableCreate =     "CREATE TABLE burndown (" \
                                    "    id integer PRIMARY KEY,"\
                                    "    component_name text NOT NULL,"\
                                    "    milestone_name text NOT NULL," \
                                    "    date integer NOT NULL,"\
                                    "    hours_remaining integer NOT NULL"\
                                    ")"
                                    
        cursor.execute(sqlTableCreate)

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'burndown'
                
    def get_navigation_items(self, req):
        yield 'mainnav', 'burndown', Markup('<a href="%s">Burndown</a>', self.env.href.burndown())

    # IRequestHandler methods
    def match_request(self, req):
        return req.path_info == '/burndown'
    
    def process_request(self, req):
        add_stylesheet(req, 'hw/css/burndown.css')
        return 'burndown.cs', None
        
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        from pkg_resources import resource_filename
        return [resource_filename(__name__, 'templates')]

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
        return [('hw', resource_filename(__name__, 'htdocs'))]