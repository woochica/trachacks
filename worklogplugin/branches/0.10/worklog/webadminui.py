import time

from trac import ticket
from trac import util
from trac.core import *
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.util import Markup
from webadmin.web_ui import IAdminPageProvider


class WorklogAdminPage(Component):

    implements(IAdminPageProvider)

    # IAdminPageProvider methods
    def get_admin_pages(self, req):
        if req.perm.has_permission('TICKET_ADMIN'):
            yield ('ticket', 'Ticket System', 'worklog', 'Work Log')

    def process_admin_request(self, req, cat, page, component):
        req.perm.assert_permission('TICKET_ADMIN')
        section = "worklog"

        bools = [ "timingandestimation", "comment",
                  "autostop", "autostopstart", "autoreassignaccept" ]
        
        if req.method == 'POST' and req.args.has_key('update'):
            for yesno in bools:
                if req.args.has_key(yesno):
                    self.config.set(section, yesno, True)
                else:
                    self.config.set(section, yesno, False)
                roundup = 1
                if req.args.has_key('roundup'):
                    try:
                        if int(req.args.get('roundup')) > 0:
                            roundup = int(req.args.get('roundup'))
                    except:
                        pass
                self.config.set(section, 'roundup', roundup)
                
            self.config.save()

        mytrue = Markup('checked="checked"')
        settings = {}
        for yesno in bools:
            if self.config.getbool(section, yesno):
                settings[yesno] = mytrue

        if self.config.getint(section, 'roundup'):
            settings['roundup'] = self.config.getint(section, 'roundup')

        req.hdf['settings'] = settings
        return 'worklog_webadminui.cs', None
