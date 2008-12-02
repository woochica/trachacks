from trac.core import *
from trac.web.chrome import ITemplateProvider
from pkg_resources import resource_filename

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

    def render_admin_panel(self, req, category, page, path_info):
        assert req.perm.has_permission('TICKET_ADMIN')

        action = req.args.get('action')
        
        caption = '';
        teams = []
        count = 0
                
        if action:
            # load data from post
            count = int(req.args.get('count'))
            for i in xrange(count):
                team = req.args.get("team_%i" % i )
                dispatcher = req.args.get("dispatcher_%i" % i )
                #TODO: Verify unique team-names and e-mail address struct
                if action != 'newLine' and ( team == '' or dispatcher == '' ):
                    continue
                teams.append({'id': i, 'name' : team , 'dispatcher' : dispatcher})
            caption = req.args.get("caption")
            
            if action == 'newLine': # add an additional empty line
                teams.append({'id': count, 'name' : '', 'dispatcher' : ''})
                count = count + 1
            elif action == 'save': # save the data
                names = []
                # write own data and prepare external names
                count = 0
                for team in teams:
                    self.config.set('ticket-team-dispatcher', '%i.team' % count, team['name'])
                    self.config.set('ticket-team-dispatcher', '%i.dispatcher' % count, team['dispatcher'])
                    names.append(team['name'])
                    count = count + 1
                self.config.set('ticket-team-dispatcher', 'caption', caption)
                self.config.set('ticket-team-dispatcher', 'count', count)
                
                #remove deleted items from trac.ini
                while self.config.has_option('ticket-team-dispatcher', '%i.team' % count):
                    self.config.remove('ticket-team-dispatcher', '%i.team' % count)
                    self.config.remove('ticket-team-dispatcher', '%i.dispatcher' % count)
                    count = count + 1
                
                # evil hack on ticket-custom ;) TODO: use api of http://trac-hacks.org/wiki/CustomFieldAdminPlugin
                if not self.config.has_option('ticket-custom', 'ttd'):
                    self.config.set('ticket-custom', 'ttd', 'select')
                self.config.set('ticket-custom', 'ttd.label',   caption)
                self.config.set('ticket-custom', 'ttd.options', "|".join(names))                
                
                self.config.save()
        else: 
            # load data from config
            count = self.env.config.getint('ticket-team-dispatcher', 'count', 0)
            for i in xrange(count): 
                teams.append({'id': i,
                              'name' : self.config.get('ticket-team-dispatcher', '%i.team' % i, None),
                              'dispatcher' : self.config.get('ticket-team-dispatcher', '%i.dispatcher' % i, None)})
            caption = self.env.config.get('ticket-team-dispatcher', 'caption', 'Team')        
                                
        return 'ttd_admin.html', {'teams' : teams, 'caption' : caption, 'count' : count}

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
