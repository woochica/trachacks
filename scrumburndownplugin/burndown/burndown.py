# Burndown plugin
# Copyright (C) 2006 Sam Bloomquist <spooninator@hotmail.com>
# All rights reserved.
# vi: et ts=4 sw=4
# This software may at some point consist of voluntary contributions made by
# many individuals. For the exact contribution history, see the revision
# history and logs, available at http://projects.edgewall.com/trac/.
#
# Author: Sam Bloomquist <spooninator@hotmail.com>

import time
import sys

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, format_date

class BurndownComponent(Component):
    implements(IEnvironmentSetupParticipant, INavigationContributor,
                    IRequestHandler, ITemplateProvider, IPermissionRequestor)
    
    #---------------------------------------------------------------------------
    # IEnvironmentSetupParticipant methods
    #---------------------------------------------------------------------------
    def environment_created(self):
        pass

    def environment_needs_upgrade(self, db):
        needsUpgrade = False
        
        #get a database connection if we don't already have one
        if not db:
            db = self.env.get_db_cnx()
            handle_ta = True
        else:
            handle_ta = False
            
        # See if the burndown table exists, if not, return True because we need to upgrade the database
        # the latest version of the burndown table contains a 'week' column
        cursor = db.cursor()
        try:
            cursor.execute('SELECT week FROM burndown LIMIT 1')
        except:
            needsUpgrade = True
            
        if handle_ta:
            db.commit()
            
        return needsUpgrade

    def upgrade_environment(self, db):
        cursor = db.cursor()
        
        needsCreate = False
        try:
            cursor.execute('SELECT * FROM burndown LIMIT 1')
        except:
            needsCreate = True
            
        if needsCreate:
            print >> sys.stderr, 'Attempting to create the burndown table'
            # Create the burndown table in the database
            sqlBurndownCreate = "CREATE TABLE burndown (" \
                                            "    id integer PRIMARY KEY NOT NULL,"\
                                            "    component_name text NOT NULL,"\
                                            "    milestone_name text NOT NULL," \
                                            "    date text,"\
                                            "    week text,"\
                                            "    year text,"\
                                            "    hours_remaining integer NOT NULL"\
                                            ")"
                                        
            cursor.execute(sqlBurndownCreate)
        else:
            print >> sys.stderr, 'Attempting to modify the burndown table'
            #burndown table already exists, just need to add week and year columns
            sqlBurndown = [
            """CREATE TEMP TABLE burndown_old as SELECT * FROM burndown;""",
            """DROP TABLE burndown;""",
            """CREATE TABLE burndown (
                    id integer PRIMARY KEY NOT NULL,
                    component_name text NOT NULL,
                    milestone_name text NOT NULL,
                    date text,
                    week text,
                    year text,
                    hours_remaining integer NOT NULL
                );""",
            """INSERT INTO burndown(id,component_name,milestone_name,date,hours_remaining)
            SELECT id,component_name,milestone_name,date,hours_remaining FROM burndown_old;"""
            ]
            for line in sqlBurndown:
                cursor.execute(line)
        
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
    # IPermissionRequestor methods
    #---------------------------------------------------------------------------
    def get_permission_actions(self):
        return ["BURNDOWN_VIEW", "BURNDOWN_ADMIN"]

    #---------------------------------------------------------------------------
    # IRequestHandler methods
    #---------------------------------------------------------------------------
    def match_request(self, req):
        return req.path_info == '/burndown'
    
    def process_request(self, req):
        req.perm.assert_permission('BURNDOWN_VIEW')
        
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
        
        if (milestones and milestones[0]):
            selected_milestone = req.args.get('selected_milestone', milestones[0])
        else:
            selected_milestone = ''
        selected_component = req.args.get('selected_component', 'All Components')
        
        # expose display data to the clearsilver templates
        req.hdf['milestones'] = milestones
        req.hdf['components'] = components
        req.hdf['selected_milestone'] = selected_milestone
        req.hdf['selected_component'] = selected_component
        req.hdf['draw_graph'] = False
        req.hdf['start'] = False
        
        if req.perm.has_permission("BURNDOWN_ADMIN"):
            req.hdf['start'] = True # show the start and complete milestone buttons to admins
        
        if req.args.has_key('start'):
            self.startMilestone(db, selected_milestone)
        else:
            req.hdf['draw_graph'] = True
            req.hdf['burndown_data'] = self.getBurndownData(db, selected_milestone, components, selected_component) # this will be a list of (id, hours_remaining) tuples
        
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
            
        if len(component_data) > 0 and component_data[component_data.keys()[0]]:
            burndown_length = len(component_data[component_data.keys()[0]])
        else:
            burndown_length = 0
        burndown_data = []
        if selected_component == 'All Components':
            for time_unit in range (0, burndown_length): #burndown can be incremented in days or weeks, so I decided to use the generic 'time_unit'
                sumHours = 0
                for comp in components:
                    self.log.debug('component: %s', comp);
                    self.log.debug('time_unit: %i', time_unit);
                    if (component_data[comp] and len(component_data[comp]) > time_unit):
                        sumHours += component_data[comp][time_unit][1]
                
                burndown_data.append((time_unit+1, sumHours))
                
        else:
            for time_unit in range (0, len(component_data[selected_component])):
                burndown_data.append((time_unit+1, component_data[selected_component][time_unit][1]))
            
        return burndown_data
        
    def startMilestone(self, db, milestone):
        cursor = db.cursor()
        cursor.execute("SELECT started FROM milestone WHERE name = '%s'" % milestone)
        row = cursor.fetchone()
        if row and row[0] > 0:
            raise TracError("Milestone '%s' was already started on %s" % (milestone, format_date(int(row[0]))))
            
        cursor.execute("UPDATE milestone SET started = %i WHERE name = '%s'" % (int(time.time()), milestone))
        
        db.commit()
        
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
