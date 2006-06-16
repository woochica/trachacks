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
        sqlTableCreate =     "CREATE TABLE burndown (" \
                                    "    id integer PRIMARY KEY NOT NULL,"\
                                    "    component_name text NOT NULL,"\
                                    "    milestone_name text NOT NULL," \
                                    "    date text NOT NULL,"\
                                    "    hours_remaining integer NOT NULL"\
                                    ")"
                                    
        cursor.execute(sqlTableCreate)
        
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
        milestones = cursor.fetchall()
        for mile in milestones:
            self.env.log.debug(mile[0])
        cursor.execute("SELECT name FROM component")
        components = cursor.fetchall()
        #for comp in components:
        #    print comp
        
        draw = req.args.get('draw', None)
        milestone = req.args.get('selected_milestone')
        
        if draw and milestone:
            req.hdf['selected_milestone'] = milestone
            req.hdf['burndown_entries'] = getBurndownForMilestone(milestone)
        
        add_stylesheet(req, 'hw/css/burndown.css')
        return 'burndown.cs', None
        
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