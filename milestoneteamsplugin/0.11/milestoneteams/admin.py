# Trac core imports
from trac.core import *
from trac.config import *

# Trac extension point imports
from trac.admin.api import IAdminPanelProvider
from trac.web.chrome import ITemplateProvider

# Trac Administration Panel
class mtAdminPanel(Component):
    """Modifies Trac UI for editing Milestone Teams"""
    
    implements(IAdminPanelProvider, ITemplateProvider)

    def get_admin_panels(self, req):
        """Return a list of our administration panels."""
        perm = req.perm('ticket')
        if 'MILESTONE_MODIFY' in perm or 'TICKET_ADMIN' in perm:
            return ( ( 'ticket', 'Ticket System', 'milestoneteams', 'Milestone Teams' ), )
        return ( )

    def set_milestone_team(self, milestone, manager, members):
        db      = self.env.get_db_cnx()
        cursor  = db.cursor()
        query   = "INSERT OR REPLACE INTO milestone_teams (milestone, username, role, notify) VALUES (%s, %s, %s, %s)"
#        self.log.debug("MilestoneTeams: Saving data... %s" % ( (milestone, manager, members), ))
        
        try:
            for member in members:
                cursor.execute(query, (milestone, member, 0, 1))
            cursor.execute(query, (milestone, manager, 1, 1))
        except Exception, e:
            self.log.error("MilestoneTeams error in admin module: %s" % (e,))
            return False
        
        db.commit()
        db.close()
        return True

    def get_milestone_team(self, milestone=None):
        db          = self.env.get_db_cnx()
        cursor      = db.cursor()
        milestones  = [ ]

#        self.log.debug("MilestoneTeams: Loading data for milestone: '%s'" % (milestone, ))

        try:
            if milestone:
                cursor.execute("SELECT m.name FROM milestone AS m WHERE m.name=%s", (milestone, ))
            else:
                cursor.execute("SELECT m.name FROM milestone AS m WHERE m.completed=0 ORDER BY m.due DESC")
                
            for row in cursor:
                milestones.append({ 'title': row[0], 'manager': "", 'members': [ ],})
            for milestone in milestones:
                cursor.execute("SELECT mt.username, mt.role FROM milestone_teams AS mt WHERE mt.milestone=%s AND mt.notify > %s", (milestone['title'], 0))
                for row in cursor:
                    if row[1] > 0:
                        milestone['manager'] = row[0]
                    else:
                        milestone['members'].append(row[0])
        except Exception, e:
            self.log.error("MilestoneTeams error in admin module: %s" % (e,))
            raise e
        
#        self.log.debug("MilestoneTeams: %s", (milestones,))
        
        db.close()
        return milestones

    def get_session_users(self):
        db      = self.env.get_db_cnx()
        cursor  = db.cursor()
        users   = [ ]
        
        try:
            cursor.execute("SELECT s.sid AS user FROM session AS s ORDER BY s.sid ASC")
            for row in cursor:
                users.append(row[0])
        except Exception, e:
            self.log.error("MilestoneTeams error in admin module: %s" % (e,))
            raise e
        
        db.close()
        return users

    def render_admin_panel(self, req, category, page, path_info):
        """Return the template and data used to render our administration page."""

        db      = self.env.get_db_cnx()
        cursor  = db.cursor()
 
        if req.method == 'POST':
            if req.args.get('action') == 'Modify':
                if not self.set_milestone_team(req.args.get('title'), req.args.get('manager'), req.args.get('members')):
                    self.log.error("MilestoneTeams Error: Failed to save state for milestone'%s'" % (req.args.get('title'), ))
        
        milestones  = self.get_milestone_team(path_info)
        users       = self.get_session_users()

        if path_info:
            for milestone in milestones:
                if milestone['title'] == path_info:
                    data = {
                        'view':         'detail',
                        'users':        users,
                        'milestone':    milestone,
                    }
        else:
            data = {
                'view':         'list',
                'users':        users,
                'milestones':   milestones,
                }

        db.close()
        return 'milestoneteams.html', data

    def get_templates_dirs(self):
        from pkg_resources import resource_filename
        return [resource_filename(__name__,'templates')]
        
    def get_htdocs_dirs(self):
        return []
