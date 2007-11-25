# NikoNiko plugin
# Copyright (C) 2007 Brett Smith
# All rights reserved.
#
# Author: Brett Smith <brett@3sp.com>

import time
import sys
import datetime

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.perm import IPermissionRequestor
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.main import IRequestHandler
from trac.util import escape, Markup, format_date

class NikoNikoComponent(Component):
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
            cursor.execute('SELECT nikoniko_username FROM nikoniko LIMIT 1')
        except:
            needsUpgrade = True
            
        if handle_ta:
            db.commit()
            
        return needsUpgrade

    def upgrade_environment(self, db):
        cursor = db.cursor()
        
        needsCreate = False
        try:
            cursor.execute('SELECT * FROM nikoniko LIMIT 1')
        except:
            needsCreate = True
            
        if needsCreate:
            print >> sys.stderr, 'Attempting to create the niko table'
            sqlCreate = "CREATE TABLE nikoniko ( " \
               "nikoniko_username text NOT NULL, "\
               "nikoniko_date date NOT NULL, "\
               "nikoniko_mood text NOT NULL, "\
               "nikoniko_comment text NOT NULL, "\
               "PRIMARY KEY ( nikoniko_username,nikoniko_date ) "\
               ")"
            cursor.execute(sqlCreate)

    #---------------------------------------------------------------------------
    # INavigationContributor methods
    #---------------------------------------------------------------------------
    def get_active_navigation_item(self, req):
        return 'nikoniko'
                
    def get_navigation_items(self, req):
        if not req.perm.has_permission('NIKONIKO_VIEW'):
            return
        yield 'mainnav', 'nikoniko', Markup('<a href="%s">NikoNiko</a>', self.env.href.nikoniko())
        
    #---------------------------------------------------------------------------
    # IPermissionRequestor methods
    #---------------------------------------------------------------------------
    def get_permission_actions(self):
        return ["NIKONIKO_VIEW","NIKONIKO_CHANGE"]

    #---------------------------------------------------------------------------
    # IRequestHandler methods
    #---------------------------------------------------------------------------
    def match_request(self, req):
        return req.path_info == '/nikoniko' or req.path_info == '/login/nikoniko' 
    
    def process_request(self, req):
        req.perm.assert_permission('NIKONIKO_VIEW')
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()
        now = datetime.datetime.now()
        date_time = str(now.date())
        username = req.authname;
        
        # Get current mood
        getMoodSQL = "SELECT nikoniko_mood,nikoniko_comment FROM nikoniko WHERE "\
                     "nikoniko_username = %s AND "\
                     "nikoniko_date = %s "
        cursor.execute(getMoodSQL, (username,date_time) )
        row = cursor.fetchone()
        if row and row[0] > 0:
            todays_mood = row[0]
            comment = row[1]
            new_mood = False
        else:
            todays_mood = 'okMood'
            comment = 'Feeling Average'
            new_mood = True
        
        # Decide if an an update is needed
        do_update = False        
        if req.args.has_key('badMood'):
            do_update = True
            todays_mood = 'badMood'
        if req.args.has_key('okMood'):
            do_update = True
            todays_mood = 'okMood'
        if req.args.has_key('goodMood'):
            do_update = True
            todays_mood = 'goodMood'
        if req.args.has_key("comment"):            
        # TODO prevent SQL injection
            comment = req.args["comment"]
            do_update = True
            
        if do_update:
            self.update_mood(req, todays_mood, comment, username, now, new_mood)
            
        # Calendar
        self.build_calendar(req, cursor)
            
        # Make variables available to template
    
        req.hdf['username'] = username
        req.hdf['comment'] = comment
        req.hdf['todays_mood'] = todays_mood
        req.hdf['date_time'] = date_time
        req.hdf['can_change'] = req.perm.has_permission('NIKONIKO_CHANGE')  

        add_stylesheet(req, 'nn/css/nikoniko.css')
        return 'nikoniko.cs', None
    
    def build_calendar(self, req, cursor):
        
        # The user may have requested a different week
        if req.args.has_key('date'):
            calendar_date = datetime.datetime(*time.strptime(req.args['date'], '%d/%m/%y')[0:5])
        else:
            calendar_date = datetime.datetime.now()

        # Work out the start and end of week
        start_of_week = calendar_date 
        while start_of_week.weekday() != 0:
            start_of_week = start_of_week - datetime.timedelta(days=1) 

        end_of_week = calendar_date 
        while end_of_week.weekday() != 6:
            end_of_week = end_of_week + datetime.timedelta(days=1)
            
        # Work out last week and next week for calendar navigation
        last_week = start_of_week - datetime.timedelta(weeks=1)
        next_week = end_of_week + datetime.timedelta(days=1)
          
        # Work out all the days that will be displayed
        days = []
        week_date = start_of_week
        while week_date <= end_of_week:
            days.append(week_date.strftime("%A"))
            week_date = week_date + datetime.timedelta(days=1) 

        # Get all users
        getUsersSQL = "SELECT DISTINCT nikoniko_username FROM nikoniko"
        cursor.execute(getUsersSQL)
        user_list = cursor.fetchall() 
        users= []
        for user in user_list:
            users.append(user[0])

        # Get the mood of each user, per day
        mood_data = {}
        comment_data = {}
        getMoodsSQL = "SELECT nikoniko_username,nikoniko_date,nikoniko_mood,nikoniko_comment "\
            "FROM nikoniko WHERE "\
            "nikoniko_date >= %s "\
            "AND "\
            "nikoniko_date <= %s "
        cursor.execute(getMoodsSQL, ( str(start_of_week.date()), str( end_of_week.date() ) ) )
        niko_data = cursor.fetchall()
        for row in niko_data:
            username = row[0]
            mood_date = row[1]
            mood = row[2]
            comment = row[3]
            
            if not mood_data.has_key(username):
               week_data = {}
               week_comment_data = {}
               mood_data[username] = week_data
               comment_data[username] = week_comment_data
               
            mood_data[username][mood_date.strftime("%A")] = mood
            comment_data[username][mood_date.strftime("%A")] = comment
            
        # Make variables available to template
        
        req.hdf['mood_data'] = mood_data; 
        req.hdf['comment_data'] = comment_data;
        req.hdf['last_week'] = last_week.strftime("%d/%m/%y")
        req.hdf['next_week'] = next_week.strftime("%d/%m/%y")
        req.hdf['start_of_week'] = start_of_week.strftime("%d/%m/%y")
        req.hdf['end_of_week'] =  end_of_week.strftime("%d/%m/%y")
        req.hdf['days'] = days 
        req.hdf['users'] = users
        
    def update_mood(self, req, todays_mood, comment, username, date_time, new_mood):
        req.perm.assert_permission('NIKONIKO_CHANGE')
        
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        cursor = db.cursor()
        if new_mood:
            changeMoodSQL = "INSERT INTO nikoniko ("\
                         "nikoniko_username,nikoniko_date,nikoniko_mood,nikoniko_comment) "\
                         "VALUES ( %s,"\
                         " %s,"\
                         " %s, %s )"
            cursor.execute(changeMoodSQL, (username, str(date_time.date()), todays_mood, comment ) )
        else: 
            changeMoodSQL = "UPDATE nikoniko SET nikoniko_mood = "\
                            " %s, nikoniko_comment = "\
                            " %s WHERE "\
                            "nikoniko_username = %s AND "\
                            "nikoniko_date = "\
                            " %s "
            cursor.execute(changeMoodSQL, ( todays_mood, comment, username, str(date_time.date()) ) )
        db.commit()

        return todays_mood
        
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
        return [('nn', resource_filename(__name__, 'htdocs'))]
