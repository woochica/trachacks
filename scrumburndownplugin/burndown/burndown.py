# Burndown plugin
# Copyright (C) 2006 Sam Bloomquist <spooninator@hotmail.com>
# All rights reserved.
#
# This software may at some point consist of voluntary contributions made by
# many individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Sam Bloomquist <spooninator@hotmail.com>

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup

class BurndownComponent(Component):
    implements(IEnvironmentSetupParticipant, INavigationContributor, IRequestHandler, ITemplateProvider)
    
    #---------------------------------------------------------------------------
    # IEnvironmentSetupParticipant methods
    #---------------------------------------------------------------------------
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        result = False
        
        #get a database connection if we don't already have one
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        # See if the burndown table exists, if not, return True because we need to upgrade the database
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
        
        # Create the burndown table in the database
        sqlBurndownCreate =     "CREATE TABLE burndown (" \
                                    "    id integer PRIMARY KEY NOT NULL,"\
                                    "    component_name text NOT NULL,"\
                                    "    milestone_name text NOT NULL," \
                                    "    date text NOT NULL,"\
                                    "    hours_remaining integer NOT NULL"\
                                    ")"
                                    
        cursor.execute(sqlBurndownCreate)
        
        sqlMilestone = [
        #-- Add the 'started' column to the milestone table
        """CREATE TEMP TABLE milestone_old AS SELECT * FROM milestone;""",
        """DROP TABLE milestone;""",
        """CREATE TABLE milestone (
                 name            text PRIMARY KEY,
                 due             integer, -- Due date/time
                 completed       integer, -- Completed date/time
                 started        integer, -- Started date/time
                 description     text
        );""",
        """INSERT INTO milestone(name,due,completed,started,description)
        SELECT name,due,completed,0,description FROM milestone_old;"""
        ]
        for s in sqlMilestone:
            cursor.execute(s)

    #---------------------------------------------------------------------------
    # INavigationContributor methods
    #---------------------------------------------------------------------------
    def get_active_navigation_item(self, req):
        return 'burndown'
                
    def get_navigation_items(self, req):
        yield 'mainnav', 'burndown', Markup('<a href="%s">Burndown</a>', self.env.href.burndown())

    #---------------------------------------------------------------------------
    # IRequestHandler methods
    #---------------------------------------------------------------------------
    def match_request(self, req):
        return req.path_info == '/burndown'
    
    def process_request(self, req):
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        
        cursor.execute("SELECT name FROM milestone")
        milestone_lists = cursor.fetchall()
        milestones = []
        for mile in milestone_lists:
            milestones.append(mile[0])
            
        cursor.execute("SELECT name FROM component")
        component_lists = cursor.fetchall()
        components = []
        for comp in component_lists:
            components.append(comp[0])
        
        selected_milestone = req.args.get('selected_milestone', milestones[0])
        selected_component = req.args.get('selected_component', 'All Components')

        # expose display data to the clearsilver templates
        req.hdf['milestones'] = milestones
        req.hdf['components'] = components
        req.hdf['burndown_data'] = self.getBurndownData(db, selected_milestone, components, selected_component) # this will be a list of (id, hours_remaining) tuples
        req.hdf['selected_milestone'] = selected_milestone
        req.hdf['selected_component'] = selected_component
        
        self.env.log.debug(selected_component)
        self.env.log.debug(self.getBurndownData(db, selected_milestone, components, selected_component))
        
        add_stylesheet(req, 'hw/css/burndown.css')
        return 'burndown.cs', None
        
    def getBurndownData(self, db, selected_milestone, components, selected_component):
        cursor = db.cursor()
        
        component_data = {} # this will be a dictionary of lists of tuples -- e.g. component_data = {'componentName':[(id, hours_remaining), (id, hours_remaining), (id, hours_remaining)]}
        for comp in components:
            if selected_component == 'All Components' or comp == selected_component:
                sqlBurndown = "SELECT id, hours_remaining "\
                                    "FROM burndown "\
                                    "WHERE milestone_name = '" + selected_milestone + "' AND component_name = '" + comp + "' "\
                                    "ORDER BY id"
                
                cursor.execute(sqlBurndown)
                component_data[comp] = cursor.fetchall()
            
        burndown_length = len(component_data[component_data.keys()[0] ])
        burndown_data = []
        if selected_component == 'All Components':
            for day in range (0, burndown_length):
                sumHours = 0
                for comp in components:
                    sumHours += component_data[comp][day][1]
                
                burndown_data.append((day+1, sumHours))
                
        else:
            for day in range (0, len(component_data[selected_component])):
                burndown_data.append((day+1, component_data[selected_component][day][1]))
            
        return burndown_data
        
    #---------------------------------------------------------------------------
    # ITemplateProvider methods
    #---------------------------------------------------------------------------
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