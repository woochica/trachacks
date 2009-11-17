from trac.core import *
from trac.web.chrome import ITemplateProvider
from pkg_resources import resource_filename

from tracusermanager.api import UserManager, User
from trac.admin import IAdminPanelProvider

class TicketTeamDispatcherAdmin(Component):
    """
        Provides functions related to registration
    """

    implements(ITemplateProvider, IAdminPanelProvider)

    # IAdminPageProvider methods
    def get_admin_panels(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'ttd', 'Ticket Team Dispatcher')
            
    def getCaption(self):
        return self.config.get('ticket-custom', 'ttd.label')
        
    def setCaption(self, caption):
        self.config.set('ticket-custom', 'ttd.label', caption)
        self.config.save()
                
    def getTeams(self):
        return self.config.get('ticket-custom', 'ttd.options').split('|')   
        
    def setTeams(self, teams):
        self.config.set('ticket-custom', 'ttd.options', '|'.join(teams))     
        self.config.save()
        
    def render_admin_panel(self, req, category, page, path_info):
        assert req.perm.has_permission('TICKET_ADMIN')

        action = req.args.get('action')
        
        users = UserManager(self.env).get_active_users()
        caption = self.getCaption()
        teams = self.getTeams()
                
        if action:
            # load data from post
            if action == 'rename':
                caption = req.args.get('caption')
                self.setCaption(caption)
            elif action == 'add':
                newTeam = req.args.get('newTeam')
                
                canAdd = True
                for team in teams:
                    if team == newTeam:
                        canAdd = False
                        break
                
                if canAdd:
                    teams.append(newTeam)
                    for user in users:
                        user[newTeam] = '0'
                        user.save()
                    self.setTeams(teams)                
            elif action == 'up':
                id = req.args.get('id')
                i = teams.index(id)
                if i > 0:
                    tmp = teams[i-1]
                    teams[i-1] = teams[i]
                    teams[i] = tmp
                    self.setTeams(teams)                
            elif action == 'down':
                id = req.args.get('id')
                i = teams.index(id)
                if i < len(teams)-1:
                    tmp = teams[i+1]
                    teams[i+1] = teams[i]
                    teams[i] = tmp
                    self.setTeams(teams)        
            elif action == 'delete':
                id = req.args.get('id')
                teams.remove(id)
                for user in users:
                    del user[id]
                    user.save()
                self.setTeams(teams)   
            elif action == 'updateUsers':
                for user in users:
                    for team in teams:
                        if req.args.get('%s_%s' % (user.username, team)):
                            user[team] = '1'
                        else:
                            user[team] = '0'
                        
                    user.save()
                                
        return 'ttd_admin.html', {'teams' : teams, 'users' : users, 'caption' : caption}

    # INavigationContributor
    def get_templates_dirs(self):
        """
            Return the absolute path of the directory containing the provided
            templates
        """
        return [resource_filename(__name__, 'tpl')]

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
        return [('ttd', resource_filename(__name__, 'htdocs'))]
